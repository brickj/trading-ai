#!/usr/bin/env python3
"""
Debug test for the /stocks page and /api/sp500_analysis endpoint
"""

import sys
import os
import json
import time
import requests
from bs4 import BeautifulSoup
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

def test_api_endpoint():
    """Test the /api/sp500_analysis endpoint directly"""
    logger.info("Testing /api/sp500_analysis endpoint...")
    
    try:
        # Make a direct request to the API
        response = requests.get('http://localhost:5001/api/sp500_analysis')
        logger.info(f"API response status code: {response.status_code}")
        
        if response.status_code == 200:
            # Parse the response
            data = response.json()
            logger.info(f"API response success: {data.get('success', False)}")
            
            # Check if the response has the expected structure
            if 'data' in data:
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
                
                # Check for errors
                errors = data['data'].get('errors', [])
                logger.info(f"Errors: {len(errors)}")
                for error in errors:
                    logger.info(f"Error: {error}")
                
                return True, data
            else:
                logger.error(f"Invalid API response structure: {data}")
                return False, data
        else:
            logger.error(f"API request failed with status code: {response.status_code}")
            return False, {"error": f"Status code: {response.status_code}"}
    
    except Exception as e:
        logger.error(f"Exception during API test: {e}")
        return False, {"error": str(e)}

def test_stocks_page():
    """Test the /stocks page directly"""
    logger.info("Testing /stocks page...")
    
    try:
        # Make a direct request to the page
        response = requests.get('http://localhost:5001/stocks')
        logger.info(f"Page response status code: {response.status_code}")
        
        if response.status_code == 200:
            # Parse the HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Check for key elements
            refresh_btn = soup.find('button', id='refreshBtn')
            winners_list = soup.find('div', id='winnersList')
            losers_list = soup.find('div', id='losersList')
            stocks_table_body = soup.find('tbody', id='stocksTableBody')
            
            logger.info(f"Found refresh button: {refresh_btn is not None}")
            logger.info(f"Found winners list: {winners_list is not None}")
            logger.info(f"Found losers list: {losers_list is not None}")
            logger.info(f"Found stocks table body: {stocks_table_body is not None}")
            
            # Check for content in winners and losers lists
            winners_content = winners_list.get_text() if winners_list else ""
            losers_content = losers_list.get_text() if losers_list else ""
            
            logger.info(f"Winners list content length: {len(winners_content)}")
            logger.info(f"Losers list content length: {len(losers_content)}")
            
            # Check if the winners/losers summary section is visible
            winners_losers_summary = soup.find('div', id='winnersLosersSummary')
            if winners_losers_summary:
                style = winners_losers_summary.get('style', '')
                logger.info(f"Winners/losers summary style: {style}")
                is_visible = 'display: none' not in style
                logger.info(f"Winners/losers summary is visible: {is_visible}")
            
            # Check for any JavaScript errors (can't do this with requests)
            logger.info("Note: Can't check for JavaScript errors with requests")
            
            return True, {
                "refresh_btn_exists": refresh_btn is not None,
                "winners_list_exists": winners_list is not None,
                "losers_list_exists": losers_list is not None,
                "stocks_table_body_exists": stocks_table_body is not None,
                "winners_content_length": len(winners_content),
                "losers_content_length": len(losers_content)
            }
        else:
            logger.error(f"Page request failed with status code: {response.status_code}")
            return False, {"error": f"Status code: {response.status_code}"}
    
    except Exception as e:
        logger.error(f"Exception during page test: {e}")
        return False, {"error": str(e)}

def test_full_sequence():
    """Test the full sequence: API request followed by page load"""
    logger.info("Testing full sequence...")
    
    # First, test the API
    api_success, api_data = test_api_endpoint()
    
    # Then, test the page
    page_success, page_data = test_stocks_page()
    
    # Combined result
    success = api_success and page_success
    
    logger.info(f"Full sequence test result: {'SUCCESS' if success else 'FAILURE'}")
    
    return success, {
        "api_test": {
            "success": api_success,
            "data": api_data
        },
        "page_test": {
            "success": page_success,
            "data": page_data
        }
    }

def main():
    """Main function"""
    logger.info("Starting stocks page debug test...")
    
    # Run the full sequence test
    success, data = test_full_sequence()
    
    # Save the results to a file
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    with open(f"stocks_page_debug_{timestamp}.json", "w") as f:
        json.dump(data, f, indent=2, default=str)
    
    logger.info(f"Results saved to stocks_page_debug_{timestamp}.json")
    
    # Return success or failure
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main()) 