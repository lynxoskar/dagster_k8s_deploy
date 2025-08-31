#!/usr/bin/env -S uv run
"""
# /// script
# requires-python = ">=3.9"
# dependencies = [
#     "typer[all]>=0.12.0",
#     "loguru>=0.7.2",
#     "pyyaml>=6.0",
# ]
# ///
"""
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import List, Optional

import typer
from loguru import logger
import yaml

app = typer.Typer(help="Dagster k8s GitOps helper CLI")


# ----- Logging setup -----
def _configure_logging(verbose: bool) -> None:
    logger.remove()
    level = "DEBUG" if verbose else "INFO"
    logger.add(
        sink=lambda msg: typer.echo(str(msg), nl=False),
        level=level,
        colorize=True,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{message}</cyan>",
    )


# ----- Core functions -----
def _load_config(config_file: Path) -> dict:
    with config_file.open("r") as f:
        return yaml.safe_load(f) or {}


def _process_yaml_template(template_path: Path, config: dict) -> str:
    content = template_path.read_text()

    # Replace image placeholders
    for image_key, image_value in (config.get("images") or {}).items():
        placeholder = f"{{{{ images.{image_key} }}}}"
        content = content.replace(placeholder, str(image_value))

    # Replace environment placeholders
    for env_key, env_value in (config.get("environment") or {}).items():
        placeholder = f"{{{{ environment.{env_key} }}}}"
        content = content.replace(placeholder, str(env_value))

    return content


def _generate_deploy(
    sources: List[Path],
    out_dir: Path,
    config: dict,
    force: bool,
) -> None:
    if out_dir.exists() and not force:
        raise FileExistsError(
            f"Output directory '{out_dir}' exists. Use --force to overwrite."
        )
    if out_dir.exists() and force:
        for p in out_dir.glob("**/*"):
            # Simple clean: remove files only
            if p.is_file():
                p.unlink()
    out_dir.mkdir(parents=True, exist_ok=True)
    logger.success(f"Created/cleaned output: {out_dir}")

    for src in sources:
        if not src.exists():
            logger.warning(f"Skipping missing source dir: {src}")
            continue
        target = out_dir / src
        target.mkdir(parents=True, exist_ok=True)

        for yaml_file in list(src.glob("*.yml")) + list(src.glob("*.yaml")):
            logger.info(f"Processing {yaml_file}")
            processed = _process_yaml_template(yaml_file, config)
            out_file = target / yaml_file.name
            out_file.write_text(processed)
            logger.debug(f"Wrote {out_file}")

    logger.success("Deployment files generated")


def _kubectl_apply(directory: Path) -> None:
    if not directory.exists():
        logger.warning(f"Skip apply (not found): {directory}")
        return
    logger.info(f"kubectl apply -f {directory}")
    subprocess.run(["kubectl", "apply", "-f", str(directory)], check=True)


# ----- CLI commands -----
@app.command()
def generate(
    config: Path = typer.Option(Path("configvalues.yaml"), help="Config values file"),
    out_dir: Path = typer.Option(Path("deploy"), help="Output directory for generated manifests"),
    sources: List[Path] = typer.Option(
        [Path("postgres"), Path("instance"), Path("A"), Path("B")],
        help="Source manifest directories to process",
    ),
    force: bool = typer.Option(False, help="Overwrite existing output directory"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose logging"),
):
    """Generate Kubernetes manifests from templates and config values."""
    _configure_logging(verbose)
    try:
        cfg = _load_config(config)
        logger.success(f"Loaded config: {config}")
    except FileNotFoundError:
        logger.error(f"Config file not found: {config}")
        raise typer.Exit(code=1)
    except yaml.YAMLError as e:
        logger.error(f"Failed to parse config: {e}")
        raise typer.Exit(code=1)

    try:
        _generate_deploy(sources=sources, out_dir=out_dir, config=cfg, force=force)
    except Exception as e:
        logger.error(f"Generation failed: {e}")
        raise typer.Exit(code=1)


@app.command()
def deploy(
    out_dir: Path = typer.Option(Path("deploy"), help="Directory with generated manifests"),
    components: List[str] = typer.Option(
        ["postgres", "instance", "A", "B"],
        help="Which components to apply",
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose logging"),
):
    """Apply generated manifests with kubectl (per component)."""
    _configure_logging(verbose)
    order = ["postgres", "instance", "A", "B"]
    # Apply in stable order, but only selected components
    for comp in order:
        if comp in components:
            _kubectl_apply(out_dir / comp)
    logger.success("kubectl apply completed")


@app.command()
def validate(
    config: Path = typer.Option(Path("configvalues.yaml"), help="Config values file"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose logging"),
):
    """Validate config and presence of source directories."""
    _configure_logging(verbose)
    problems = 0
    try:
        cfg = _load_config(config)
        logger.success(f"Config OK: {config}")
    except Exception as e:
        logger.error(f"Config invalid: {e}")
        problems += 1
        cfg = {}

    for d in [Path("postgres"), Path("instance"), Path("A"), Path("B")]:
        if not d.exists():
            logger.error(f"Missing directory: {d}")
            problems += 1
        else:
            logger.info(f"Found: {d}")

    images = (cfg.get("images") or {})
    if not images:
        logger.warning("No images configured under 'images' in configvalues.yaml")

    if problems:
        logger.error(f"Validation failed with {problems} problem(s)")
        raise typer.Exit(code=1)
    logger.success("Validation passed")


if __name__ == "__main__":
    app()
