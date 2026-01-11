#!/bin/bash
# manager.sh - Aetos Scraper Manager

set -e

# Configuration
RESOURCE_GROUP="aetos-dev-rg"
REGISTRY="aetosregistry"
IMAGE="${REGISTRY}.azurecr.io/aetos-scraper:latest"
CONTAINER_NAME="aetos-scraper-test"
LOCATION="uksouth"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Get registry password
get_registry_password() {
    az acr credential show --name $REGISTRY --query "passwords[0].value" -o tsv
}

# Delete existing container
delete_container() {
    echo -e "${BLUE}🗑️  Deleting existing container...${NC}"
    az container delete \
        --resource-group $RESOURCE_GROUP \
        --name $CONTAINER_NAME \
        --yes 2>/dev/null || echo "No existing container to delete"
}

# Create and run container
run_container() {
    local registry_password=$(get_registry_password)
    
    # Get storage key
    local storage_key=$(az storage account keys list \
        --resource-group $RESOURCE_GROUP \
        --account-name aetosscraperstorage \
        --query "[0].value" -o tsv)
    
    echo -e "${BLUE}🚀 Creating container instance with Azure File Share...${NC}"
    az container create \
        --resource-group $RESOURCE_GROUP \
        --name $CONTAINER_NAME \
        --image $IMAGE \
        --registry-login-server ${REGISTRY}.azurecr.io \
        --registry-username $REGISTRY \
        --registry-password $registry_password \
        --os-type Linux \
        --azure-file-volume-account-name aetosscraperstorage \
        --azure-file-volume-account-key $storage_key \
        --azure-file-volume-share-name scraper-logs \
        --azure-file-volume-mount-path /app/logs \
        --environment-variables USE_PROXY=false PYTHONUNBUFFERED=1 \
        --cpu 1 \
        --memory 2 \
        --restart-policy Never \
        --location $LOCATION
    
    echo -e "${GREEN}✅ Container created with logs mounted to Azure File Share${NC}"
}

# Stream logs
stream_logs() {
    echo -e "${BLUE}📋 Container starting...${NC}"
    echo -e "${BLUE}Waiting 60 seconds for script to complete...${NC}\n"
    
    # Wait for container to finish (takes ~30-60s)
    sleep 60
    
    # Now show the logs from file share
    view_file_share_logs
}

# Build and push
build_and_push() {
    echo -e "${BLUE}🔨 Building Docker image...${NC}"
    docker build -t $IMAGE .
    
    echo -e "${BLUE}📤 Pushing to registry...${NC}"
    docker push $IMAGE
    
    echo -e "${GREEN}✅ Build and push complete${NC}"
}

# View logs from Azure File Share
view_file_share_logs() {
    echo -e "\n${GREEN}=== View File Share Logs ===${NC}\n"
    echo -e "${BLUE}📋 Downloading logs from Azure File Share...${NC}\n"
    
    local storage_key=$(az storage account keys list \
        --resource-group $RESOURCE_GROUP \
        --account-name aetosscraperstorage \
        --query "[0].value" -o tsv)
    
    echo -e "${BLUE}====================================================================${NC}\n"
    
    # Try to download and display the log
    if az storage file download \
        --account-name aetosscraperstorage \
        --account-key $storage_key \
        --share-name scraper-logs \
        --path output.log \
        --dest /dev/stdout 2>/dev/null; then
        echo ""
    else
        echo -e "${RED}No logs found yet. Container may still be running or hasn't started.${NC}"
    fi
    
    echo -e "\n${BLUE}====================================================================${NC}"
}

# List all log files in file share
list_log_files() {
    echo -e "\n${GREEN}=== Log Files in Azure File Share ===${NC}\n"
    
    local storage_key=$(az storage account keys list \
        --resource-group $RESOURCE_GROUP \
        --account-name aetosscraperstorage \
        --query "[0].value" -o tsv)
    
    az storage file list \
        --account-name aetosscraperstorage \
        --account-key $storage_key \
        --share-name scraper-logs \
        --output table
}

# Main menu
show_menu() {
    clear
    echo -e "${GREEN}╔════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║   Aetos Scraper Manager                ║${NC}"
    echo -e "${GREEN}╔════════════════════════════════════════╗${NC}"
    echo ""
    echo "1. 🔨 Build, Push & Run"
    echo "   (Rebuild image, push to ACR, run, view logs)"
    echo ""
    echo "2. 🚀 Run & View Logs"
    echo "   (Use existing image, run, view logs)"
    echo ""
    echo "3. 📋 View Logs from File Share"
    echo "   (Download and display output.log)"
    echo ""
    echo "4. 📁 List All Log Files"
    echo "   (Show all files in Azure File Share)"
    echo ""
    echo "5. 🗑️  Delete Container"
    echo "   (Stop and remove container)"
    echo ""
    echo "6. ❌ Exit"
    echo ""
    echo -n "Choose option [1-6]: "
}


# Option 1: Build, Push & Stream
option_build_push_stream() {
    echo -e "\n${GREEN}=== Build, Push & Stream ===${NC}\n"
    build_and_push
    delete_container
    run_container
    stream_logs
}

# Option 2: Run & Stream
option_run_stream() {
    echo -e "\n${GREEN}=== Run & Stream ===${NC}\n"
    delete_container
    run_container
    stream_logs
}

# Option 3: View Logs
option_view_logs() {
    echo -e "\n${GREEN}=== View Logs ===${NC}\n"
    stream_logs
}

# Option 4: Delete Container
option_delete() {
    echo -e "\n${GREEN}=== Delete Container ===${NC}\n"
    delete_container
    echo -e "${GREEN}✅ Container deleted${NC}"
}

# Main loop
main() {
    while true; do
        show_menu
        read -r choice
        
        case $choice in
            1)
                option_build_push_stream
                ;;
            2)
                option_run_stream
                ;;
            3)
                view_file_share_logs
                ;;
            4)
                list_log_files
                ;;
            5)
                option_delete
                ;;
            6)
                echo -e "\n${GREEN}👋 Goodbye!${NC}\n"
                exit 0
                ;;
            *)
                echo -e "\n${RED}Invalid option. Please choose 1-6.${NC}\n"
                sleep 2
                ;;
        esac
        
        echo -e "\n${BLUE}Press Enter to continue...${NC}"
        read -r
    done
}

# Run main
main