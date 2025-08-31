# Use ARGs to define base image and versions for easy configuration.
ARG PYTHON_VERSION=3.11
ARG UV_VERSION=latest
ARG BASE_IMAGE=astral/uv:${UV_VERSION}-python${PYTHON_VERSION}

# --- Final Image ---
# This image creates a generic Dagster runtime environment.
# User code will be mounted into it by git-sync at runtime.
FROM ${BASE_IMAGE}

# Use ARGs to make framework versions easily configurable.
ARG DAGSTER_VERSION="1.5.0"
ARG DAGSTER_K8S_VERSION="1.5.0"
ARG DAGSTER_POSTGRES_VERSION="0.21.0"
ARG PSYCOPG2_VERSION="2.9.9"

# Set environment variables to compile bytecode for better performance.
ENV UV_COMPILE_BYTECODE=1

# Install Dagster framework dependencies.
# This creates the runtime environment for the code that git-sync will pull.
RUN uv pip install --no-cache \
    dagster==${DAGSTER_VERSION} \
    dagster-k8s==${DAGSTER_K8S_VERSION} \
    dagster-postgres==${DAGSTER_POSTGRES_VERSION} \
    psycopg2-binary==${PSYCOPG2_VERSION}

# Create the directory where git-sync will clone the user code.
# The WORKDIR will be set here, and this is the mount point for the volume.
WORKDIR /opt/dagster/app

# Expose the gRPC port that Dagster uses.
EXPOSE 8080