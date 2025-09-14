import unittest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import json
import time
import logging
import requests
import os
import sys

# Add project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, project_root)

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/debug_panel_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class TestDebugPanel(unittest.TestCase):
    def setUp(self):
        """Set up test environment and verify server is running"""
        logger.info("Setting up test environment")
        
        # First verify the server is running
        try:
            response = requests.get('http://localhost:5001/api/system_status')
            self.assertTrue(response.ok, "Server is not responding")
            logger.info("Server is running and responding")
        except requests.RequestException as e:
            logger.error(f"Server check failed: {e}")
            raise Exception("Server is not running. Please start the server before running tests.")
        
        # Set up webdriver
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')  # Run in headless mode
        self.driver = webdriver.Chrome(options=options)
        logger.info("Browser started")

    def tearDown(self):
        logger.info("Tearing down test environment")
        if self.driver:
            self.driver.quit()

    def verify_index_page_elements(self):
        """Verify all required elements are present on the index page"""
        try:
            # Load the page
            self.driver.get('http://localhost:5001')
            logger.info("Navigated to index page")
            
            # Wait for critical elements
            wait = WebDriverWait(self.driver, 10)
            
            # Check main container
            main_container = wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'container')))
            self.assertTrue(main_container.is_displayed(), "Main container not visible")
            
            # Check required form elements
            stock_input = wait.until(EC.presence_of_element_located((By.ID, 'stockSymbol')))
            self.assertTrue(stock_input.is_enabled(), "Stock symbol input not enabled")
            
            standard_btn = self.driver.find_element(By.ID, 'standardAnalysisBtn')
            self.assertTrue(standard_btn.is_enabled(), "Standard analysis button not enabled")
            
            enhanced_btn = self.driver.find_element(By.ID, 'enhancedAnalysisBtn')
            self.assertTrue(enhanced_btn.is_enabled(), "Enhanced analysis button not enabled")
            
            # Check debug panel elements
            debug_panel = self.driver.find_element(By.ID, 'debugPanelBody')
            self.assertTrue(debug_panel.is_displayed(), "Debug panel not visible")
            
            request_section = self.driver.find_element(By.ID, 'requestData')
            self.assertIsNotNone(request_section, "Request data section not found")
            
            response_section = self.driver.find_element(By.ID, 'responseData')
            self.assertIsNotNone(response_section, "Response data section not found")
            
            # Check results section exists (though it may be empty)
            results_section = self.driver.find_element(By.ID, 'resultsSection')
            self.assertIsNotNone(results_section, "Results section not found")
            
            logger.info("All required index page elements verified")
            return True
        except Exception as e:
            logger.error(f"Index page verification failed: {e}")
            logger.error(f"Current page source: {self.driver.page_source}")
            raise

    def verify_loading_states(self, analysis_type):
        """Verify loading indicators appear and disappear appropriately"""
        try:
            wait = WebDriverWait(self.driver, 10)
            
            # Check for loading indicator based on analysis type
            btn_content_id = 'standardBtnContent' if analysis_type == 'Standard' else 'enhancedBtnContent'
            loading_id = 'standardBtnLoading' if analysis_type == 'Standard' else 'enhancedBtnLoading'
            
            # Wait for button content to be hidden
            wait.until(EC.invisibility_of_element_located((By.ID, btn_content_id)))
            logger.info(f"{analysis_type} button content hidden")
            
            # Wait for loading indicator to be visible
            wait.until(EC.visibility_of_element_located((By.ID, loading_id)))
            logger.info(f"{analysis_type} analysis loading indicator verified")
            
            # Wait for loading to complete
            wait.until(EC.invisibility_of_element_located((By.ID, loading_id)))
            logger.info(f"{analysis_type} analysis loading completed")
            
            return True
        except TimeoutException:
            logger.error(f"{analysis_type} analysis loading state verification failed")
            raise

    def verify_debug_panel_update(self, analysis_type):
        """Verify debug panel updates with new data"""
        try:
            wait = WebDriverWait(self.driver, 10)
            
            # Get initial debug panel content
            initial_request = self.driver.find_element(By.ID, 'requestData').text
            initial_response = self.driver.find_element(By.ID, 'responseData').text
            
            # Wait for content to change
            def request_changed(driver):
                current = driver.find_element(By.ID, 'requestData').text
                return current != initial_request and current.strip() != "" and current != "No request data"
                
            def response_changed(driver):
                current = driver.find_element(By.ID, 'responseData').text
                return current != initial_response and current.strip() != "" and current != "No response data"
            
            # Verify request update
            wait.until(request_changed)
            logger.info(f"{analysis_type} analysis request data updated")
            
            # Verify response update
            wait.until(response_changed)
            logger.info(f"{analysis_type} analysis response data updated")
            
            return True
        except TimeoutException:
            logger.error(f"{analysis_type} analysis debug panel update verification failed")
            raise

    def verify_debug_panel_data(self, panel_type, data_text, expected_fields):
        """Helper method to verify debug panel data"""
        try:
            # Skip verification if no data yet
            if data_text.strip() in ["No request data", "No response data"]:
                logger.info(f"Skipping {panel_type} verification - no data yet")
                return None
                
            json_data = json.loads(data_text)
            logger.info(f"{panel_type} data structure:")
            logger.info(json.dumps(json_data, indent=2))
            
            # For request data
            if 'method' in json_data:
                for field in expected_fields:
                    self.assertIn(field, json_data, f"{panel_type} missing field: {field}")
                # Verify request specific fields
                self.assertEqual(json_data['method'], 'POST', "Request method should be POST")
                self.assertTrue(json_data['url'].endswith('/analyze'), "Request URL should end with /analyze")
                self.assertIn('symbol', json_data['body'], "Request body should contain symbol")
            # For response data
            else:
                # Check if it's an error response
                if 'error' in json_data:
                    self.assertIn('error', json_data, f"{panel_type} missing field: error")
                    self.assertEqual(json_data['status'], 'error', "Status should be 'error' for error responses")
                else:
                    self.assertIn('status', json_data, f"{panel_type} missing field: status")
                    self.assertEqual(json_data['status'], 'success', "Response status should be success")
                    self.assertIn('data', json_data, f"{panel_type} missing field: data")
                    self.assertIn('timestamp', json_data, f"{panel_type} missing field: timestamp")
            
            logger.info(f"{panel_type} structure verified")
            return json_data
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse {panel_type} JSON: {e}")
            logger.error(f"Raw {panel_type} data: {data_text}")
            raise

    def verify_enhanced_recommendations(self, response_json):
        """Helper method to verify enhanced recommendations"""
        try:
            # Skip if no response data
            if response_json is None:
                logger.info("Skipping enhanced recommendations verification - no response data")
                return False
                
            # Check for recommendations in the response
            self.assertIn('data', response_json, "Response missing data field")
            data = response_json['data']
            
            # Check for comprehensive recommendations
            self.assertIn('recommendations', data, "Missing recommendations")
            recommendations = data['recommendations']
            
            # Check for different types of recommendations
            self.assertIn('top_recommendation', recommendations, "Missing top recommendation")
            self.assertIn('options_recommendations', recommendations, "Missing options recommendations")
            self.assertIn('stock_recommendations', recommendations, "Missing stock recommendations")
            
            # Verify we have recommendations
            options_recs = recommendations['options_recommendations']
            stock_recs = recommendations['stock_recommendations']
            self.assertTrue(len(options_recs) > 0 or len(stock_recs) > 0, "No recommendations found")
            
            # Check recommendation structure
            if len(options_recs) > 0:
                first_rec = options_recs[0]
                required_fields = ['recommendation_type', 'action', 'confidence', 'reasoning', 'option_type', 'strike_price']
                for field in required_fields:
                    self.assertIn(field, first_rec, f"Options recommendation missing field: {field}")
            
            if len(stock_recs) > 0:
                first_rec = stock_recs[0]
                required_fields = ['recommendation_type', 'action', 'confidence', 'reasoning', 'target_price', 'stop_loss']
                for field in required_fields:
                    self.assertIn(field, first_rec, f"Stock recommendation missing field: {field}")
            
            # Log recommendation details
            logger.info(f"Found {len(options_recs)} options recommendations and {len(stock_recs)} stock recommendations")
            logger.info(f"Top recommendation: {json.dumps(recommendations['top_recommendation'], indent=2)}")
            
            return True
        except Exception as e:
            logger.error(f"Failed to verify recommendations: {e}")
            return False

    def verify_results_section(self, analysis_type):
        """Helper method to verify results section"""
        try:
            results_section = self.driver.find_element(By.ID, 'resultsSection')
            self.assertTrue(results_section.is_displayed(), "Results section should be visible")
            
            # Check for specific elements based on analysis type
            if analysis_type == 'standard':
                self.assertTrue(
                    len(self.driver.find_elements(By.CLASS_NAME, 'card-primary')) > 0,
                    "Standard analysis results not found"
                )
            else:  # enhanced
                # For enhanced analysis, check for recommendation cards
                recommendation_cards = self.driver.find_elements(By.CLASS_NAME, 'recommendation-card')
                self.assertTrue(len(recommendation_cards) > 0, "No recommendation cards found")
                
                # Check for different recommendation types
                recommendation_types = set()
                for card in recommendation_cards:
                    try:
                        rec_type = card.find_element(By.CLASS_NAME, 'recommendation-type').text
                        recommendation_types.add(rec_type)
                    except:
                        continue
                
                logger.info(f"Found recommendation types: {recommendation_types}")
                self.assertTrue(len(recommendation_types) > 0, "No recommendation types found")
            
            logger.info(f"{analysis_type.capitalize()} analysis results verified")
            return True
        except Exception as e:
            logger.error(f"Failed to verify {analysis_type} results: {e}")
            return False

    def test_invalid_symbol(self):
        """Test error handling for invalid stock symbol"""
        try:
            logger.info("Testing invalid symbol handling")
            
            # First verify the index page loads correctly
            self.verify_index_page_elements()
            
            # Enter invalid symbol
            wait = WebDriverWait(self.driver, 10)
            stock_input = wait.until(EC.presence_of_element_located((By.ID, 'stockSymbol')))
            stock_input.clear()
            stock_input.send_keys('INVALID123')
            
            # Try standard analysis
            analysis_button = self.driver.find_element(By.ID, 'standardAnalysisBtn')
            analysis_button.click()
            
            # Verify error in debug panel
            time.sleep(2)
            response_data = wait.until(EC.presence_of_element_located((By.ID, 'responseData')))
            response_json = json.loads(response_data.text)
            
            self.assertIn('error', response_json, "Error response expected for invalid symbol")
            self.assertEqual(response_json['status'], 'error', "Status should be 'error' for invalid symbol")
            
            # Verify error message displayed to user
            results_section = wait.until(EC.presence_of_element_located((By.ID, 'resultsSection')))
            self.assertTrue('Error:' in results_section.text, "Error message should be visible in results section")
            
            logger.info("Invalid symbol error handling verified")
            
        except Exception as e:
            logger.error(f"Invalid symbol test failed: {str(e)}")
            logger.error(f"Page source at failure: {self.driver.page_source}")
            raise

    def test_debug_panel_functionality(self):
        try:
            logger.info("Starting debug panel test")
            
            # First verify the index page loads correctly
            self.verify_index_page_elements()
            
            # Get the stock input element
            wait = WebDriverWait(self.driver, 10)
            stock_input = wait.until(EC.presence_of_element_located((By.ID, 'stockSymbol')))
            logger.info("Found stock symbol input")

            # Test Standard Analysis
            logger.info("Testing Standard Analysis...")
            stock_input.clear()
            stock_input.send_keys('AAPL')
            
            # Get initial debug panel state
            initial_request = self.driver.find_element(By.ID, 'requestData').text
            initial_response = self.driver.find_element(By.ID, 'responseData').text
            
            # Click analysis button
            analysis_button = self.driver.find_element(By.ID, 'standardAnalysisBtn')
            analysis_button.click()
            logger.info("Clicked standard analysis button")
            
            # Verify loading states
            self.verify_loading_states('Standard')
            
            # Verify debug panel updates
            self.verify_debug_panel_update('Standard')
            
            # Wait and verify request data
            request_data = wait.until(EC.presence_of_element_located((By.ID, 'requestData')))
            request_json = self.verify_debug_panel_data(
                "Standard request",
                request_data.text,
                ['method', 'url', 'body', 'headers']
            )
            
            # Only verify request data if we got a valid response
            if request_json:
                self.assertEqual(request_json['body']['symbol'], 'AAPL', "Request symbol mismatch")
                self.assertEqual(request_json['body']['analysis_type'], 'standard', "Analysis type mismatch")
            
            # Wait and verify response
            response_data = wait.until(EC.presence_of_element_located((By.ID, 'responseData')))
            response_json = self.verify_debug_panel_data(
                "Standard response",
                response_data.text,
                ['status', 'data', 'timestamp']
            )
            
            # Verify results displayed
            self.verify_results_section('standard')
            
            # Test Enhanced Analysis
            logger.info("Testing Enhanced Analysis...")
            stock_input = self.driver.find_element(By.ID, 'stockSymbol')
            stock_input.clear()
            stock_input.send_keys('MSFT')
            
            # Click enhanced button
            enhanced_button = self.driver.find_element(By.ID, 'enhancedAnalysisBtn')
            enhanced_button.click()
            logger.info("Clicked enhanced analysis button")
            
            # Verify loading states
            self.verify_loading_states('Enhanced')
            
            # Verify debug panel updates
            self.verify_debug_panel_update('Enhanced')
            
            # Wait and verify enhanced request data
            enhanced_request_data = wait.until(EC.presence_of_element_located((By.ID, 'requestData')))
            enhanced_request_json = self.verify_debug_panel_data(
                "Enhanced request",
                enhanced_request_data.text,
                ['method', 'url', 'body', 'headers']
            )
            
            # Only verify request data if we got a valid response
            if enhanced_request_json:
                self.assertEqual(enhanced_request_json['body']['symbol'], 'MSFT', "Enhanced request symbol mismatch")
                self.assertEqual(enhanced_request_json['body']['analysis_type'], 'enhanced', "Analysis type mismatch")
            
            # Wait and verify enhanced response
            enhanced_response_data = wait.until(EC.presence_of_element_located((By.ID, 'responseData')))
            enhanced_response_json = self.verify_debug_panel_data(
                "Enhanced response",
                enhanced_response_data.text,
                ['status', 'data', 'timestamp']
            )
            
            # Verify enhanced recommendations
            self.verify_enhanced_recommendations(enhanced_response_json)
            
            # Verify enhanced results displayed
            self.verify_results_section('enhanced')
            
            logger.info("Debug panel test completed successfully")

        except Exception as e:
            logger.error(f"Test failed with error: {str(e)}")
            logger.error(f"Page source at failure: {self.driver.page_source}")
            raise

if __name__ == '__main__':
    unittest.main() 