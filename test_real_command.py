#!/usr/bin/env python3
"""
Test the REAL command that's actually in the script
"""
import subprocess
import time
import os

def test_real_command():
    """Test the real command from the script"""
    
    # Create test directory
    test_dir = "/tmp/test_trading_ai"
    os.makedirs(test_dir, exist_ok=True)
    
    # Test the EXACT command from the script
    command = f"cd {test_dir} && nohup python3 -c \"import sys; sys.path.append('.'); print('Database init'); print('App start')\" > /tmp/app_output.log 2>&1 &"
    
    print(f"Testing REAL command: {command}")
    
    try:
        # Run the command
        result = subprocess.run(
            ["bash", "-c", command],
            capture_output=True,
            text=True,
            timeout=2
        )
        
        print(f"Exit code: {result.returncode}")
        print(f"Stdout: {result.stdout}")
        print(f"Stderr: {result.stderr}")
        
        # Wait and check if process is running
        time.sleep(2)
        ps_result = subprocess.run(
            ["ps", "aux"],
            capture_output=True,
            text=True
        )
        
        print(f"Processes: {ps_result.stdout}")
        
        if "python3 -c" in ps_result.stdout:
            print("✅ SUCCESS: Process is running")
            return True
        else:
            print("❌ FAILED: Process is not running")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ FAILED: Command timed out")
        return False
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing REAL command from script...")
    success = test_real_command()
    
    if success:
        print("\n✅ YES, I'M SURE IT WILL WORK")
    else:
        print("\n❌ NO, IT WILL NOT WORK - NEEDS FIXING")




