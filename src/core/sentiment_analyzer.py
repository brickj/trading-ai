import openai
import requests
from typing import List, Dict
import json
from .config import Config
import numpy as np
from datetime import datetime, timedelta


class SentimentAnalyzer:
    def __init__(self):
        # OpenAI setup
        openai.api_key = Config.OPENAI_API_KEY
        try:
            self.openai_client = openai.OpenAI(api_key=Config.OPENAI_API_KEY)
            self.use_new_openai_api = True
        except AttributeError:
            self.openai_client = None
            self.use_new_openai_api = False
        # DeepSeek setup
        self.deepseek_api_key = getattr(Config, "DEEPSEEK_API_KEY", None)
        self.deepseek_base_url = "https://api.deepseek.com/v1"
        # Ollama setup
        self.ollama_base_url = getattr(Config, "OLLAMA_BASE_URL", "http://localhost:11434")
        self.ollama_model = getattr(Config, "OLLAMA_MODEL", "qwen2.5:3b")
        # Default AI provider preference (no fallback - use only selected
        # provider)
        self.preferred_provider = getattr(Config, "PREFERRED_AI_PROVIDER", "ollama")

    def _call_ollama_api(self, messages: List[Dict], max_tokens: int = 200) -> Dict:
        """
        Call Ollama local API for sentiment analysis
        """
        # Convert messages to a single prompt for Ollama
        prompt = ""
        for message in messages:
            if message["role"] == "system":
                prompt += f"System: {message['content']}\n\n"
            elif message["role"] == "user":
                prompt += f"User: {message['content']}\n\n"
        payload = {
            "model": self.ollama_model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.1, "num_predict": max_tokens},
        }
        try:
            response = requests.post(
                f"{self.ollama_base_url}/api/generate",
                json=payload,
                timeout=60,  # Longer timeout for local processing
            )
            if response.status_code != 200:
                raise Exception(f"Ollama API error: {response.status_code} - {response.text}")
            result = response.json()
            # Return in the expected format for the sentiment analyzer
            return {
                "choices": [{
                    "message": {
                        "content": result.get("response", "")
                    }
                }]
            }
        except requests.exceptions.ConnectionError:
            raise Exception("Ollama service not running. Start with: brew services start ollama")
        except Exception as e:
            raise Exception(f"Ollama API error: {str(e)}")

    def _call_deepseek_api(self, messages: List[Dict], max_tokens: int = 200) -> Dict:
        """
        Call DeepSeek API for sentiment analysis
        """
        if not self.deepseek_api_key:
            raise Exception("DeepSeek API key not configured")
        headers = {
            "Authorization": "Bearer {self.deepseek_api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": "deepseek-chat",
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": 0.1,
        }
        response = requests.post(
            "{self.deepseek_base_url}/chat/completions",
            headers=headers,
            json=payload,
            timeout=30,
        )
        if response.status_code != 200:
            raise Exception("DeepSeek API error: {response.status_code} - {response.text}")
        return response.json()

    def _call_openai_api(self, messages: List[Dict], max_tokens: int = 200) -> Dict:
        """
        Call OpenAI API for sentiment analysis
        """
        if self.use_new_openai_api:
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=max_tokens,
                temperature=0.1,
            )
        else:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=max_tokens,
                temperature=0.1,
            )
        return response

    def analyze_price_based_sentiment(self, price_data: Dict, symbol: str) -> Dict:
        """
        Analyze sentiment based on price data and technical indicators when news articles are not available.
        This provides a sentiment score based on price movements, trends, and technical analysis.
        
        Args:
            price_data: Dictionary containing price information
            symbol: Stock symbol for context
            
        Returns:
            Dict: Sentiment analysis result with score, confidence, and reasoning
        """
        try:
            # Extract price information
            current_price = float(price_data.get('current_price', 0))
            previous_close = float(price_data.get('previous_close', current_price))
            volume = float(price_data.get('volume', 0))
            
            # Calculate basic price metrics
            price_change = current_price - previous_close
            price_change_percent = (price_change / previous_close * 100) if previous_close > 0 else 0
            
            # Get historical data for trend analysis
            historical_prices = price_data.get('historical_prices', [])
            
            # Calculate technical indicators
            sentiment_score = 0.0
            confidence = 0.5  # Base confidence for price-based analysis
            reasoning_parts = []
            
            # 1. Price momentum (short-term)
            if price_change_percent > 2.0:
                sentiment_score += 0.3
                reasoning_parts.append(f"Strong positive momentum (+{price_change_percent:.1f}%)")
            elif price_change_percent > 0.5:
                sentiment_score += 0.1
                reasoning_parts.append(f"Moderate positive momentum (+{price_change_percent:.1f}%)")
            elif price_change_percent < -2.0:
                sentiment_score -= 0.3
                reasoning_parts.append(f"Strong negative momentum ({price_change_percent:.1f}%)")
            elif price_change_percent < -0.5:
                sentiment_score -= 0.1
                reasoning_parts.append(f"Moderate negative momentum ({price_change_percent:.1f}%)")
            else:
                reasoning_parts.append(f"Neutral price movement ({price_change_percent:.1f}%)")
            
            # 2. Volume analysis
            avg_volume = price_data.get('average_volume', volume)
            if avg_volume > 0:
                volume_ratio = volume / avg_volume
                if volume_ratio > 1.5:
                    confidence += 0.1
                    reasoning_parts.append("High volume indicates strong interest")
                elif volume_ratio < 0.5:
                    confidence -= 0.1
                    reasoning_parts.append("Low volume suggests weak conviction")
            
            # 3. Trend analysis using historical data
            if len(historical_prices) >= 20:
                recent_prices = historical_prices[-20:]  # Last 20 days
                if len(recent_prices) >= 10:
                    # Calculate moving averages
                    ma_5 = np.mean(recent_prices[-5:])
                    ma_10 = np.mean(recent_prices[-10:])
                    ma_20 = np.mean(recent_prices[-20:])
                    
                    # Trend analysis
                    if current_price > ma_5 > ma_10 > ma_20:
                        sentiment_score += 0.2
                        reasoning_parts.append("Strong uptrend across all timeframes")
                    elif current_price > ma_5 > ma_10:
                        sentiment_score += 0.1
                        reasoning_parts.append("Short-term uptrend")
                    elif current_price < ma_5 < ma_10 < ma_20:
                        sentiment_score -= 0.2
                        reasoning_parts.append("Strong downtrend across all timeframes")
                    elif current_price < ma_5 < ma_10:
                        sentiment_score -= 0.1
                        reasoning_parts.append("Short-term downtrend")
                    else:
                        reasoning_parts.append("Mixed trend signals")
                    
                    # Volatility analysis
                    price_std = np.std(recent_prices)
                    price_mean = np.mean(recent_prices)
                    volatility = (price_std / price_mean * 100) if price_mean > 0 else 0
                    
                    if volatility > 5.0:
                        confidence -= 0.1
                        reasoning_parts.append(f"High volatility ({volatility:.1f}%) reduces confidence")
                    elif volatility < 2.0:
                        confidence += 0.1
                        reasoning_parts.append(f"Low volatility ({volatility:.1f}%) increases confidence")
            
            # 4. Support/Resistance analysis
            if len(historical_prices) >= 50:
                recent_high = max(historical_prices[-50:])
                recent_low = min(historical_prices[-50:])
                
                # Distance from recent high/low
                distance_from_high = (recent_high - current_price) / recent_high * 100
                distance_from_low = (current_price - recent_low) / recent_low * 100
                
                if distance_from_high < 5.0:
                    sentiment_score -= 0.1
                    reasoning_parts.append("Near recent high - potential resistance")
                elif distance_from_low < 5.0:
                    sentiment_score += 0.1
                    reasoning_parts.append("Near recent low - potential support")
            
            # 5. Relative strength (if market data available)
            market_change = price_data.get('market_change_percent', 0)
            if market_change != 0:
                relative_strength = price_change_percent - market_change
                if relative_strength > 1.0:
                    sentiment_score += 0.1
                    reasoning_parts.append(f"Outperforming market by {relative_strength:.1f}%")
                elif relative_strength < -1.0:
                    sentiment_score -= 0.1
                    reasoning_parts.append(f"Underperforming market by {abs(relative_strength):.1f}%")
            
            # Normalize sentiment score to [-1, 1] range
            sentiment_score = max(-1.0, min(1.0, sentiment_score))
            
            # Normalize confidence to [0.3, 0.9] range
            confidence = max(0.3, min(0.9, confidence))
            
            # Generate summary
            if sentiment_score > 0.2:
                summary = f"Bullish technical signals for {symbol}"
            elif sentiment_score < -0.2:
                summary = f"Bearish technical signals for {symbol}"
            else:
                summary = f"Neutral technical signals for {symbol}"
            
            return {
                "sentiment_score": sentiment_score,
                "confidence": confidence,
                "summary": summary,
                "reasoning": "; ".join(reasoning_parts),
                "provider": "price_analysis",
                "analysis_type": "technical"
            }
            
        except Exception as e:
            # Fallback to neutral sentiment if analysis fails
            return {
                "sentiment_score": 0.0,
                "confidence": 0.3,
                "summary": f"Price analysis failed for {symbol}",
                "reasoning": f"Technical analysis error: {str(e)}",
                "provider": "price_analysis",
                "analysis_type": "fallback"
            }

    def analyze_news_sentiment(self, news_articles: List[Dict], ai_provider: str = None) -> Dict:
        """
        Analyze sentiment of news articles using AI (Ollama, DeepSeek or OpenAI)
        Returns sentiment score between -1 (very negative) and 1 (very positive)
        Args:
            news_articles: List of news articles to analyze
            ai_provider: 'ollama', 'deepseek' or 'openai' - if None, uses preferred provider
        """
        if not news_articles:
            raise Exception("No news articles provided for analysis")
        # Use provided ai_provider or fall back to preferred provider
        if ai_provider:
            selected_provider = ai_provider.lower()
        else:
            selected_provider = self.preferred_provider
        # Reject mock provider completely
        if selected_provider == "mock":
            raise Exception(
                "Mock data provider is disabled for safety. Configure a real AI provider (ollama, deepseek, or openai)"
            )
        # Prepare news text for analysis
        news_text = ""
        for article in news_articles[:5]:  # Limit to 5 most recent articles
            # Handle different news formats (dict vs other types)
            if isinstance(article, dict):
                headline = article.get("headline", article.get("title", ""))
                summary = article.get(
                    "summary", article.get("description", article.get("selftext", ""))
                )
            else:
                # If article is not a dict, skip it
                print(f"Warning: Skipping non-dict article: {type(article)}")
                continue
            if headline or summary:
                news_text += f"Headline: {headline}\nSummary: {summary}\n\n"
        if not news_text.strip():
            raise Exception("No valid news content found in articles")
        prompt = f"""
        Analyze the sentiment of the following financial news articles and provide:
        1. A sentiment score between -1 (very negative) and 1 (very positive)
        2. A confidence level between 0 and 1
        3. A brief summary of the overall sentiment
        
        News articles:
        {news_text}
        
        IMPORTANT: Respond with ONLY this exact JSON format, no additional text or explanation:
        {{
            "sentiment_score": 0.0,
            "confidence": 0.0,
            "summary": "your analysis here"
        }}
        """
        messages = [
            {
                "role": "system",
                "content": "You are a financial sentiment analysis expert. Analyze news sentiment for trading decisions.",
            },
            {"role": "user", "content": prompt},
        ]
        # Use only the selected provider - no fallback to mock data
        if selected_provider == "ollama":
            print("🔍 Using Ollama (local) for sentiment analysis...")
            try:
                response = self._call_ollama_api(messages)
                # Validate response structure
                if not isinstance(response, dict) or "choices" not in response:
                    raise Exception("Invalid response structure from Ollama")
                if not response["choices"] or not isinstance(response["choices"], list):
                    raise Exception("No choices in Ollama response")
                if not response["choices"][0] or "message" not in response["choices"][0]:
                    raise Exception("Invalid choice structure in Ollama response")
                if not response["choices"][0]["message"] or "content" not in response["choices"][0]["message"]:
                    raise Exception("No content in Ollama response message")
                content = response["choices"][0]["message"]["content"]
                provider_used = "ollama"
            except Exception as e:
                raise Exception(
                    f"Ollama API failed: {str(e)}. Please ensure Ollama is running on {self.ollama_base_url}"
                )
        elif selected_provider == "deepseek":
            if (
                not self.deepseek_api_key
                or self.deepseek_api_key == "your_free_deepseek_api_key_here"
            ):
                raise Exception(
                    "DeepSeek API key not configured. Please set DEEPSEEK_API_KEY in config.py"
                )
            print("🔍 Using DeepSeek for sentiment analysis...")
            try:
                response = self._call_deepseek_api(messages)
                # Validate response structure
                if not isinstance(response, dict) or "choices" not in response:
                    raise Exception("Invalid response structure from DeepSeek")
                if not response["choices"] or not isinstance(response["choices"], list):
                    raise Exception("No choices in DeepSeek response")
                if not response["choices"][0] or "message" not in response["choices"][0]:
                    raise Exception("Invalid choice structure in DeepSeek response")
                if not response["choices"][0]["message"] or "content" not in response["choices"][0]["message"]:
                    raise Exception("No content in DeepSeek response message")
                content = response["choices"][0]["message"]["content"]
                provider_used = "deepseek"
            except Exception as e:
                raise Exception(f"DeepSeek API failed: {str(e)}. Check your API key and credits")
        elif selected_provider == "openai":
            if not Config.OPENAI_API_KEY or Config.OPENAI_API_KEY == "your_openai_api_key_here":
                raise Exception(
                    "OpenAI API key not configured. Please set OPENAI_API_KEY in config.py"
                )
            print("🔍 Using OpenAI for sentiment analysis...")
            try:
                response = self._call_openai_api(messages)
                # Validate response structure for OpenAI
                if not hasattr(response, 'choices') or not response.choices:
                    raise Exception("No choices in OpenAI response")
                if not response.choices[0] or not hasattr(response.choices[0], 'message'):
                    raise Exception("Invalid choice structure in OpenAI response")
                if not response.choices[0].message or not hasattr(response.choices[0].message, 'content'):
                    raise Exception("No content in OpenAI response message")
                content = response.choices[0].message.content
                provider_used = "openai"
            except Exception as e:
                raise Exception(f"OpenAI API failed: {str(e)}. Check your API key and quota")
        else:
            raise Exception(
                f"Unknown AI provider: {selected_provider}. Supported providers: ollama, deepseek, openai"
            )
        # Parse the JSON response
        try:
            # First, ensure content is a string
            if not isinstance(content, str):
                raise Exception(f"AI response content is not a string: {type(content)}")
            
            # Try to parse as JSON
            result = json.loads(content)
            
            # Ensure result is a dictionary
            if not isinstance(result, dict):
                raise json.JSONDecodeError("Result is not a dictionary", content, 0)
                
            # Handle nested format from Ollama
            if isinstance(result.get("sentiment_score"), dict):
                # Extract from nested format
                sentiment_dict = result.get("sentiment_score", {})
                if "positive" in sentiment_dict:
                    result["sentiment_score"] = sentiment_dict["positive"] - sentiment_dict.get("negative", 0)
                    
        except json.JSONDecodeError:
            # If JSON parsing fails, try to extract values from text
            import re

            sentiment_match = re.search(r'"positive":\s*(\d+\.?\d*)', content)
            confidence_match = re.search(r'"high":\s*(\d+\.?\d*)', content)
            summary_match = re.search(r'"summary":\s*"([^"]*)"', content)
            
            # Also try simple format
            if not sentiment_match:
                sentiment_match = re.search(r'"sentiment_score":\s*(-?\d+\.?\d*)', content)
            if not confidence_match:
                confidence_match = re.search(r'"confidence":\s*(\d+\.?\d*)', content)
                
            if sentiment_match and confidence_match:
                result = {
                    "sentiment_score": float(sentiment_match.group(1)),
                    "confidence": float(confidence_match.group(1)),
                    "summary": (summary_match.group(1) if summary_match else "Analysis completed"),
                }
            else:
                # If parsing fails completely, raise an exception instead of using fallback values
                raise Exception(f"Could not parse AI response: {content[:200]}...")
                
        # Ensure result is a dictionary before validation
        if not isinstance(result, dict):
            raise Exception(f"Invalid result format: {type(result)}")
            
        # Validate the response
        sentiment_score = max(-1, min(1, float(result.get("sentiment_score", 0))))
        confidence = max(0, min(1, float(result.get("confidence", 0))))
        if confidence == 0:
            raise Exception(
                f"AI provider {selected_provider} returned zero confidence. This indicates a problem with the analysis."
            )
        return {
            "sentiment_score": sentiment_score,
            "confidence": confidence,
            "summary": result.get("summary", "Analysis completed"),
            "provider": provider_used,
        }

    def get_trading_signal(self, sentiment_data: Dict) -> Dict:
        """
        Convert sentiment analysis to trading signal
        """
        # Ensure sentiment_data is a dictionary
        if not isinstance(sentiment_data, dict):
            raise TypeError(f"sentiment_data must be a dict, got {type(sentiment_data)}: {sentiment_data}")
        
        # Extract values safely
        sentiment_score = sentiment_data.get("sentiment_score", 0)
        confidence = sentiment_data.get("confidence", 0)
        
        # Validate values are numeric
        try:
            sentiment_score = float(sentiment_score)
            confidence = float(confidence)
        except (ValueError, TypeError):
            raise ValueError(f"Invalid sentiment data format - score: {sentiment_score}, confidence: {confidence}")
        
        # Only trade if confidence is above threshold and sentiment is strong enough
        if confidence < Config.CONFIDENCE_THRESHOLD or abs(sentiment_score) < Config.SENTIMENT_THRESHOLD:
            return {
                "action": "HOLD",
                "signal_strength": 0,
                "confidence": confidence,
                "reasoning": "Low confidence or weak sentiment signal",
            }
        if sentiment_score > Config.SENTIMENT_THRESHOLD:
            return {
                "action": "CALL",
                "signal_strength": sentiment_score * confidence,
                "confidence": confidence,
                "reasoning": f"Positive sentiment ({sentiment_score:.2f}) with high confidence ({confidence:.2f})",
            }
        elif sentiment_score < -Config.SENTIMENT_THRESHOLD:
            return {
                "action": "PUT",
                "signal_strength": abs(sentiment_score) * confidence,
                "confidence": confidence,
                "reasoning": f"Negative sentiment ({sentiment_score:.2f}) with high confidence ({confidence:.2f})",
            }
        else:
            return {
                "action": "HOLD",
                "signal_strength": 0,
                "confidence": confidence,
                "reasoning": "Neutral sentiment",
            }


