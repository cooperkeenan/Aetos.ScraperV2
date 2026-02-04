#!/bin/bash

CONTAINER_NAME="aetos-api"
RESOURCE_GROUP="aetos-dev-rg"
LOCATION="eastus"

echo "▶️  Starting API container..."
az container start --name $CONTAINER_NAME --resource-group $RESOURCE_GROUP

echo "✅ API is running!"
echo ""
echo "API URL: http://aetos-scraper.$LOCATION.azurecontainer.io:8000"