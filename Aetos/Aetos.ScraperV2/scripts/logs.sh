#!/bin/bash

CONTAINER_NAME="aetos-api"
RESOURCE_GROUP="aetos-dev-rg"

# Try streaming - if it fails, fall back to polling
az container logs --follow \
  --resource-group $RESOURCE_GROUP \
  --name $CONTAINER_NAME \
  --container-name $CONTAINER_NAME \
  --output tsv 
    
