#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo ""
echo -e "${BLUE}╔════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     Aetos Scraper - Menu           ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════╝${NC}"
echo ""
echo "1) Deploy and stream logs"
echo "2) Start API"
echo "3) Stop API"
echo "4) Deploy only"
echo ""
read -p "Select option (1-4): " choice

case $choice in
    1)
        echo -e "${GREEN}Deploying and streaming logs...${NC}"
        ./scripts/deploy.sh && ./scripts/logs.sh
        ;;
    2)
        echo -e "${GREEN}Starting API...${NC}"
        ./scripts/start_api.sh
        ;;
    3)
        echo -e "${YELLOW}Stopping API...${NC}"
        ./scripts/stop_api.sh
        ;;
    4)
        echo -e "${GREEN}Deploying...${NC}"
        ./scripts/deploy.sh
        ;;
    *)
        echo -e "${RED}Invalid option${NC}"
        exit 1
        ;;
esac