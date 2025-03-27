#!/bin/bash

# Configuration
WIKI_REPO="https://github.com/FairGigAI/PEPPER.wiki.git"
WIKI_DIR="wiki-content"
TEMP_DIR=".wiki-temp"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}Starting wiki sync...${NC}"

# Create temporary directory
rm -rf $TEMP_DIR
mkdir $TEMP_DIR
cd $TEMP_DIR

# Clone wiki repository
echo "Cloning wiki repository..."
git clone $WIKI_REPO .

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

# Push changes
echo "Pushing changes..."
git push origin master

# Cleanup
cd ..
rm -rf $TEMP_DIR

echo -e "${GREEN}Wiki sync completed successfully${NC}" 