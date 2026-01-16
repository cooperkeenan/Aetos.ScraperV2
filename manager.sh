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
    echo -e "\n${GREEN}=== Downloading Logs ===${NC}\n"
    
    # Create local logs directory
    mkdir -p ./logs
    
    local storage_key=$(az storage account keys list \
        --resource-group $RESOURCE_GROUP \
        --account-name aetosscraperstorage \
        --query "[0].value" -o tsv)
    
    echo -e "${BLUE}Downloading output.log...${NC}"
    
    if az storage file download \
        --account-name aetosscraperstorage \
        --account-key $storage_key \
        --share-name scraper-logs \
        --path output.log \
        --dest ./logs/output.log \
        --output none 2>/dev/null; then
        
        echo -e "${GREEN}✅ Downloaded to ./logs/output.log${NC}\n"
        echo -e "${BLUE}====================================================================${NC}"
        cat ./logs/output.log
        echo -e "${BLUE}====================================================================${NC}"
    else
        echo -e "${RED}❌ Failed to download logs${NC}"
    fi
}

# Download latest screenshot
download_screenshot() {
    echo -e "\n${GREEN}=== Downloading Screenshot ===${NC}\n"
    
    # Create local logs directory
    mkdir -p ./logs
    
    local storage_key=$(az storage account keys list \
        --resource-group $RESOURCE_GROUP \
        --account-name aetosscraperstorage \
        --query "[0].value" -o tsv)
    
    echo -e "${BLUE}Finding latest screenshot...${NC}"
    
    # Get list of PNG files
    local latest_screenshot=$(az storage file list \
        --account-name aetosscraperstorage \
        --account-key $storage_key \
        --share-name scraper-logs \
        --query "[?ends_with(name, '.png')] | sort_by(@, &properties.lastModified) | [-1].name" \
        --output tsv 2>/dev/null)
    
    if [ -z "$latest_screenshot" ]; then
        echo -e "${RED}❌ No screenshots found${NC}"
        return
    fi
    
    echo -e "${BLUE}Downloading: $latest_screenshot${NC}"
    
    if az storage file download \
        --account-name aetosscraperstorage \
        --account-key $storage_key \
        --share-name scraper-logs \
        --path "$latest_screenshot" \
        --dest ./logs/screenshot.png \
        --output none 2>/dev/null; then
        
        echo -e "${GREEN}✅ Downloaded to ./logs/screenshot.png${NC}"
        echo -e "${BLUE}Original name: $latest_screenshot${NC}"
    else
        echo -e "${RED}❌ Failed to download screenshot${NC}"
    fi
}

# Download HTML files for debugging
download_html_files() {
    echo -e "\n${GREEN}=== Downloading HTML Files ===${NC}\n"
    
    # Create local logs directory
    mkdir -p ./logs
    
    local storage_key=$(az storage account keys list \
        --resource-group $RESOURCE_GROUP \
        --account-name aetosscraperstorage \
        --query "[0].value" -o tsv)
    
    echo -e "${BLUE}Finding HTML files...${NC}"
    
    # Get list of HTML files
    local html_files=$(az storage file list \
        --account-name aetosscraperstorage \
        --account-key $storage_key \
        --share-name scraper-logs \
        --query "[?ends_with(name, '.html')].name" \
        --output tsv 2>/dev/null)
    
    if [ -z "$html_files" ]; then
        echo -e "${RED}❌ No HTML files found${NC}"
        return
    fi
    
    # Download each HTML file
    while IFS= read -r filename; do
        echo -e "${BLUE}Downloading: $filename${NC}"
        
        az storage file download \
            --account-name aetosscraperstorage \
            --account-key $storage_key \
            --share-name scraper-logs \
            --path "$filename" \
            --dest "./logs/$filename" \
            --output none 2>/dev/null
        
        if [ -f "./logs/$filename" ]; then
            local size=$(wc -c < "./logs/$filename")
            echo -e "${GREEN}✅ Downloaded ./logs/$filename (${size} bytes)${NC}"
        fi
    done <<< "$html_files"
    
    echo -e "\n${GREEN}All HTML files downloaded to ./logs/${NC}"
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

# Check container status
check_status() {
    echo -e "\n${GREEN}=== Container Status ===${NC}\n"
    
    if az container show \
        --resource-group $RESOURCE_GROUP \
        --name $CONTAINER_NAME \
        --output table 2>/dev/null; then
        
        echo -e "\n${BLUE}=== Instance View ===${NC}"
        az container show \
            --resource-group $RESOURCE_GROUP \
            --name $CONTAINER_NAME \
            --query "instanceView" \
            --output table
    else
        echo -e "${RED}❌ Container not found${NC}"
    fi
}

# Main menu
show_menu() {
    clear
    echo -e "${GREEN}╔════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║   Aetos Scraper Manager                ║${NC}"
    echo -e "${GREEN}╔════════════════════════════════════════╗${NC}"
    echo ""
    echo "1. 🔨 Build, Push & Run"
    echo "   (Rebuild image, push to ACR, run container)"
    echo ""
    echo "2. 🚀 Run Container"
    echo "   (Use existing image, run container)"
    echo ""
    echo "3. 📊 Check Container Status"
    echo "   (View current container state and details)"
    echo ""
    echo "4. 📋 Download & View Logs"
    echo "   (Download output.log to ./logs/ and display)"
    echo ""
    echo "5. 📸 Download Latest Screenshot"
    echo "   (Download newest screenshot to ./logs/)"
    echo ""
    echo "6. 🌐 Download HTML Files"
    echo "   (Download all .html files for debugging)"
    echo ""
    echo "7. 📁 List All Files in File Share"
    echo "   (Show all files in Azure File Share)"
    echo ""
    echo "8. 🗑️  Delete Container"
    echo "   (Stop and remove container)"
    echo ""
    echo "9. ❌ Exit"
    echo ""
    echo -n "Choose option [1-9]: "
}


# Option 1: Build, Push & Run
option_build_push_stream() {
    echo -e "\n${GREEN}=== Build, Push & Run ===${NC}\n"
    build_and_push
    delete_container
    run_container
    
    echo -e "\n${BLUE}Container is running. Use Option 4 to view logs when complete.${NC}"
}

# Option 2: Run
option_run_stream() {
    echo -e "\n${GREEN}=== Run Container ===${NC}\n"
    delete_container
    run_container
    
    echo -e "\n${BLUE}Container is running. Use Option 4 to view logs when complete.${NC}"
}

# Option 3: View Logs
option_view_logs() {
    echo -e "\n${GREEN}=== View Logs ===${NC}\n"
    view_file_share_logs
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
                check_status
                ;;
            4)
                view_file_share_logs
                ;;
            5)
                download_screenshot
                ;;
            6)
                download_html_files
                ;;
            7)
                list_log_files
                ;;
            8)
                option_delete
                ;;
            9)
                echo -e "\n${GREEN}👋 Goodbye!${NC}\n"
                exit 0
                ;;
            *)
                echo -e "\n${RED}Invalid option. Please choose 1-9.${NC}\n"
                sleep 2
                ;;
        esac
        
        echo -e "\n${BLUE}Press Enter to continue...${NC}"
        read -r
    done
}

# Run main
main