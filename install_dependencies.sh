#!/bin/bash

# Exit on error
set -e

# Check for uv
if ! command -v uv &> /dev/null
then
    echo "uv could not be found, installing..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
else
    echo "uv is already installed."
fi

# Check for kubectl
if ! command -v kubectl &> /dev/null
then
    echo "kubectl could not be found, installing..."
    if [[ "$(uname)" == "Linux" ]]; then
        curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
        chmod +x kubectl
        echo "kubectl has been downloaded to the current directory."
        echo "Please move it to a directory in your PATH, for example:"
        echo "  sudo mv kubectl /usr/local/bin/"
    else
        echo "This script only supports kubectl installation on Linux. Please install kubectl manually."
        exit 1
    fi
else
    echo "kubectl is already installed."
fi

echo "Dependency check complete."
