# Code Location Image Builder

This directory contains the resources to build the Docker image for your Dagster user code.

The `Dockerfile` is optimized using a multi-stage build process as recommended by Astral (the creators of `uv`) to create a lean, production-ready image.

## How to Build

The `build_run.sh` script is provided to simplify the build and publish process.

### 1. Configuration

Before running the script, you **must** export the following environment variable:

```sh
export DOCKER_REPO="your-docker-hub-username-or-registry-url"
```

For example:
```sh
export DOCKER_REPO="docker.io/myusername"
```

You can also optionally override the default image name and tag:

```sh
export IMAGE_NAME="my-dagster-code"
export IMAGE_TAG="1.0.0"
```

### 2. Run the Script

Navigate to this directory (`k8s_deploy/codelocation`) to run the script.

**To build the image locally:**

```sh
./build_run.sh build
```

**To build and publish the image to your repository:**

```sh
./build_run.sh publish
```

---

## Dockerfile Details

- **Base Image**: Uses `astral/uv` for an optimized `uv` environment.
- **Framework Versioning**: The Dockerfile installs a specific version of `dagster`, `dagster-k8s`, and `dagster-postgres` into the image. This ensures that your code locations run in a stable, consistent environment. You can change these versions by modifying the `ARG` values at the top of the `Dockerfile`.
- **Dependency Caching**: The build process is structured to maximize Docker layer caching. The framework dependencies are installed first, and your project-specific dependencies are installed second. Changes to your source code will not trigger a re-install of the framework, leading to faster build times.
