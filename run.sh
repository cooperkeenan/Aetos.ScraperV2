#!/bin/bash
set -e

REGISTRY="aetosregistry"
IMAGE="aetos-scraper:latest"

echo "🔨 Building in ACR..."
az acr build \
  --registry $REGISTRY \
  --image $IMAGE \
  --file Dockerfile \
  .

echo "🚀 Running with streaming logs..."
az acr run \
  --registry $REGISTRY \
  --cmd "$REGISTRY.azurecr.io/$IMAGE python test_navigation.py" \
  /dev/null