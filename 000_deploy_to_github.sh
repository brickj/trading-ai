#!/bin/bash
# Trading AI - GitHub Deployment Script
# This script commits and pushes changes to GitHub

echo "🚀 TRADING AI - GITHUB DEPLOYMENT"
echo "=================================="
echo "Committing and pushing changes to GitHub..."
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

# Function to check authentication
check_auth() {
    print_status "Checking GitHub authentication..."
    
    # Test if we can access the repository
    if git ls-remote origin > /dev/null 2>&1; then
        print_success "GitHub authentication is working"
        return 0
    else
        print_warning "GitHub authentication may need setup"
        return 1
    fi
}

# Function to setup authentication
setup_auth() {
    echo ""
    print_status "Setting up GitHub authentication..."
    echo ""
    echo "You have several options for GitHub authentication:"
    echo ""
    echo "1. Personal Access Token (Recommended)"
    echo "   - Go to GitHub.com → Settings → Developer settings → Personal access tokens"
    echo "   - Generate a new token with 'repo' scope"
    echo "   - Use your username and the token as password"
    echo ""
    echo "2. SSH Key (More secure)"
    echo "   - Generate SSH key: ssh-keygen -t ed25519 -C 'your-email@example.com'"
    echo "   - Add to GitHub: Settings → SSH and GPG keys"
    echo ""
    echo "3. GitHub CLI (Easiest)"
    echo "   - Install: brew install gh"
    echo "   - Login: gh auth login"
    echo ""
    
    read -p "Which method would you like to use? (1/2/3): " auth_method
    
    case $auth_method in
        1)
            print_status "Using Personal Access Token method..."
            print_status "When prompted, use your GitHub username and Personal Access Token as password"
            ;;
        2)
            print_status "Using SSH method..."
            if ! ssh -T git@github.com 2>&1 | grep -q "successfully authenticated"; then
                print_error "SSH authentication failed. Please set up SSH keys first."
                print_error "Run: ssh-keygen -t ed25519 -C 'your-email@example.com'"
                print_error "Then add the public key to GitHub"
                exit 1
            fi
            print_success "SSH authentication working"
            ;;
        3)
            print_status "Using GitHub CLI method..."
            if ! command -v gh &> /dev/null; then
                print_error "GitHub CLI not installed. Install with: brew install gh"
                exit 1
            fi
            gh auth login
            ;;
        *)
            print_error "Invalid choice"
            exit 1
            ;;
    esac
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

# Check authentication
if ! check_auth; then
    setup_auth
fi

# Function to sync with remote repository
sync_with_remote() {
    print_status "Syncing local repository with GitHub..."
    
    # Fetch latest changes from remote
    print_status "Fetching latest changes from GitHub..."
    git fetch origin
    
    if [ $? -ne 0 ]; then
        print_error "Failed to fetch from remote repository"
        return 1
    fi
    
    # Check if local branch is behind remote
    LOCAL=$(git rev-parse HEAD)
    REMOTE=$(git rev-parse origin/main)
    
    if [ "$LOCAL" = "$REMOTE" ]; then
        print_success "Local repository is up to date with GitHub"
        return 0
    fi
    
    # Check if local is behind remote
    if git merge-base --is-ancestor "$LOCAL" "$REMOTE"; then
        print_warning "Local repository is behind GitHub. Pulling latest changes..."
        git pull origin main
        
        if [ $? -eq 0 ]; then
            print_success "Successfully pulled latest changes from GitHub"
            return 0
        else
            print_error "Failed to pull changes from GitHub"
            return 1
        fi
    fi
    
    # Check if local is ahead of remote
    if git merge-base --is-ancestor "$REMOTE" "$LOCAL"; then
        print_warning "Local repository is ahead of GitHub. This is normal for new commits."
        return 0
    fi
    
    # Check if branches have diverged
    print_warning "Local and remote branches have diverged"
    print_status "Local commits: $(git rev-list --count origin/main..HEAD)"
    print_status "Remote commits: $(git rev-list --count HEAD..origin/main)"
    
    echo ""
    echo "You have several options:"
    echo "1. Merge remote changes (recommended)"
    echo "2. Rebase local changes on top of remote"
    echo "3. Force push (DANGEROUS - will overwrite remote changes)"
    echo "4. Abort and resolve manually"
    echo ""
    
    read -p "Choose an option (1/2/3/4): " sync_option
    
    case $sync_option in
        1)
            print_status "Merging remote changes..."
            git merge origin/main
            if [ $? -eq 0 ]; then
                print_success "Successfully merged remote changes"
                return 0
            else
                print_error "Merge failed. Please resolve conflicts manually"
                return 1
            fi
            ;;
        2)
            print_status "Rebasing local changes on top of remote..."
            git rebase origin/main
            if [ $? -eq 0 ]; then
                print_success "Successfully rebased local changes"
                return 0
            else
                print_error "Rebase failed. Please resolve conflicts manually"
                return 1
            fi
            ;;
        3)
            print_warning "Force pushing local changes (this will overwrite remote changes)"
            read -p "Are you sure? This action cannot be undone (y/N): " confirm
            if [[ $confirm =~ ^[Yy]$ ]]; then
                git push --force origin main
                if [ $? -eq 0 ]; then
                    print_success "Force push completed"
                    return 0
                else
                    print_error "Force push failed"
                    return 1
                fi
            else
                print_status "Force push cancelled"
                return 1
            fi
            ;;
        4)
            print_status "Sync aborted. Please resolve conflicts manually"
            return 1
            ;;
        *)
            print_error "Invalid option"
            return 1
            ;;
    esac
}

# Sync with remote repository
if ! sync_with_remote; then
    print_error "Failed to sync with remote repository"
    print_error "Please resolve any conflicts and try again"
    exit 1
fi

# Check if there are any changes to commit
if git diff-index --quiet HEAD --; then
    print_warning "No changes to commit. Working directory is clean."
    exit 0
fi

# Get commit message from user or use default
if [ -n "$1" ]; then
    COMMIT_MESSAGE="$1"
else
    read -p "Enter commit message (or press Enter for default): " COMMIT_MESSAGE
    if [ -z "$COMMIT_MESSAGE" ]; then
        COMMIT_MESSAGE="Update Trading AI application - $(date '+%Y-%m-%d %H:%M:%S')"
    fi
fi

print_status "Commit message: $COMMIT_MESSAGE"

# Add all changes
print_status "Adding all changes to git..."
git add .

if [ $? -eq 0 ]; then
    print_success "Changes added successfully"
else
    print_error "Failed to add changes"
    exit 1
fi

# Commit changes
print_status "Committing changes..."
git commit -m "$COMMIT_MESSAGE"

if [ $? -eq 0 ]; then
    print_success "Changes committed successfully"
else
    print_error "Failed to commit changes"
    exit 1
fi

# Push to GitHub
print_status "Pushing to GitHub..."
git push origin main

if [ $? -eq 0 ]; then
    print_success "Successfully pushed to GitHub!"
    echo ""
    echo "🎉 DEPLOYMENT COMPLETE!"
    echo "======================"
    echo "✅ Changes committed with message: $COMMIT_MESSAGE"
    echo "✅ Changes pushed to GitHub"
    echo ""
    print_status "Your Trading AI application is now updated on GitHub"
else
    print_error "Failed to push to GitHub"
    print_error "This might be due to authentication issues."
    print_error "Try running the script again to set up authentication."
    exit 1
fi 