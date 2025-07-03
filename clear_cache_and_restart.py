#!/usr/bin/env python3
"""
Script to clear the cache and restart the app to ensure fresh data.
"""
import os
import sys
import subprocess
import time
import signal

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the cache clearing function
from src.core.cache import clear_cache

def kill_existing_app():
    """Kill any existing app processes"""
    print("Stopping any running app instances...")
    try:
        # Find processes running start_app.py
        ps_cmd = "ps aux | grep 'python3 start_app.py' | grep -v grep | awk '{print $2}'"
        pids = subprocess.check_output(ps_cmd, shell=True).decode().strip().split('\n')
        
        # Kill each process
        for pid in pids:
            if pid:
                try:
                    os.kill(int(pid), signal.SIGTERM)
                    print(f"Killed process {pid}")
                except ProcessLookupError:
                    pass
                except ValueError:
                    pass
        
        # Wait a moment to ensure processes are terminated
        time.sleep(1)
        return True
    except Exception as e:
        print(f"Error killing processes: {e}")
        return False

def clear_all_cache():
    """Clear all cache entries"""
    print("Clearing cache...")
    result = clear_cache()
    print(f"Cache cleared: {result}")
    return result

def start_app():
    """Start the app in a new process"""
    print("Starting app...")
    subprocess.Popen(["python3", "start_app.py"])
    print("App started. Please wait a few seconds for it to initialize.")

if __name__ == "__main__":
    kill_existing_app()
    clear_all_cache()
    start_app()
    print("\nDone! The app has been restarted with a fresh cache.")
    print("You can now test the standard analysis endpoint.")
