#!/bin/bash
set -e

REGISTRY="aetosregistry"
IMAGE="aetos-scraper:latest"
CONTAINER_NAME="aetos-api"
RESOURCE_GROUP="aetos-dev-rg"
LOCATION="eastus"

echo "🔨 Building in ACR..."
az acr build \
  --registry $REGISTRY \
  --image $IMAGE \
  --file Dockerfile \
  .

echo ""
echo "🗑️  Checking for existing container..."
if az container show --resource-group $RESOURCE_GROUP --name $CONTAINER_NAME --output none 2>/dev/null; then
  echo "⚠️  Found existing container '$CONTAINER_NAME', deleting..."
  az container delete \
    --resource-group $RESOURCE_GROUP \
    --name $CONTAINER_NAME \
    --yes \
    --output none
  
  # Wait for deletion to complete
  echo "⏳ Waiting for deletion to complete..."
  sleep 10
  
  # Verify it's gone
  MAX_WAIT=30
  WAITED=0
  while az container show --resource-group $RESOURCE_GROUP --name $CONTAINER_NAME --output none 2>/dev/null; do
    if [ $WAITED -ge $MAX_WAIT ]; then
      echo "❌ Deletion timeout - container still exists after ${MAX_WAIT}s"
      exit 1
    fi
    echo "   Still deleting... (${WAITED}s)"
    sleep 5
    WAITED=$((WAITED + 5))
  done
  
  echo "✅ Old container deleted successfully"
else
  echo "✅ No existing container found"
fi

echo ""
echo "🚀 Deploying API to Azure Container Instances..."
az container create \
  --resource-group $RESOURCE_GROUP \
  --name $CONTAINER_NAME \
  --image $REGISTRY.azurecr.io/$IMAGE \
  --os-type Linux \
  --registry-login-server $REGISTRY.azurecr.io \
  --registry-username $(az acr credential show --name $REGISTRY --query username -o tsv) \
  --registry-password $(az acr credential show --name $REGISTRY --query passwords[0].value -o tsv) \
  --dns-name-label aetos-scraper \
  --ports 8000 \
  --cpu 2 \
  --memory 4 \
  --environment-variables \
    API_KEY=${API_KEY:-aetos-production-key-2024} \
    DB_HOST=ep-broad-fire-a8ngftkc-pooler.eastus2.azure.neon.tech \
    DB_PORT=5432 \
    DB_NAME=neondb \
    DB_USER=neondb_owner \
    DB_PASSWORD=npg_MXEm6PaRCbu7 \
    IPROYAL_USER=fSlhwsc42Ar5tRdI \
    IPROYAL_PASS=0CAUxP7NxySHwelp \
    PROXY_COUNTRY=gb \
    PROXY_CITIES=edinburgh \
    GOOGLE_USER=mike.steel505@gmail.com \
    GOOGLE_PASS=SuperSteelMike!0 \
  --restart-policy Always

echo ""
echo "✅ API deployed and running!"
echo ""
echo "API URL: http://aetos-scraper.$LOCATION.azurecontainer.io:8000"
echo "API Docs: http://aetos-scraper.$LOCATION.azurecontainer.io:8000/docs"
echo ""
echo "🔑 API Key: ${API_KEY:-aetos-production-key-2024}"
echo ""
echo "Test scrape:"
echo "curl -X POST http://aetos-scraper.$LOCATION.azurecontainer.io:8000/scrape \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -H 'X-API-Key: ${API_KEY:-aetos-production-key-2024}' \\"
echo "  -d '{\"brand\":\"Canon\"}'"