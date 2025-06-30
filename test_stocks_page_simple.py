#!/usr/bin/env python3
"""
Simple test for the /stocks page
This test will verify that the API returns data and then provide instructions for manual verification
"""

import sys
import os
import time
import json
import logging
import requests
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

def test_api_endpoint(base_url="http://localhost:5001"):
    """Test the /api/sp500_analysis endpoint directly"""
    logger.info("Testing /api/sp500_analysis endpoint...")
    
    try:
        # Make a direct request to the API
        start_time = time.time()
        response = requests.get(f"{base_url}/api/sp500_analysis")
        end_time = time.time()
        response_time_ms = int((end_time - start_time) * 1000)
        
        logger.info(f"API response status code: {response.status_code} (took {response_time_ms}ms)")
        
        if response.status_code == 200:
            # Parse the response
            data = response.json()
            logger.info(f"API response success: {data.get('success', False)}")
            
            # Check if the response has the expected structure
            if data.get('success') and 'data' in data:
                enhanced_analysis = data['data'].get('enhanced_analysis', [])
                logger.info(f"Enhanced analysis entries: {len(enhanced_analysis)}")
                
                # Check for winners and losers
                winners = [s for s in enhanced_analysis if s.get('type') == 'winner']
                losers = [s for s in enhanced_analysis if s.get('type') == 'loser']
                logger.info(f"Winners: {len(winners)}, Losers: {len(losers)}")
                
                # Print some details about the winners and losers
                for i, winner in enumerate(winners):
                    logger.info(f"Winner {i+1}: {winner.get('symbol')} - Price: {winner.get('price_data', {}).get('current_price')}")
                
                for i, loser in enumerate(losers):
                    logger.info(f"Loser {i+1}: {loser.get('symbol')} - Price: {loser.get('price_data', {}).get('current_price')}")
                
                # Save the API response for debugging
                with open('stocks_api_response.json', 'w') as f:
                    json.dump(data, f, indent=2)
                logger.info(f"API response saved to stocks_api_response.json")
                
                # Return success
                return True, data
            else:
                error_msg = f"Invalid API response structure: {data}"
                logger.error(error_msg)
                return False, error_msg
        else:
            error_msg = f"API request failed with status code: {response.status_code}"
            logger.error(error_msg)
            return False, error_msg
    
    except Exception as e:
        error_msg = f"Exception during API test: {e}"
        logger.error(error_msg)
        return False, error_msg

def provide_manual_test_instructions(base_url="http://localhost:5001"):
    """Provide instructions for manual verification"""
    print("\n" + "="*80)
    print("MANUAL VERIFICATION INSTRUCTIONS")
    print("="*80)
    print(f"1. Open your browser and navigate to: {base_url}/stocks")
    print("2. Verify that the page loads without errors")
    print("3. Check that the 'Top 3 Winners Today' section shows data")
    print("4. Check that the 'Bottom 3 Losers Today' section shows data")
    print("5. Check that the main table shows stock data")
    print("6. Try clicking the 'Refresh Data' button and verify it works")
    print("="*80)
    print("If all of these checks pass, the page is working correctly!")
    print("="*80)

def main():
    """Main function"""
    logger.info("Starting simple stocks page test...")
    
    # Test the API endpoint
    api_success, api_data = test_api_endpoint()
    
    # Print summary
    print("\n=== TEST SUMMARY ===")
    print(f"API Test: {'✅' if api_success else '❌'}")
    
    if api_success and isinstance(api_data, dict):
        data_dict = api_data.get('data', {})
        if isinstance(data_dict, dict):
            enhanced_analysis = data_dict.get('enhanced_analysis', [])
            winners = [s for s in enhanced_analysis if s.get('type') == 'winner']
            losers = [s for s in enhanced_analysis if s.get('type') == 'loser']
            print(f"  - Winners found: {len(winners)}")
            print(f"  - Losers found: {len(losers)}")
            print(f"  - Total stocks: {len(enhanced_analysis)}")
        
        # Provide manual test instructions
        provide_manual_test_instructions()
    else:
        print(f"  - Error: {api_data}")
    
    return 0 if api_success else 1

if __name__ == "__main__":
    sys.exit(main()) 