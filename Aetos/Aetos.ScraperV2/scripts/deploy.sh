#!/bin/bash
set -e

REGISTRY="aetosregistry"
IMAGE="aetos-scraper:latest"
CONTAINER_NAME="aetos-api"
RESOURCE_GROUP="aetos-dev-rg"
LOCATION="eastus"
STORAGE_ACCOUNT="aetoslogstorage"
FILE_SHARE="aetos-logs"

echo "🔨 Building in ACR..."
az acr build \
  --registry $REGISTRY \
  --image $IMAGE \
  --file Dockerfile \
  .

echo ""
echo "📦 Ensuring storage account and file share exist..."
az storage account create \
  --name $STORAGE_ACCOUNT \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --sku Standard_LRS \
  --output none 2>/dev/null || true

az storage share create \
  --name $FILE_SHARE \
  --account-name $STORAGE_ACCOUNT \
  --output none 2>/dev/null || true

STORAGE_KEY=$(az storage account keys list \
  --account-name $STORAGE_ACCOUNT \
  --resource-group $RESOURCE_GROUP \
  --query "[0].value" -o tsv)

echo ""
echo "🗑️  Checking for existing container..."
if az container show --resource-group $RESOURCE_GROUP --name $CONTAINER_NAME --output none 2>/dev/null; then
  echo "⚠️  Found existing container '$CONTAINER_NAME', deleting..."
  az container delete \
    --resource-group $RESOURCE_GROUP \
    --name $CONTAINER_NAME \
    --yes \
    --output none

  echo "⏳ Waiting for deletion to complete..."
  sleep 10

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
  --azure-file-volume-account-name $STORAGE_ACCOUNT \
  --azure-file-volume-account-key $STORAGE_KEY \
  --azure-file-volume-share-name $FILE_SHARE \
  --azure-file-volume-mount-path /app/logs \
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
    ORCHESTRATOR_WEBHOOK_URL=https://aetos-orchestrator-func-gycubdb8cxd0fsgs.uksouth-01.azurewebsites.net/api/webhooks/scraper/job-complete \
    ORCHESTRATOR_API_KEY=${ORCHESTRATOR_API_KEY:-aetos-production-key-2024} \
  --restart-policy Always

echo ""
echo "🔑 Assigning ACI permissions to orchestrator managed identity..."
az role assignment create \
  --assignee "e1b435be-446f-4e6c-9993-6f9f03a63e5b" \
  --role "Contributor" \
  --scope "/subscriptions/37035190-2489-46aa-bc55-ccc9fc751ead/resourceGroups/aetos-dev-rg/providers/Microsoft.ContainerInstance/containerGroups/aetos-api" \
  --output none 2>/dev/null || echo "⚠️  Role assignment already exists"

echo ""
echo "✅ API deployed and running!"
echo ""
echo "API URL: http://aetos-scraper.$LOCATION.azurecontainer.io:8000"
echo "API Docs: http://aetos-scraper.$LOCATION.azurecontainer.io:8000/docs"
echo "📁 Logs: Azure Storage Explorer → $STORAGE_ACCOUNT → $FILE_SHARE"
echo ""
echo "🔑 API Key: ${API_KEY:-aetos-production-key-2024}"