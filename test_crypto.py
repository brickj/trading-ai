#!/usr/bin/env python3
"""
Test script to run crypto analysis manually
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core.batch_processor import create_crypto_analysis_tasks, batch_processor_instance

def test_crypto_analysis():
    print("Testing crypto analysis...")
    
    # Test crypto symbols
    crypto_symbols = ['BTC', 'ETH', 'SOL']
    print(f"Crypto symbols: {crypto_symbols}")
    
    # Create crypto analysis tasks
    try:
        crypto_tasks = create_crypto_analysis_tasks(crypto_symbols)
        print(f"Created {len(crypto_tasks)} crypto analysis tasks")
        
        # Process the batch
        crypto_batch_result = batch_processor_instance.process_batch_sync(crypto_tasks, progress_callback=None)
        print(f"Batch result: {crypto_batch_result}")
        
        # Extract results
        crypto_opportunities = [
            result
            for result in crypto_batch_result["results"].values()
            if result and "error" not in result
        ]
        crypto_errors = [
            result
            for result in crypto_batch_result["results"].values()
            if result and "error" in result
        ]
        
        print(f"Crypto opportunities: {len(crypto_opportunities)}")
        print(f"Crypto errors: {len(crypto_errors)}")
        
        if crypto_opportunities:
            print(f"Sample opportunity: {crypto_opportunities[0]}")
        
        if crypto_errors:
            print(f"Sample error: {crypto_errors[0]}")
            
    except Exception as e:
        print(f"Error in crypto analysis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_crypto_analysis()
