#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Print with color
print_status() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}! $1${NC}"
}

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
if ! command_exists git; then
    print_error "Git is not installed. Please install Git first."
    exit 1
fi

# Get the repository name from the current directory
REPO_NAME=$(basename $(git rev-parse --show-toplevel))
WIKI_REPO="https://github.com/FairGigAI/${REPO_NAME}.wiki.git"
TEMP_DIR=".wiki-temp"

print_status "Starting wiki sync..."

# Create temporary directory
rm -rf "$TEMP_DIR"
mkdir -p "$TEMP_DIR"

# Clone wiki repository
print_status "Cloning wiki repository..."
if git clone "$WIKI_REPO" "$TEMP_DIR"; then
    print_status "Successfully cloned wiki repository"
else
    print_warning "Wiki repository not found. Please create it first:"
    print_warning "1. Go to https://github.com/FairGigAI/${REPO_NAME}/wiki"
    print_warning "2. Click 'Create the first page'"
    print_warning "3. Add any content and save"
    print_warning "4. Run this script again"
    rm -rf "$TEMP_DIR"
    exit 1
fi

# Copy content
print_status "Copying content..."
cp -r wiki-content/* "$TEMP_DIR/"

# Commit changes
print_status "Committing changes..."
cd "$TEMP_DIR"
git add .
git commit -m "Sync wiki content from main repository"

# Push changes
print_status "Pushing changes..."
# Try to determine the default branch
DEFAULT_BRANCH=$(git remote show origin | grep "HEAD branch" | cut -d ":" -f 2 | tr -d " ")
if [ -z "$DEFAULT_BRANCH" ]; then
    DEFAULT_BRANCH="master"
fi

# Try to push to the default branch
if git push origin "$DEFAULT_BRANCH"; then
    print_status "Successfully pushed changes to $DEFAULT_BRANCH branch"
else
    print_warning "Failed to push to $DEFAULT_BRANCH branch. Trying 'master' branch..."
    if git push origin master; then
        print_status "Successfully pushed changes to master branch"
    else
        print_error "Failed to push changes to any branch"
        cd ..
        rm -rf "$TEMP_DIR"
        exit 1
    fi
fi

# Clean up
cd ..
rm -rf "$TEMP_DIR"

print_status "Wiki sync completed successfully" 