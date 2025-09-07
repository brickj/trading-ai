#!/bin/bash
# Trading AI - GitHub Pull Script
# This script pulls the latest changes from GitHub

echo "📥 TRADING AI - GITHUB PULL"
echo "============================"
echo "Pulling latest changes from GitHub..."
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    print_error "Not in a git repository. Please initialize git first:"
    print_error "  git init"
    print_error "  git remote add origin <your-github-repo-url>"
    exit 1
fi

# Check if remote origin exists
if ! git remote get-url origin > /dev/null 2>&1; then
    print_error "No remote origin configured. Please add your GitHub repository:"
    print_error "  git remote add origin https://github.com/brickj/trading-ai.git"
    exit 1
fi

# Show current status
print_status "Current repository status:"
git status --short

echo ""

# Check if there are uncommitted changes
if ! git diff-index --quiet HEAD --; then
    print_warning "You have uncommitted changes in your working directory."
    echo ""
    echo "You have several options:"
    echo "1. Stash changes and pull (recommended)"
    echo "2. Commit changes first, then pull"
    echo "3. Discard changes and pull (WARNING: This will lose your changes)"
    echo "4. Cancel and handle changes manually"
    echo ""
    
    read -p "What would you like to do? (1/2/3/4): " choice
    
    case $choice in
        1)
            print_status "Stashing changes..."
            git stash push -m "Auto-stash before pull - $(date '+%Y-%m-%d %H:%M:%S')"
            if [ $? -eq 0 ]; then
                print_success "Changes stashed successfully"
                STASHED=true
            else
                print_error "Failed to stash changes"
                exit 1
            fi
            ;;
        2)
            print_status "Please commit your changes first, then run this script again."
            exit 0
            ;;
        3)
            print_warning "Discarding all uncommitted changes..."
            read -p "Are you sure? This will permanently delete your changes! (yes/no): " confirm
            if [ "$confirm" = "yes" ]; then
                git reset --hard HEAD
                git clean -fd
                print_success "Changes discarded"
            else
                print_status "Operation cancelled"
                exit 0
            fi
            ;;
        4)
            print_status "Operation cancelled. Please handle your changes manually."
            exit 0
            ;;
        *)
            print_error "Invalid choice"
            exit 1
            ;;
    esac
fi

# Fetch latest changes from remote
print_status "Fetching latest changes from GitHub..."
git fetch origin

if [ $? -eq 0 ]; then
    print_success "Successfully fetched from GitHub"
else
    print_error "Failed to fetch from GitHub"
    exit 1
fi

# Check if there are any updates available
LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse origin/main)

if [ "$LOCAL" = "$REMOTE" ]; then
    print_success "Your local repository is already up to date!"
    if [ "$STASHED" = true ]; then
        print_status "Restoring stashed changes..."
        git stash pop
        if [ $? -eq 0 ]; then
            print_success "Stashed changes restored"
        else
            print_warning "There were conflicts when restoring stashed changes"
            print_warning "Please resolve them manually with: git status"
        fi
    fi
    exit 0
fi

# Show what will be updated
print_status "Updates available. Here's what will be changed:"
git log --oneline HEAD..origin/main

echo ""

# Pull the latest changes
print_status "Pulling latest changes from GitHub..."
git pull origin main

if [ $? -eq 0 ]; then
    print_success "Successfully pulled latest changes from GitHub!"
    
    # Restore stashed changes if any
    if [ "$STASHED" = true ]; then
        print_status "Restoring stashed changes..."
        git stash pop
        if [ $? -eq 0 ]; then
            print_success "Stashed changes restored"
        else
            print_warning "There were conflicts when restoring stashed changes"
            print_warning "Please resolve them manually with: git status"
        fi
    fi
    
    echo ""
    echo "🎉 UPDATE COMPLETE!"
    echo "=================="
    echo "✅ Latest changes pulled from GitHub"
    echo "✅ Local repository updated"
    echo ""
    print_status "Your Trading AI application is now up to date"
    
    # Show final status
    echo ""
    print_status "Current repository status:"
    git status --short
    
else
    print_error "Failed to pull from GitHub"
    print_error "This might be due to merge conflicts or authentication issues."
    
    # Restore stashed changes if pull failed
    if [ "$STASHED" = true ]; then
        print_status "Restoring stashed changes due to pull failure..."
        git stash pop
    fi
    
    exit 1
fi
