import sys
import os
from datetime import datetime, timedelta

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.telegram_alerts import telegram_alerter
from src.core.config import Config

def test_enhanced_analysis_alert():
    # Create a test enhanced analysis result
    test_result = {
        "symbol": "AAPL",
        "price_data": {
            "current_price": 213.45,
            "change_percent": 1.5,
            "volume": 45000000
        },
        "sentiment_data": {
            "sentiment_score": 0.75,
            "reasoning": "Positive sentiment due to strong earnings and new product announcements."
        },
        "news_count": 12,
        "trade_signal": {
            "action": "BUY",
            "confidence": 0.85,
            "reasoning": "Strong buy signal based on technical and sentiment analysis."
        },
        "stock_recommendations": [
            {
                "action": "BUY",
                "recommendation_type": "Momentum",
                "confidence": 0.78,
                "target_price": 230.00,
                "stop_loss_price": 200.00,
                "risk_level": "Medium",
                "time_horizon": "1-3 months"
            },
            {
                "action": "HOLD",
                "recommendation_type": "Value",
                "confidence": 0.65,
                "risk_level": "Low",
                "time_horizon": "3-6 months"
            }
        ],
        "options_recommendations": [
            {
                "action": "CALL",
                "recommendation_type": "Bull Call Spread",
                "confidence": 0.72,
                "strike_price": 215.00,
                "expiry_date": "2025-08-15",
                "target_gain_percent": 15.0,
                "stop_loss_percent": 10.0
            }
        ]
    }

    # Send the test alert
    print("Sending test enhanced analysis alert...")
    success = telegram_alerter.send_enhanced_analysis_alert(test_result)
    
    if success:
        print("✅ Test alert sent successfully!")
    else:
        print("❌ Failed to send test alert")

if __name__ == "__main__":
    test_enhanced_analysis_alert()
