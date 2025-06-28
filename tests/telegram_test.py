#!/usr/bin/env python3
"""
Telegram Test Script
Tests the Telegram alerter functionality and logging
"""

import sys
import os
import time
from datetime import datetime

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.core.telegram_alerts import TelegramAlerts
from src.core.config import Config
from src.core.logger import log_info, log_error, log_system_event

def test_telegram_connection():
    """Test Telegram connection"""
    print("🚀 Testing Telegram Connection...")

    telegram_alerter = TelegramAlerts()
    connection_result = telegram_alerter.test_connection()

    if connection_result.get('working', False):
        print(f"✅ Telegram connection successful")
        print(f"   Bot Name: {connection_result.get('bot_name')}")
        print(f"   Username: {connection_result.get('username')}")
        print(f"   Chat IDs: {len(telegram_alerter.chat_ids)}")
        return True
    else:
        print(f"❌ Telegram connection failed: {connection_result.get('error', 'Unknown error')}")
        return False

def test_send_telegram_message():
    """Test sending a test message via Telegram"""
    print("📱 Testing Telegram Message Sending...")

    telegram_alerter = TelegramAlerts()

    # Check if Telegram alerts are enabled
    if not telegram_alerter.is_enabled():
        print("⚠️ Telegram alerts are disabled in config.py")
        print("   Please set TELEGRAM_ALERTS_ENABLED = True in config.py")
        return False

    # Create a test message
    test_message = f"""
📋 <b>TELEGRAM TEST MESSAGE</b>

This is a test message from the Trading AI application.
It is used to verify that Telegram alerts are working correctly.

⏰ <i>Message sent at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>
    """.strip()

    # Send the message
    success = telegram_alerter.send_message(
        message=test_message,
        message_type="test_message",
        symbol="TEST",
        parse_mode='HTML'
    )

    if success:
        print(f"✅ Test message sent successfully to {len(telegram_alerter.chat_ids)} chat(s)")
        return True
    else:
        print(f"❌ Failed to send test message")
        return False

def test_send_trading_alert():
    """Test sending a trading alert"""
    print("📊 Testing Trading Alert...")

    telegram_alerter = TelegramAlerts()

    # Mock analysis result
    analysis_result = {
        'symbol': 'TSLA',
        'current_price': '950.25',
        'sentiment_score': 0.78,
        'confidence': 0.85,
        'recommendation': 'CALL',
        'reasoning': 'Strong positive sentiment based on recent earnings report and increased production numbers. Technical indicators also show positive momentum with potential for upward price movement.'
    }

    # Force the alert threshold to ensure alert is sent
    old_threshold = Config.TELEGRAM_ALERT_THRESHOLD
    Config.TELEGRAM_ALERT_THRESHOLD = 0.5

    # Send the trading alert
    success = telegram_alerter.send_trading_alert(analysis_result)

    # Restore the original threshold
    Config.TELEGRAM_ALERT_THRESHOLD = old_threshold

    if success:
        print(f"✅ Trading alert sent successfully")
        return True
    else:
        print(f"❌ Failed to send trading alert")
        return False

def test_enhanced_analysis_alert():
    """Test sending an enhanced analysis alert"""
    print("🔍 Testing Enhanced Analysis Alert...")

    telegram_alerter = TelegramAlerts()

    # Mock enhanced analysis result
    enhanced_result = {
        'symbol': 'TSLA',
        'price_data': {
            'current_price': '950.25',
            'open': '945.00',
            'high': '955.75',
            'low': '942.50',
            'volume': 1240000
        },
        'sentiment_data': {
            'sentiment_score': 0.82,
            'confidence': 0.88,
            'sentiment_sources': ['news', 'social_media', 'earnings'],
            'news_count': 12
        },
        'trade_signal': {
            'recommendation': 'CALL',
            'confidence': 0.85,
            'reasoning': 'Strong bullish momentum with positive sentiment'
        },
        'stock_recommendations': [
            {'action': 'BUY', 'timeframe': 'SHORT', 'confidence': 0.9},
            {'action': 'HOLD', 'timeframe': 'MEDIUM', 'confidence': 0.75},
            {'action': 'BUY', 'timeframe': 'LONG', 'confidence': 0.85}
        ],
        'options_recommendations': [
            {'type': 'CALL', 'strike': '980', 'expiry': '1W', 'confidence': 0.8},
            {'type': 'CALL', 'strike': '1000', 'expiry': '1M', 'confidence': 0.75}
        ],
        'news_count': 12
    }

    # Send the enhanced analysis alert
    success = telegram_alerter.send_enhanced_analysis_alert(enhanced_result)

    if success:
        print(f"✅ Enhanced analysis alert sent successfully")
        return True
    else:
        print(f"❌ Failed to send enhanced analysis alert")
        return False

def check_telegram_logs():
    """Check Telegram logs"""
    print("📝 Checking Telegram logs...")

    log_path = os.path.join(project_root, 'logs', 'telegram_alerts.log')
    if not os.path.exists(log_path):
        print(f"❌ Telegram log file not found: {log_path}")
        return False

    # Read the logs
    try:
        with open(log_path, 'r') as f:
            log_lines = f.readlines()
            log_count = len(log_lines)
            print(f"✅ Found {log_count} log entries in telegram_alerts.log")

            # Print the most recent 5 log entries
            print("\n🔍 Most recent log entries:")
            for line in log_lines[-5:]:
                print(f"   {line.strip()}")

            return True
    except Exception as e:
        print(f"❌ Failed to read log file: {e}")
        return False

def run_all_tests():
    """Run all Telegram tests"""
    print("=" * 60)
    print("🚀 TELEGRAM TESTING SUITE")
    print("=" * 60)

    results = {}

    # Test connection
    results['connection'] = test_telegram_connection()
    print("-" * 60)

    # Test message sending
    results['message'] = test_send_telegram_message()
    print("-" * 60)

    # Test trading alert
    results['trading_alert'] = test_send_trading_alert()
    print("-" * 60)

    # Test enhanced analysis alert
    results['enhanced_alert'] = test_enhanced_analysis_alert()
    print("-" * 60)

    # Give some time for logs to be written
    print("⏳ Waiting for logs to be written...")
    time.sleep(2)

    # Check logs
    results['logs'] = check_telegram_logs()
    print("-" * 60)

    # Print summary
    print("\n📊 TEST SUMMARY")
    print("=" * 60)

    for test, result in results.items():
        print(f"{'✅' if result else '❌'} {test.replace('_', ' ').title()}")

    success_rate = sum(1 for r in results.values() if r) / len(results) * 100
    print(f"\n📈 Success Rate: {success_rate:.1f}%")

    # Overall result
    if all(results.values()):
        print("\n✅ All Telegram tests passed!")
        return 0
    else:
        print("\n⚠️ Some Telegram tests failed")
        return 1

if __name__ == '__main__':
    # Initialize logging system
    print("🔍 Setting up logging system...")
    logs_dir = os.path.join(project_root, 'logs')
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)
        print(f"✅ Created logs directory: {logs_dir}")

    # Mark test start in system log
    log_system_event("=== TELEGRAM TEST STARTED ===", "INFO")

    try:
        sys.exit(run_all_tests())
    except KeyboardInterrupt:
        print("\n⚠️ Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error running tests: {e}")
        log_error(f"Error running Telegram tests: {e}", "system")
        sys.exit(1)
    finally:
        # Mark test end in system log
        log_system_event("=== TELEGRAM TEST COMPLETED ===", "INFO")