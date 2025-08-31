#!/usr/bin/env python3
"""
# /// script
# requires-python = ">=3.8"
# dependencies = [
#     "pyyaml",
# ]
# ///

Script to generate Kubernetes deployment files from templates using configvalues.yaml.

Usage:
    uv run create_deploy.py

This will:
1. Read configvalues.yaml for image and environment settings
2. Process all YAML template files in the current directory
3. Generate deployment-ready files in the deploy/ directory
"""

import os
import shutil
import yaml
from pathlib import Path


def load_config(config_file: str = "configvalues.yaml") -> dict:
    """Load configuration values from YAML file."""
    with open(config_file, 'r') as f:
        return yaml.safe_load(f)


def process_yaml_template(template_path: Path, config: dict) -> str:
    """Process a YAML template file and replace placeholders with config values."""
    with open(template_path, 'r') as f:
        content = f.read()
    
    # Replace image placeholders
    for image_key, image_value in config.get('images', {}).items():
        placeholder = f"{{{{ images.{image_key} }}}}"
        content = content.replace(placeholder, image_value)
    
    # Replace environment placeholders
    for env_key, env_value in config.get('environment', {}).items():
        placeholder = f"{{{{ environment.{env_key} }}}}"
        content = content.replace(placeholder, str(env_value))
    
    return content


def create_deploy_directory(source_dirs: list, config: dict):
    """Create deploy directory with processed YAML files."""
    deploy_dir = Path("deploy")
    
    # Clean and create deploy directory
    if deploy_dir.exists():
        shutil.rmtree(deploy_dir)
    deploy_dir.mkdir()
    
    print(f"Created deploy directory: {deploy_dir.absolute()}")
    
    # Process each source directory
    for source_dir in source_dirs:
        source_path = Path(source_dir)
        if not source_path.exists():
            print(f"Warning: Source directory {source_dir} does not exist, skipping...")
            continue
            
        # Create corresponding directory in deploy/
        target_dir = deploy_dir / source_dir
        target_dir.mkdir(parents=True, exist_ok=True)
        
        # Process all YAML files in the source directory
        yaml_files = list(source_path.glob("*.yaml")) + list(source_path.glob("*.yml"))
        
        for yaml_file in yaml_files:
            print(f"Processing {yaml_file}...")
            
            # Process template
            processed_content = process_yaml_template(yaml_file, config)
            
            # Write to deploy directory
            target_file = target_dir / yaml_file.name
            with open(target_file, 'w') as f:
                f.write(processed_content)
            
            print(f"  -> {target_file}")


def main():
    """Main execution function."""
    print("🚀 Creating Kubernetes deployment files...")
    
    # Load configuration
    try:
        config = load_config()
        print(f"✅ Loaded configuration from configvalues.yaml")
    except FileNotFoundError:
        print("❌ Error: configvalues.yaml not found!")
        return 1
    except yaml.YAMLError as e:
        print(f"❌ Error parsing configvalues.yaml: {e}")
        return 1
    
    # Define source directories to process
    source_directories = ["postgres", "instance", "A", "B"]
    
    # Create deployment files
    try:
        create_deploy_directory(source_directories, config)
        print("✅ Deployment files created successfully!")
        print("\nTo deploy:")
        print("  kubectl apply -f deploy/postgres/")
        print("  kubectl apply -f deploy/instance/")
        print("  kubectl apply -f deploy/A/")
        print("  kubectl apply -f deploy/B/")
    except Exception as e:
        print(f"❌ Error creating deployment files: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())

