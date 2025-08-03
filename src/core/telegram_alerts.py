import requests
from datetime import datetime, timedelta
from typing import Dict
from ..core.config import Config
from ..core.logger import log_info, log_error

# Use config for historical data period
HISTORICAL_LOOKBACK_DAYS = Config.HISTORICAL_LOOKBACK_DAYS


class TelegramAlerts:
    def __init__(self):
        self.api_key = Config.TELEGRAM_API_KEY
        self.chat_ids = getattr(Config, "TELEGRAM_CHAT_IDS", [Config.TELEGRAM_CHAT_ID])
        self.base_url = f"https://api.telegram.org/bot{self.api_key}"
        self.last_alerts = {}  # Track last alert time for each symbol

    def is_enabled(self) -> bool:
        """Check if Telegram alerts are enabled"""
        return getattr(Config, "TELEGRAM_ALERTS_ENABLED", False)

    def test_connection(self) -> Dict:
        """Test Telegram bot connection"""
        try:
            response = requests.get(f"{self.base_url}/getMe", timeout=10)
            if response.status_code == 200:
                bot_info = response.json()
                if bot_info.get("ok"):
                    return {
                        "working": True,
                        "bot_name": bot_info["result"].get("first_name", "Unknown"),
                        "username": bot_info["result"].get("username", "Unknown"),
                        "chat_count": len(self.chat_ids),
                    }
            return {"working": False, "error": "Invalid bot token"}
        except Exception as e:
            return {"working": False, "error": str(e)}

    def send_message(
        self,
        message: str,
        message_type: str = "general",
        symbol: str = "",
        parse_mode: str = "HTML",
    ) -> bool:
        """Send a message to all configured Telegram chat IDs"""
        if not self.is_enabled():
            return False
        success_count = 0
        total_chats = len(self.chat_ids)
        successful_recipients = []
        failed_recipients = []
        for chat_id in self.chat_ids:
            try:
                payload = {
                    "chat_id": chat_id,
                    "text": message,
                    "parse_mode": parse_mode,
                    "disable_web_page_preview": True,
                }
                response = requests.post(
                    f"{self.base_url}/sendMessage", json=payload, timeout=10
                )
                if response.status_code == 200:
                    success_count += 1
                    successful_recipients.append(chat_id)
                else:
                    failed_recipients.append(chat_id)
                    log_error(f"Failed to send to chat {chat_id}: {response.text}")
            except Exception as e:
                failed_recipients.append(chat_id)
                log_error(f"Failed to send Telegram message to {chat_id}: {e}")
        # Log the message
        # Just the first line as preview
        message_preview = message.split("\n")[0]
        log_telegram_message(
            f"Message sent to {success_count}/{total_chats} recipients. Preview: {message_preview}"
        )
        # Return True if at least one message was sent successfully
        success = success_count > 0
        if success:
            log_info(
                f"Telegram message sent to {success_count}/{total_chats} recipients"
            )
        return success

    def should_send_alert(self, symbol: str) -> bool:
        """Check if enough time has passed since last alert for this symbol"""
        if symbol not in self.last_alerts:
            return True
        last_alert_time = self.last_alerts[symbol]
        cooldown_period = timedelta(seconds=Config.TELEGRAM_ALERT_COOLDOWN)
        return datetime.now() - last_alert_time > cooldown_period

    def send_trading_alert(self, analysis_result: Dict) -> bool:
        """Send a trading signal alert"""
        if not self.is_enabled():
            return False
        symbol = analysis_result.get("symbol", "Unknown")
        confidence = analysis_result.get("confidence", 0)
        # Check confidence threshold
        if confidence < Config.TELEGRAM_ALERT_THRESHOLD:
            return False
        # Check cooldown
        if not self.should_send_alert(symbol):
            return False
        # Extract data
        analysis_result.get("current_price", "N/A")
        analysis_result.get("sentiment_score", 0)
        analysis_result.get("recommendation", "HOLD")
        analysis_result.get("reasoning", "No reasoning provided")
        # Create alert message
        message = """
🚀 <b>TRADING ALERT</b> 🚀
📊 <b>Symbol:</b> {symbol}
💰 <b>Price:</b> ${current_price}
📈 <b>Recommendation:</b> {recommendation}
🎯 <b>Confidence:</b> {confidence:.1%}
😊 <b>Sentiment:</b> {sentiment_score:+.2f}
💡 <b>Analysis:</b>
{reasoning[:300]}{'...' if len(reasoning) > 300 else ''}
⏰ <i>Alert sent at {datetime.now().strftime('%H:%M:%S')}</i>
        """.strip()
        success = self.send_message(
            message, message_type="trading_alert", symbol=symbol
        )
        if success:
            self.last_alerts[symbol] = datetime.now()
            log_info("Telegram alert sent for {symbol}", "telegram")
        return success

    def send_portfolio_summary(self, portfolio_data: Dict) -> bool:
        """Send daily portfolio summary"""
        if not self.is_enabled():
            return False
        portfolio_data.get("total_value", 0)
        portfolio_data.get("daily_change", 0)
        portfolio_data.get("daily_change_pct", 0)
        positions = portfolio_data.get("positions", [])
        message = """
📊 <b>DAILY PORTFOLIO SUMMARY</b>
💼 <b>Total Value:</b> ${total_value:,.2f}
📈 <b>Daily Change:</b> ${daily_change:+,.2f} ({daily_change_pct:+.2f}%)
<b>Active Positions:</b> {len(positions)}
        """.strip()
        if positions:
            message += "\n\n<b>Top Positions:</b>\n"
            for i, pos in enumerate(positions[:5]):  # Show top 5
                pos.get("symbol", "Unknown")
                pos.get("value", 0)
                pos.get("change_pct", 0)
                message += "🟢 {symbol}: ${value:,.0f} ({change:+.1f}%)\n"
        message += "\n⏰ <i>Summary for {datetime.now().strftime('%Y-%m-%d')}</i>"
        return self.send_message(message)

    def send_news_alert(self, symbol: str, news_data: Dict) -> bool:
        """Send breaking news alert"""
        if not self.is_enabled():
            return False
        if not self.should_send_alert("news_{symbol}"):
            return False
        news_data.get("headline", "Breaking News")
        sentiment = news_data.get("sentiment", 0)
        news_data.get("source", "Unknown")
        "🚨" if abs(sentiment) > 0.5 else "📰"
        message = """
{sentiment_emoji} <b>NEWS ALERT</b>
📊 <b>Symbol:</b> {symbol}
📰 <b>Headline:</b> {headline}
📈 <b>Sentiment Impact:</b> {sentiment:+.2f}
🔗 <b>Source:</b> {source}
⏰ <i>Alert sent at {datetime.now().strftime('%H:%M:%S')}</i>
        """.strip()
        success = self.send_message(message, message_type="news_alert", symbol=symbol)
        if success:
            self.last_alerts["news_{symbol}"] = datetime.now()
        return success

    def send_system_alert(self, alert_type: str, message: str) -> bool:
        """Send system status alerts"""
        if not self.is_enabled():
            return False
        emoji_map = {"error": "🚨", "warning": "⚠️", "info": "ℹ️", "success": "✅"}
        emoji_map.get(alert_type, "ℹ️")
        alert_message = """
{emoji} <b>SYSTEM ALERT</b>
{message}
⏰ <i>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>
        """.strip()
        return self.send_message(alert_message)

    def send_enhanced_analysis_alert(self, enhanced_result: Dict) -> bool:
        """Send enhanced analysis alert with multiple recommendations"""
        if not self.is_enabled():
            return False
        symbol = enhanced_result.get("symbol", "Unknown")
        # Check cooldown
        if not self.should_send_alert("enhanced_{symbol}"):
            return False
        # Extract basic data
        enhanced_result.get("price_data", {}).get("current_price", "N/A")
        enhanced_result.get("sentiment_data", {}).get("sentiment_score", 0)
        # Get top recommendation
        trade_signal = enhanced_result.get("trade_signal", {})
        trade_signal.get("confidence", 0)
        enhanced_result.get("trade_signal", {}).get("action", "HOLD")
        # Get stock recommendations
        stock_recommendations = enhanced_result.get("stock_recommendations", [])
        options_recommendations = enhanced_result.get("options_recommendations", [])
        enhanced_result.get("news_count", 0)
        # Create alert message with proper string formatting
        message = f"""
🚀 <b>ENHANCED ANALYSIS ALERT</b> 🚀
📊 <b>Symbol:</b> {symbol}
💰 <b>Price:</b> ${enhanced_result.get("price_data", {}).get("current_price", "N/A"):.2f}
😊 <b>Sentiment:</b> {enhanced_result.get("sentiment_data", {}).get("sentiment_score", 0):+.2f}
📰 <b>News Articles Analyzed:</b> {enhanced_result.get("news_count", 0)}
📈 <b>Historical Data:</b> {HISTORICAL_LOOKBACK_DAYS // 365}-year analysis included
<b>TOP RECOMMENDATION:</b>
🎯 {trade_signal.get("action", "HOLD")} with {trade_signal.get("confidence", 0):.1%} confidence
<b>STOCK STRATEGIES:</b>
"""
        # Add stock recommendations
        for i, rec in enumerate(stock_recommendations[:3]):  # Show top 3
            rec.get("action", "HOLD")
            rec.get("recommendation_type", "Strategy")
            rec.get("confidence", 0)
            rec.get("risk_level", "")
            rec.get("time_horizon", "")
            # Add target price and stop loss for stock strategies if available
            target_info = ""
            if rec.get("target_price") is not None:
                target_info = f" | Target: ${float(rec.get('target_price', 0)):.2f}"
            if rec.get("stop_loss_price") is not None:
                target_info += f" | Stop: ${float(rec.get('stop_loss_price', 0)):.2f}"
            message += f"🟢 <b>{rec.get('recommendation_type', 'Strategy')}:</b> {rec.get('action', 'HOLD')} ({rec.get('confidence', 0):.1%}){target_info}\n"
        # Add options recommendations if available
        if options_recommendations:
            message += "\n<b>OPTIONS STRATEGIES:</b>\n"
            for i, rec in enumerate(options_recommendations[:3]):  # Show top 3
                rec.get("action", "HOLD")
                rec.get("recommendation_type", "Strategy")
                rec.get("confidence", 0)
                # Add detailed options information if available
                rec.get("days_to_expiry", "")
                rec.get("strike_price", "")
                rec.get("target_gain_percent", "")
                rec.get("stop_loss_percent", "")
                # Add historical stats if available
                hist_stats = rec.get("historical_stats", {})
                hist_stats.get("win_rate", 0)
                message += f"🔵 <b>{rec.get('recommendation_type', 'Options')}:</b> {rec.get('action', 'HOLD')} ({rec.get('confidence', 0):.1%})\n"
        # Add reasoning if available
        reasoning = enhanced_result.get("sentiment_data", {}).get("reasoning", "")
        if reasoning:
            reasoning_preview = reasoning[:250] + (
                "..." if len(reasoning) > 250 else ""
            )
            message += f"\n<b>ANALYSIS SUMMARY:</b>\n{reasoning_preview}\n"
        message += f"\n⏰ <i>Enhanced analysis sent at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>"
        success = self.send_message(
            message, message_type="enhanced_analysis", symbol=symbol
        )
        if success:
            self.last_alerts["enhanced_{symbol}"] = datetime.now()
        return success

    def send_recommendation_alert(self, recommendation_data: Dict) -> bool:
        """Send recommendation alert - compatibility method for tests"""
        return self.send_trading_alert(recommendation_data)


def log_telegram_message(message: str, level: str = "INFO"):
    """Log telegram message with proper logging"""
    if level == "ERROR":
        log_error("Telegram: {message}")
    else:
        log_info("Telegram: {message}")


# Global instance
telegram_alerter = TelegramAlerts()
