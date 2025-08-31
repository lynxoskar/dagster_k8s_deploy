#!/bin/bash
set -euo pipefail

# ==============================================================================
# Build and Publish Script for Dagster Harness Image
# ==============================================================================

# --- Configuration ---
: "${DOCKER_REPO:?ERROR: Please set the DOCKER_REPO environment variable (e.g., 'docker.io/myusername')}"
: "${IMAGE_NAME:=dagster-harness}"
: "${IMAGE_TAG:=latest}"

# --- Script Setup ---
SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)
FULL_IMAGE_NAME="${DOCKER_REPO}/${IMAGE_NAME}:${IMAGE_TAG}"

# --- Helper Functions ---
function print_usage() {
  echo "Usage: $0 [COMMAND]"
  echo "Commands:"
  echo "  build    Build the Docker image."
  echo "  publish  Build and push the Docker image to the configured repository."
}

function build_image() {
  echo "--- Building Docker Image ---"
  echo "Image:         ${FULL_IMAGE_NAME}"
  echo "Build Context: ${SCRIPT_DIR}"
  echo "-----------------------------"

  # The build context is the directory containing this script and the Dockerfile.
  docker build -t "${FULL_IMAGE_NAME}" "${SCRIPT_DIR}"

  echo "--- Build Complete ---"
}

function publish_image() {
  echo "--- Publishing Docker Image ---"
  build_image
  echo "Attempting to push to ${DOCKER_REPO}. You may be prompted to log in."
  docker push "${FULL_IMAGE_NAME}"
  echo "--- Publish Complete ---"
}

# --- Main Execution ---
main() {
  local command="${1:-}"

  if [[ -z "${command}" ]]; then
    print_usage
    exit 1
  fi

  case ${command} in
  build)
    build_image
    ;;
  publish)
    publish_image
    ;;
  *)
    echo "ERROR: Invalid command '${command}'."
    echo ""
    print_usage
    exit 1
    ;;
  esac
}

main "$@"