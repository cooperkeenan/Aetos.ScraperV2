#!/bin/bash

CONTAINER_NAME="aetos-api"
RESOURCE_GROUP="aetos-dev-rg"

echo "⏸️  Stopping API container..."
az container stop --name $CONTAINER_NAME --resource-group $RESOURCE_GROUP

echo "✅ Container stopped (no charges while stopped)"
echo ""
echo "To start again: ./start_api.sh"