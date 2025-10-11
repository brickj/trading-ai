#!/usr/bin/env python3
"""
Trading AI - GitHub Update Script
This script commits local changes to GitHub and updates the EC2 instance with the latest code.
Does NOT start/stop the application - use a separate script for that.
"""

import subprocess
import sys
import os
import time
import tempfile
from datetime import datetime
from pathlib import Path

class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'

class EC2GitHubUpdater:
    def __init__(self):
        # EC2 connection details (from your existing setup)
        self.pem_file = "/Users/rick/Desktop/stuff/keys/aws_key4.pem"
        self.elastic_ip = "54.163.187.86"
        self.ssh_user = "ubuntu"
        self.remote_repo_dir = "/home/ubuntu/trading-ai"
        self.app_name = "trading-ai"
        
        # Local paths
        self.local_repo_dir = "/Users/rick/Desktop/stuff/code_projects/IBS/trading"
        
        # Application details
        self.app_port = 5001
        self.process_name = "start_app.py"

    def print_status(self, msg): 
        print(f"{Colors.BLUE}[INFO]{Colors.NC} {msg}")
    
    def print_success(self, msg): 
        print(f"{Colors.GREEN}[SUCCESS]{Colors.NC} {msg}")
    
    def print_warning(self, msg): 
        print(f"{Colors.YELLOW}[WARNING]{Colors.NC} {msg}")
    
    def print_error(self, msg): 
        print(f"{Colors.RED}[ERROR]{Colors.NC} {msg}")

    def run_command(self, command, cwd=None, capture_output=True):
        """Run a shell command and return the result"""
        try:
            if isinstance(command, str):
                command = command.split()
            
            result = subprocess.run(
                command,
                cwd=cwd,
                capture_output=capture_output,
                text=True,
                timeout=300  # 5 minute timeout
            )
            return result
        except subprocess.TimeoutExpired:
            self.print_error(f"Command timed out: {' '.join(command)}")
            return None
        except Exception as e:
            self.print_error(f"Command failed: {e}")
            return None

    def check_git_status(self):
        """Check if we're in a git repository and have changes"""
        self.print_status("Checking git status...")
        
        # Check if we're in a git repo
        result = self.run_command("git rev-parse --git-dir", cwd=self.local_repo_dir)
        if not result or result.returncode != 0:
            self.print_error("Not in a git repository!")
            return False
        
        # Check if there are changes to commit
        result = self.run_command("git diff-index --quiet HEAD --", cwd=self.local_repo_dir)
        if result and result.returncode == 0:
            self.print_warning("No changes to commit. Working directory is clean.")
            return False
        
        # Show what changes we have
        result = self.run_command("git status --porcelain", cwd=self.local_repo_dir)
        if result and result.stdout.strip():
            self.print_status("Changes detected:")
            for line in result.stdout.strip().split('\n'):
                print(f"  {line}")
        
        return True

    def sync_with_github(self):
        """Sync local repository with GitHub"""
        self.print_status("Syncing with GitHub...")
        
        # Fetch latest changes
        result = self.run_command("git fetch origin", cwd=self.local_repo_dir)
        if not result or result.returncode != 0:
            self.print_error("Failed to fetch from GitHub")
            return False
        
        # Check if we need to pull
        result = self.run_command("git rev-parse HEAD", cwd=self.local_repo_dir)
        if not result:
            return False
        local_commit = result.stdout.strip()
        
        result = self.run_command("git rev-parse origin/main", cwd=self.local_repo_dir)
        if not result:
            return False
        remote_commit = result.stdout.strip()
        
        if local_commit != remote_commit:
            self.print_warning("Local repository is behind GitHub. Pulling latest changes...")
            result = self.run_command("git pull origin main", cwd=self.local_repo_dir)
            if not result or result.returncode != 0:
                self.print_error("Failed to pull from GitHub")
                return False
            self.print_success("Successfully pulled latest changes")
        
        return True

    def commit_and_push(self, commit_message=None):
        """Commit local changes and push to GitHub"""
        self.print_status("Committing and pushing changes to GitHub...")
        
        if not commit_message:
            commit_message = f"Fix datetime comparison error - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        # Add all changes
        result = self.run_command("git add .", cwd=self.local_repo_dir)
        if not result or result.returncode != 0:
            self.print_error("Failed to add changes")
            return False
        
        # Commit changes
        result = self.run_command(f"git commit -m '{commit_message}'", cwd=self.local_repo_dir)
        if not result or result.returncode != 0:
            self.print_error("Failed to commit changes")
            return False
        
        # Push to GitHub
        result = self.run_command("git push origin main", cwd=self.local_repo_dir)
        if not result or result.returncode != 0:
            self.print_error("Failed to push to GitHub")
            return False
        
        self.print_success(f"Successfully pushed to GitHub with message: {commit_message}")
        return True

    def test_ssh_connection(self):
        """Test SSH connection to EC2"""
        self.print_status(f"Testing SSH connection to {self.elastic_ip}...")
        
        result = self.run_command([
            "ssh", "-i", self.pem_file,
            "-o", "StrictHostKeyChecking=no",
            "-o", "UserKnownHostsFile=/dev/null",
            "-o", "ConnectTimeout=10",
            f"{self.ssh_user}@{self.elastic_ip}",
            "echo 'SSH connection successful'"
        ])
        
        if result and result.returncode == 0:
            self.print_success("SSH connection successful")
            return True
        else:
            self.print_error("SSH connection failed")
            return False


    def update_code_on_ec2(self):
        """Pull latest code from GitHub on EC2 with conflict resolution"""
        self.print_status("Updating code on EC2 from GitHub...")
        
        update_script = f"""
        cd {self.remote_repo_dir}
        
        # Check if it's a git repository
        if [ ! -d ".git" ]; then
            echo "ERROR: Not a git repository!"
            exit 1
        fi
        
        # Check for local changes and handle them
        echo "Checking for local changes..."
        if ! git diff-index --quiet HEAD --; then
            echo "⚠️ Local changes detected. Stashing them..."
            git stash push -m "Auto-stash before update $(date)"
            echo "✅ Local changes stashed"
        fi
        
        # Fetch and pull latest changes
        echo "Fetching latest changes from GitHub..."
        git fetch origin
        
        if [ $? -ne 0 ]; then
            echo "ERROR: Failed to fetch from GitHub"
            exit 1
        fi
        
        echo "Pulling latest changes..."
        git pull origin main
        
        if [ $? -ne 0 ]; then
            echo "ERROR: Failed to pull from GitHub"
            echo "Attempting to resolve conflicts..."
            
            # Try to reset to remote state if pull fails
            echo "Resetting to remote state..."
            git reset --hard origin/main
            
            if [ $? -ne 0 ]; then
                echo "ERROR: Failed to reset to remote state"
                exit 1
            fi
        fi
        
        echo "Code updated successfully"
        
        # Show the latest commit
        echo "Latest commit:"
        git log -1 --oneline
        
        # Check for missing files and restore them if needed
        echo "Checking for missing files..."
        if [ ! -f "src/web/routes/__init__.py" ]; then
            echo "⚠️ Missing web routes directory, creating it..."
            mkdir -p src/web/routes
            touch src/web/routes/__init__.py
        fi
        
        if [ ! -f "src/web/templates/__init__.py" ]; then
            echo "⚠️ Missing web templates directory, creating it..."
            mkdir -p src/web/templates
            touch src/web/templates/__init__.py
        fi
        
        # Check if the fix is present
        if grep -q "cutoff_date_only = cutoff_date.date()" src/data/historical_data_updater.py; then
            echo "✅ Datetime comparison fix is present"
        else
            echo "❌ Datetime comparison fix not found"
            exit 1
        fi
        
        # Fix file permissions to prevent future conflicts
        echo "Fixing file permissions..."
        find . -type f -name "*.py" -exec chmod 644 {{}} \\;
        find . -type f -name "*.md" -exec chmod 644 {{}} \\;
        find . -type f -name "*.html" -exec chmod 644 {{}} \\;
        find . -type f -name "*.css" -exec chmod 644 {{}} \\;
        find . -type f -name "*.js" -exec chmod 644 {{}} \\;
        find . -type f -name "*.txt" -exec chmod 644 {{}} \\;
        find . -type f -name "*.json" -exec chmod 644 {{}} \\;
        find . -type f -name "*.yaml" -exec chmod 644 {{}} \\;
        find . -type f -name "*.yml" -exec chmod 644 {{}} \\;
        echo "✅ File permissions fixed"
        """
        
        result = self.run_command([
            "ssh", "-i", self.pem_file,
            "-o", "StrictHostKeyChecking=no",
            "-o", "UserKnownHostsFile=/dev/null",
            f"{self.ssh_user}@{self.elastic_ip}",
            update_script
        ])
        
        if result and result.returncode == 0:
            self.print_success("Code updated successfully on EC2")
            return True
        else:
            self.print_error("Failed to update code on EC2")
            if result:
                print(result.stderr)
            return False


    def sync_missing_files(self):
        """Sync missing files from local to EC2"""
        self.print_status("Syncing missing files to EC2...")
        
        # Files that should exist on EC2 but might be missing
        critical_files = [
            "src/web/routes/__init__.py",
            "src/web/templates/__init__.py", 
            "src/web/services/__init__.py",
            "src/web/utils/__init__.py",
            "src/web/repositories/__init__.py"
        ]
        
        # Config files that are in .gitignore but needed on EC2
        config_files = [
            "src/core/config.py"  # The actual config file with hardcoded API keys
        ]
        
        # Sync critical files (only if they don't exist on EC2)
        for file_path in critical_files:
            local_file = f"{self.local_repo_dir}/{file_path}"
            remote_file = f"{self.remote_repo_dir}/{file_path}"
            
            # Check if file exists on EC2 first
            check_script = f"test -f {remote_file}"
            result = self.run_command([
                "ssh", "-i", self.pem_file,
                "-o", "StrictHostKeyChecking=no",
                "-o", "UserKnownHostsFile=/dev/null",
                f"{self.ssh_user}@{self.elastic_ip}",
                check_script
            ])
            
            # Only sync if file doesn't exist on EC2 AND exists locally
            if result and result.returncode != 0 and os.path.exists(local_file):
                self.print_status(f"File missing on EC2, syncing: {file_path}")
                
                # Copy file to EC2
                copy_script = f"""
                mkdir -p $(dirname {remote_file})
                cat > {remote_file} << 'EOF'
                """
                
                # Read local file content
                try:
                    with open(local_file, 'r') as f:
                        content = f.read()
                    copy_script += content + "\nEOF"
                    
                    result = self.run_command([
                        "ssh", "-i", self.pem_file,
                        "-o", "StrictHostKeyChecking=no",
                        "-o", "UserKnownHostsFile=/dev/null",
                        f"{self.ssh_user}@{self.elastic_ip}",
                        copy_script
                    ])
                    
                    if result and result.returncode == 0:
                        self.print_success(f"Synced missing file: {file_path}")
                    else:
                        self.print_warning(f"Failed to sync {file_path}")
                        
                except Exception as e:
                    self.print_warning(f"Could not read {local_file}: {e}")
            elif result and result.returncode == 0:
                self.print_status(f"File already exists on EC2: {file_path}")
            else:
                self.print_status(f"File not found locally: {file_path}")
        
        # Sync config files (from .gitignore)
        self.print_status("Syncing config files from .gitignore...")
        for file_path in config_files:
            local_file = f"{self.local_repo_dir}/{file_path}"
            remote_file = f"{self.remote_repo_dir}/{file_path}"
            
            # Check if file exists locally
            if os.path.exists(local_file):
                self.print_status(f"Found config file: {file_path}")
                
                # Copy file to EC2 using SCP for better handling of binary files
                result = self.run_command([
                    "scp", "-i", self.pem_file,
                    "-o", "StrictHostKeyChecking=no",
                    "-o", "UserKnownHostsFile=/dev/null",
                    local_file,
                    f"{self.ssh_user}@{self.elastic_ip}:{remote_file}"
                ])
                
                if result and result.returncode == 0:
                    self.print_success(f"Synced config file: {file_path}")
                else:
                    self.print_warning(f"Failed to sync config file: {file_path}")
            else:
                self.print_warning(f"Config file not found locally: {file_path}")
        
        return True

    def sync_config_files(self):
        """Sync configuration files that are in .gitignore"""
        self.print_status("Syncing configuration files from .gitignore...")
        
        # The actual config file with hardcoded API keys
        config_files = [
            "src/core/config.py"  # Contains hardcoded API keys from config.template.py
        ]
        
        synced_count = 0
        for file_path in config_files:
            local_file = f"{self.local_repo_dir}/{file_path}"
            remote_file = f"{self.remote_repo_dir}/{file_path}"
            
            # Check if file exists locally
            if os.path.exists(local_file):
                self.print_status(f"Found config file: {file_path}")
                
                # Check if file already exists on EC2
                check_script = f"test -f {remote_file}"
                check_result = self.run_command([
                    "ssh", "-i", self.pem_file,
                    "-o", "StrictHostKeyChecking=no",
                    "-o", "UserKnownHostsFile=/dev/null",
                    f"{self.ssh_user}@{self.elastic_ip}",
                    check_script
                ])
                
                # Only sync if file doesn't exist on EC2 (config files should be unique)
                if check_result and check_result.returncode != 0:
                    # Create remote directory if it doesn't exist
                    remote_dir = os.path.dirname(remote_file)
                    mkdir_script = f"mkdir -p {remote_dir}"
                    
                    self.run_command([
                        "ssh", "-i", self.pem_file,
                        "-o", "StrictHostKeyChecking=no",
                        "-o", "UserKnownHostsFile=/dev/null",
                        f"{self.ssh_user}@{self.elastic_ip}",
                        mkdir_script
                    ])
                    
                    # Copy file to EC2 using SCP
                    result = self.run_command([
                        "scp", "-i", self.pem_file,
                        "-o", "StrictHostKeyChecking=no",
                        "-o", "UserKnownHostsFile=/dev/null",
                        local_file,
                        f"{self.ssh_user}@{self.elastic_ip}:{remote_file}"
                    ])
                    
                    if result and result.returncode == 0:
                        self.print_success(f"Synced config file: {file_path}")
                        synced_count += 1
                    else:
                        self.print_warning(f"Failed to sync config file: {file_path}")
                        if result and result.stderr:
                            print(f"Error: {result.stderr}")
                else:
                    self.print_status(f"Config file already exists on EC2: {file_path}")
            else:
                self.print_status(f"Config file not found locally: {file_path}")
        
        if synced_count > 0:
            self.print_success(f"Successfully synced {synced_count} config files")
        else:
            self.print_warning("No config files found to sync")
        
        return True



    def run(self, commit_message=None):
        """Run the complete update process"""
        print("🚀 TRADING AI - GITHUB UPDATE")
        print("=============================")
        print(f"Local repo: {self.local_repo_dir}")
        print(f"EC2 instance: {self.elastic_ip}")
        print(f"Remote repo: {self.remote_repo_dir}")
        print("")
        
        # Step 1: Check git status
        if not self.check_git_status():
            self.print_warning("No changes to commit. Continuing with EC2 update...")
        else:
            # Step 2: Sync with GitHub
            if not self.sync_with_github():
                self.print_error("Failed to sync with GitHub")
                return False
            
            # Step 3: Commit and push
            if not self.commit_and_push(commit_message):
                self.print_error("Failed to commit and push to GitHub")
                return False
        
        # Step 4: Test SSH connection
        if not self.test_ssh_connection():
            self.print_error("Cannot connect to EC2 instance")
            return False
        
        # Step 5: Update code on EC2
        if not self.update_code_on_ec2():
            self.print_error("Failed to update code on EC2")
            return False
        
        # Step 6: Sync missing files
        if not self.sync_missing_files():
            self.print_warning("Some files may not have synced properly")
        
        # Step 7: Sync config files from .gitignore
        if not self.sync_config_files():
            self.print_warning("Some config files may not have synced properly")
        
        print("\n" + "="*60)
        print("🎉 GITHUB UPDATE COMPLETE!")
        print("="*60)
        print(f"✅ Local changes committed and pushed to GitHub")
        print(f"✅ EC2 instance updated with latest code")
        print(f"✅ Config files synced from .gitignore")
        print("")
        print(f"🌐 Application URL: http://{self.elastic_ip}:{self.app_port}")
        print("")
        print("Next Steps:")
        print("1. Use a separate script to start/restart the application")
        print("2. Use a separate script to manage Go services")
        print("="*60)
        
        return True

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Update Trading AI code on EC2 from GitHub (no application management)')
    parser.add_argument('--commit-message', '-m', 
                       help='Custom commit message for the changes')
    parser.add_argument('--skip-git', action='store_true',
                       help='Skip git operations and only update EC2 code')
    
    args = parser.parse_args()
    
    updater = EC2GitHubUpdater()
    
    if args.skip_git:
        # Only update EC2, skip git operations
        print("🚀 TRADING AI - EC2 UPDATE ONLY")
        print("===============================")
        
        if not updater.test_ssh_connection():
            sys.exit(1)
        
        if not updater.update_code_on_ec2():
            sys.exit(1)
        
        if not updater.sync_missing_files():
            print("Warning: Some files may not have synced properly")
        
        if not updater.sync_config_files():
            print("Warning: Some config files may not have synced properly")
        
        print("\n🎉 EC2 UPDATE COMPLETE!")
        print("Next Steps:")
        print("1. Use a separate script to start/restart the application")
        print("2. Use a separate script to manage Go services")
    else:
        # Full update process
        success = updater.run(args.commit_message)
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
