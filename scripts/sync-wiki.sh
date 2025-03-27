#!/bin/bash

# Configuration
WIKI_REPO="https://github.com/FairGigAI/PEPPER.wiki.git"
WIKI_DIR="wiki-content"
TEMP_DIR=".wiki-temp"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}Starting wiki sync...${NC}"

# Create temporary directory
rm -rf $TEMP_DIR
mkdir $TEMP_DIR
cd $TEMP_DIR

# Clone wiki repository
echo "Cloning wiki repository..."
if git clone $WIKI_REPO . 2>/dev/null; then
    echo -e "${GREEN}Successfully cloned wiki repository${NC}"
else
    echo -e "${YELLOW}Wiki repository not found. Please follow these steps:${NC}"
    echo "1. Go to https://github.com/FairGigAI/PEPPER/wiki"
    echo "2. Click 'Create the first page'"
    echo "3. Add any content and save"
    echo "4. Run this script again"
    cd ..
    rm -rf $TEMP_DIR
    exit 1
fi

# Copy content from wiki-content to wiki repository
echo "Copying content..."
cp -r ../$WIKI_DIR/* .

# Add all changes
git add .

# Check if there are any changes
if git diff --quiet HEAD; then
    echo -e "${GREEN}No changes to sync${NC}"
    cd ..
    rm -rf $TEMP_DIR
    exit 0
fi

# Commit changes
echo "Committing changes..."
git commit -m "Sync wiki content from main repository"

# Push changes (using main branch instead of master)
echo "Pushing changes..."
if git push origin main; then
    echo -e "${GREEN}Successfully pushed changes${NC}"
else
    echo -e "${RED}Failed to push changes. Trying 'master' branch...${NC}"
    if git push origin master; then
        echo -e "${GREEN}Successfully pushed changes to master branch${NC}"
    else
        echo -e "${RED}Failed to push changes. Please check your repository settings.${NC}"
        cd ..
        rm -rf $TEMP_DIR
        exit 1
    fi
fi

# Cleanup
cd ..
rm -rf $TEMP_DIR

echo -e "${GREEN}Wiki sync completed successfully${NC}" 