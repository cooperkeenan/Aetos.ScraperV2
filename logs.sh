#!/bin/bash

CONTAINER_NAME="aetos-api"
RESOURCE_GROUP="aetos-dev-rg"

echo "📋 Checking container status..."

STATE=$(az container show \
  --resource-group $RESOURCE_GROUP \
  --name $CONTAINER_NAME \
  --query "instanceView.state" -o tsv 2>/dev/null)

if [ -z "$STATE" ]; then
  echo "❌ Container not found"
  exit 1
fi

echo "Container State: $STATE"

if [ "$STATE" != "Running" ]; then
  echo "⏳ Waiting for container to start..."
  for i in {1..30}; do
    sleep 2
    STATE=$(az container show \
      --resource-group $RESOURCE_GROUP \
      --name $CONTAINER_NAME \
      --query "instanceView.state" -o tsv 2>/dev/null)
    
    if [ "$STATE" = "Running" ]; then
      echo "✅ Container is now running"
      break
    fi
    echo "   Still waiting... ($i/30) - State: $STATE"
  done
fi

echo ""
echo "📋 Fetching recent logs first..."
echo ""

# Get recent logs (non-streaming) to ensure there's content
az container logs \
  --resource-group $RESOURCE_GROUP \
  --name $CONTAINER_NAME \
  --container-name $CONTAINER_NAME \
  --output tsv | tail -n 20

echo ""
echo "📋 Now streaming new logs..."
echo "Press Ctrl+C to stop"
echo ""

# Wait a bit to ensure logs are available
sleep 3

# Try streaming - if it fails, fall back to polling
az container logs --follow \
  --resource-group $RESOURCE_GROUP \
  --name $CONTAINER_NAME \
  --container-name $CONTAINER_NAME \
  --output tsv || {
    echo ""
    echo "⚠️  Streaming failed, using polling mode instead..."
    echo ""
    
    # Poll every 3 seconds
    while true; do
      clear
      echo "📋 Container Logs (refreshing every 3s) - Press Ctrl+C to stop"
      echo ""
      az container logs \
        --resource-group $RESOURCE_GROUP \
        --name $CONTAINER_NAME \
        --container-name $CONTAINER_NAME \
        --output tsv | tail -n 50
      sleep 3
    done
  }
