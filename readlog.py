#!/usr/bin/env -S uv run
"""
# /// script
# requires-python = ">=3.9"
# dependencies = [
#     "typer>=0.12.0",
# ]
# ///

from __future__ import annotations

import subprocess
from typing import Optional

import typer

app = typer.Typer(help="Tail pod logs via kubectl")


def _kubectl(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(["kubectl", *args], check=False)


@app.command()
def follow(
    ns: str = typer.Option("dagster", help="Kubernetes namespace"),
    label: str = typer.Option(..., "--selector", "-l", help="Label selector, e.g. app=dagster-webserver"),
    container: Optional[str] = typer.Option(None, "--container", "-c", help="Container name in the pod"),
    tail: int = typer.Option(100, help="Number of lines to show initially"),
):
    """Follow logs for the first pod matching the selector."""
    # Get pod name
    get_cmd = ["get", "pods", "-n", ns, "-l", label, "-o", "jsonpath={.items[0].metadata.name}"]
    res = subprocess.run(["kubectl", *get_cmd], capture_output=True, text=True)
    pod = res.stdout.strip()
    if res.returncode != 0 or not pod:
        typer.secho("No matching pod found", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    typer.secho(f"Tailing logs for pod: {pod}", fg=typer.colors.GREEN)
    args = ["logs", pod, "-n", ns, "-f", "--tail", str(tail)]
    if container:
        args.extend(["-c", container])
    _kubectl(args)


if __name__ == "__main__":
    app()

