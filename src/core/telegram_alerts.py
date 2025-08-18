"""
Telegram Alerts Module

Handles sending trading alerts and notifications via Telegram bot.
Supports multiple chat IDs and configurable alert thresholds.
"""

import requests
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union
from src.core.config import Config
from src.core.logger import trading_logger


class TelegramAlerter:
    """Telegram bot for sending trading alerts and notifications"""
    
    def __init__(self):
        """Initialize the Telegram alerter"""
        self.api_key = Config.TELEGRAM_API_KEY
        self.chat_ids = Config.TELEGRAM_CHAT_IDS.copy()
        self.base_url = f"https://api.telegram.org/bot{self.api_key}"
        self.enabled = Config.TELEGRAM_ALERTS_ENABLED
        self.alert_cooldown = Config.TELEGRAM_ALERT_COOLDOWN
        self.confidence_threshold = Config.TELEGRAM_ALERT_THRESHOLD
        
        # Track last alert time per symbol to prevent spam
        self.last_alerts = {}
        
        # Initialize logger
        self.logger = trading_logger
        
    def is_enabled(self) -> bool:
        """Check if telegram alerts are enabled"""
        return self.enabled and bool(self.api_key) and bool(self.chat_ids)
    
    def test_connection(self) -> Dict:
        """Test Telegram bot connectivity"""
        try:
            if not self.is_enabled():
                return {
                    "working": False,
                    "error": "Telegram not configured or disabled"
                }
            
            # Test bot info
            response = requests.get(f"{self.base_url}/getMe", timeout=10)
            if response.status_code == 200:
                bot_info = response.json()
                if bot_info.get("ok"):
                    return {
                        "working": True,
                        "bot_name": bot_info["result"]["first_name"],
                        "username": bot_info["result"]["username"],
                        "chat_count": len(self.chat_ids),
                        "chat_ids": self.chat_ids
                    }
            
            return {
                "working": False,
                "error": f"Bot API error: {response.status_code}"
            }
            
        except Exception as e:
            self.logger.error_logger.error(f"Telegram connection test failed: {str(e)}")
            return {
                "working": False,
                "error": str(e)
            }
    
    def send_message(
        self, 
        message: str, 
        message_type: str = "general",
        symbol: str = "GENERAL",
        parse_mode: str = "HTML",
        priority: str = "normal"
    ) -> bool:
        """
        Send a message to all configured chat IDs
        
        Args:
            message: The message text to send
            message_type: Type of message (e.g., 'trading_signal', 'alert', 'notification')
            symbol: Trading symbol if applicable
            parse_mode: Telegram parse mode (HTML, Markdown)
            priority: Message priority (high, normal, low)
        
        Returns:
            bool: True if message sent successfully to at least one recipient
        """
        if not self.is_enabled():
            self.logger.error_logger.warning("Telegram alerts disabled, cannot send message")
            return False
        
        if not message or not message.strip():
            self.logger.error_logger.warning("Empty message, cannot send")
            return False
        
        # Check cooldown for trading signals
        if message_type == "trading_signal" and symbol != "GENERAL":
            if not self._can_send_alert(symbol):
                self.logger.app_logger.info(f"Cooldown active for {symbol}, skipping alert")
                return False
        
        success_count = 0
        failed_chats = []
        
        for chat_id in self.chat_ids:
            try:
                payload = {
                    "chat_id": chat_id,
                    "text": message,
                    "parse_mode": parse_mode,
                    "disable_web_page_preview": True
                }
                
                # Add priority indicators for high priority messages
                if priority == "high":
                    payload["text"] = "🚨 " + payload["text"]
                
                response = requests.post(
                    f"{self.base_url}/sendMessage",
                    json=payload,
                    timeout=15
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get("ok"):
                        success_count += 1
                        self.logger.app_logger.info(
                            f"Telegram message sent successfully to {chat_id}"
                        )
                        
                        # Log message details
                        self.logger.log_telegram_message(
                            message_type=message_type,
                            symbol=symbol,
                            recipients=[chat_id],
                            success_count=1,
                            message_preview=message[:50] + "..." if len(message) > 50 else message
                        )
                    else:
                        failed_chats.append(f"{chat_id}: {result.get('description', 'Unknown error')}")
                        self.logger.error_logger.error(
                            f"Telegram API error for {chat_id}: {result.get('description')}"
                        )
                else:
                    failed_chats.append(f"{chat_id}: HTTP {response.status_code}")
                    self.logger.error_logger.error(
                        f"Telegram HTTP error for {chat_id}: {response.status_code}"
                    )
                    
            except Exception as e:
                failed_chats.append(f"{chat_id}: {str(e)}")
                self.logger.error_logger.error(
                    f"Failed to send Telegram message to {chat_id}: {str(e)}"
                )
        
        # Update last alert time for trading signals
        if message_type == "trading_signal" and symbol != "GENERAL" and success_count > 0:
            self._update_last_alert(symbol)
        
        # Log overall result
        if success_count > 0:
            self.logger.app_logger.info(
                f"Telegram message sent to {success_count}/{len(self.chat_ids)} recipients"
            )
            if failed_chats:
                            self.logger.app_logger.warning(
                f"Failed to send to: {', '.join(failed_chats)}"
            )
            return True
        else:
            self.logger.error_logger.error(
                f"Failed to send Telegram message to any recipients: {', '.join(failed_chats)}"
            )
            return False
    
    def send_trading_signal(
        self, 
        symbol: str, 
        action: str, 
        confidence: float, 
        price: float,
        reason: str = "",
        additional_data: Dict = None
    ) -> bool:
        """
        Send a trading signal alert
        
        Args:
            symbol: Trading symbol
            action: BUY, SELL, HOLD
            confidence: Confidence score (0.0 to 1.0)
            price: Current price
            reason: Reason for the signal
            additional_data: Additional trading data
        
        Returns:
            bool: True if alert sent successfully
        """
        if confidence < self.confidence_threshold:
            self.logger.app_logger.info(
                f"Confidence {confidence} below threshold {self.confidence_threshold}, skipping alert"
            )
            return False
        
        # Format the trading signal message
        emoji_map = {
            "BUY": "🟢",
            "SELL": "🔴", 
            "HOLD": "🟡"
        }
        
        emoji = emoji_map.get(action, "📊")
        
        message = f"""
{emoji} <b>TRADING SIGNAL: {symbol}</b>

<b>Action:</b> {action}
<b>Confidence:</b> {confidence:.1%}
<b>Price:</b> ${price:.2f}
<b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        if reason:
            message += f"\n<b>Reason:</b> {reason}"
        
        if additional_data:
            if "sentiment_score" in additional_data:
                sentiment = additional_data["sentiment_score"]
                sentiment_emoji = "😊" if sentiment > 0 else "😞" if sentiment < 0 else "😐"
                message += f"\n<b>Sentiment:</b> {sentiment_emoji} {sentiment:.2f}"
            
            if "volume" in additional_data:
                message += f"\n<b>Volume:</b> {additional_data['volume']:,}"
        
        message += "\n\n<i>This is an automated trading signal. Please do your own research.</i>"
        
        return self.send_message(
            message=message.strip(),
            message_type="trading_signal",
            symbol=symbol,
            priority="high"
        )
    
    def send_system_alert(self, message: str, priority: str = "normal") -> bool:
        """Send a system alert/notification"""
        return self.send_message(
            message=f"🔔 <b>SYSTEM ALERT</b>\n\n{message}",
            message_type="system_alert",
            priority=priority
        )
    
    def send_error_alert(self, error_message: str, context: str = "") -> bool:
        """Send an error alert"""
        message = f"❌ <b>ERROR ALERT</b>\n\n{error_message}"
        if context:
            message += f"\n\n<b>Context:</b> {context}"
        
        return self.send_message(
            message=message,
            message_type="error_alert",
            priority="high"
        )
    
    def send_market_update(self, symbol: str, update_type: str, data: Dict) -> bool:
        """Send a market update"""
        emoji_map = {
            "price_change": "📈",
            "volume_spike": "📊",
            "news_impact": "📰",
            "technical_breakout": "🎯"
        }
        
        emoji = emoji_map.get(update_type, "📊")
        
        message = f"""
{emoji} <b>MARKET UPDATE: {symbol}</b>

<b>Type:</b> {update_type.replace('_', ' ').title()}
<b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        for key, value in data.items():
            if key != "symbol":
                message += f"\n<b>{key.replace('_', ' ').title()}:</b> {value}"
        
        return self.send_message(
            message=message.strip(),
            message_type="market_update",
            symbol=symbol
        )
    
    def _can_send_alert(self, symbol: str) -> bool:
        """Check if enough time has passed to send another alert for a symbol"""
        if symbol not in self.last_alerts:
            return True
        
        last_alert_time = self.last_alerts[symbol]
        time_since_last = datetime.now() - last_alert_time
        
        return time_since_last.total_seconds() >= self.alert_cooldown
    
    def _update_last_alert(self, symbol: str):
        """Update the last alert time for a symbol"""
        self.last_alerts[symbol] = datetime.now()
    
    def add_chat_id(self, chat_id: str) -> bool:
        """Add a new chat ID to the recipients list"""
        if chat_id not in self.chat_ids:
            self.chat_ids.append(chat_id)
            self.logger.app_logger.info(f"Added new Telegram chat ID: {chat_id}")
            return True
        return False
    
    def remove_chat_id(self, chat_id: str) -> bool:
        """Remove a chat ID from the recipients list"""
        if chat_id in self.chat_ids:
            self.chat_ids.remove(chat_id)
            self.logger.app_logger.info(f"Removed Telegram chat ID: {chat_id}")
            return True
        return False
    
    def get_chat_ids(self) -> List[str]:
        """Get current list of chat IDs"""
        return self.chat_ids.copy()
    
    def get_status(self) -> Dict:
        """Get current telegram status"""
        return {
            "enabled": self.is_enabled(),
            "chat_count": len(self.chat_ids),
            "chat_ids": self.chat_ids,
            "api_key_configured": bool(self.api_key),
            "alert_cooldown": self.alert_cooldown,
            "confidence_threshold": self.confidence_threshold
        }


# Create global instance
telegram_alerter = TelegramAlerter()
