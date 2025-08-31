#!/bin/bash

# Exit on error
set -e

echo "Deploying Dagster stack..."

# Deploy namespace
echo "Deploying namespace..."
kubectl apply -f postgres/03_namespace-dagster.yaml

# Deploy postgres resources
echo "Deploying PostgreSQL..."
kubectl apply -f postgres/

# Deploy instance resources
echo "Deploying Dagster instance..."
kubectl apply -f instance/

# Deploy A and B environments
echo "Deploying A and B environments..."
kubectl apply -f A/
kubectl apply -f B/

echo "Dagster stack deployment complete."
