import openai
import requests
from typing import List, Dict
import json
from .config import Config
import numpy as np
from datetime import datetime, timedelta
import re # Added for regex fallback

# Import API tracker for monitoring API usage
from src.utils.api_tracker import api_tracker


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

    def _call_ollama_api(self, messages: List[Dict], max_tokens: int = 500) -> Dict:
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
                timeout=60,  # 1 minute timeout for local processing
            )
            if response.status_code != 200:
                raise Exception(f"Ollama API error: {response.status_code} - {response.text}")
            result = response.json()
            
            # Track API usage
            api_tracker.record_request("ollama")
                
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
            # NO FALLBACK - raise the error instead of returning fake data
            raise Exception(f"Price analysis failed for {symbol}: {str(e)}")

    def analyze_news_sentiment(self, news_articles: List[Dict], ai_provider: str = None, symbol: str = None) -> Dict:
        """
        Analyze sentiment of news articles using AI (Ollama, DeepSeek or OpenAI)
        Returns sentiment score between -1 (very negative) and 1 (very positive)
        Args:
            news_articles: List of news articles to analyze
            ai_provider: 'ollama', 'deepseek' or 'openai' - if None, uses preferred provider
            symbol: Stock symbol for context and weighting stock-specific news
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
        
        # Prepare news text for analysis with stock-specific weighting
        stock_specific_news = []
        general_news = []
        
        for article in news_articles[:10]:  # Increased limit to get more articles for better weighting
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
                # Check if this is stock-specific news
                is_stock_specific = self._is_stock_specific_news(headline, summary, symbol)
                
                if is_stock_specific:
                    stock_specific_news.append({
                        "headline": headline,
                        "summary": summary,
                        "weight": 3.0  # Higher weight for stock-specific news
                    })
                else:
                    general_news.append({
                        "headline": headline,
                        "summary": summary,
                        "weight": 1.0  # Lower weight for general news
                    })
        
        # Combine news with weighting
        combined_news = stock_specific_news + general_news
        
        if not combined_news:
            raise Exception("No valid news content found in articles")
        
        # Build weighted news text
        news_text = ""
        total_weight = 0
        
        for article in combined_news:
            weight = article["weight"]
            total_weight += weight
            
            # Repeat stock-specific news more to give it higher weight
            repeat_count = int(weight)
            for _ in range(repeat_count):
                news_text += f"Headline: {article['headline']}\nSummary: {article['summary']}\n\n"
        
        # Limit text length to prevent Ollama timeouts (max 8000 characters)
        max_text_length = 8000
        if len(news_text) > max_text_length:
            print(f"⚠️  Truncating news text from {len(news_text)} to {max_text_length} characters to prevent timeout")
            news_text = news_text[:max_text_length] + "\n\n[Content truncated due to length limits]"
        
        # Determine if this is crypto analysis
        is_crypto = symbol and any(crypto in symbol.upper() for crypto in ["BTC", "ETH", "ADA", "DOT", "SOL", "LINK", "USD"])
        
        # Add context-specific prompt
        if is_crypto:
            # Simplified crypto prompt
            prompt = f"""Analyze crypto news sentiment for {symbol}. Score: -1 (very negative) to 1 (very positive). Confidence: 0-1.

News: {news_text}

Return JSON: {{"sentiment_score": float, "confidence": float, "summary": "string"}}"""
            messages = [
                {
                    "role": "system",
                    "content": f"You are a crypto news sentiment analyzer. Your job is to analyze crypto news content and provide sentiment scores. Focus on news related to {symbol}.",
                },
                {"role": "user", "content": prompt},
            ]
        else:
            # Simplified stock prompt
            prompt = f"""Analyze stock news sentiment for {symbol if symbol else 'stock'}. Score: -1 (very negative) to 1 (very positive). Confidence: 0-1.

News: {news_text}

Return JSON: {{"sentiment_score": float, "confidence": float, "summary": "string"}}"""
            messages = [
                {
                    "role": "system",
                    "content": f"You are a news sentiment analyzer. Your job is to analyze news content and provide sentiment scores. {f'Focus on news related to {symbol}.' if symbol else ''}",
                },
                {"role": "user", "content": prompt},
            ]
        
        # Use only the selected provider - no fallback to mock data
        if selected_provider == "ollama":
            print("🔍 Using Ollama (local) for sentiment analysis...")
            # Log the full Ollama response before any parsing
            ollama_response = self._call_ollama_api(messages)
            content = ollama_response["choices"][0]["message"]["content"]
            print(f"[OLLAMA RAW RESPONSE] symbol={symbol} content=\n{content}\n---END---")
            # Continue with the rest of the logic using 'content' as before
            # (The rest of the function should use 'content' instead of calling _call_ollama_api again)
            print(f"📝 News content being analyzed:")
            print(f"   Stock-specific news: {len(stock_specific_news)} articles")
            print(f"   General news: {len(general_news)} articles")
            print(f"   Total weight: {total_weight}")
            print(f"   News text length: {len(news_text)} characters")
            if len(news_text) < 100:
                print(f"   ⚠️  WARNING: Very short news text: '{news_text}'")
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
                
                # Log the Ollama response for debugging
                print(f"🔍 Ollama response for sentiment analysis:")
                print(f"   Content: {content}")
                print(f"   Content length: {len(content)}")
            except Exception as e:
                print(f"⚠️ Ollama API failed: {str(e)}. Falling back to price-based analysis...")
                # Don't raise exception, let the calling code handle fallback
                raise Exception(f"Ollama API failed: {str(e)}. Please ensure Ollama is running on {self.ollama_base_url}")
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
            # Clean the content - remove any leading/trailing whitespace and normalize newlines
            content = content.strip()
            # Log the full content before parsing
            print(f"[LOG] Full AI response content before parsing: {content}")
            
            # Try direct JSON parsing first
            try:
                result = json.loads(content)
                print(f"✅ Parsed JSON directly: {result}")
                return result
            except json.JSONDecodeError as e:
                print(f"⚠️ Direct JSON parsing failed: {e}")
            
            # Extract JSON substring - find the first { and last }
            start_idx = content.find('{')
            end_idx = content.rfind('}')
            
            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                json_string = content[start_idx:end_idx + 1]
                print(f"[LOG] Extracted JSON string: {json_string}")
                
                try:
                    result = json.loads(json_string)
                    print(f"✅ Parsed JSON from extraction: {result}")
                    return result
                except json.JSONDecodeError as e:
                    print(f"❌ JSON parsing failed for extracted string: {e}")
                    
                    # Check if the JSON is truncated (missing closing brace)
                    if not json_string.endswith('}'):
                        # Try to complete the JSON by adding missing closing brace
                        if '"summary":' in json_string and not json_string.endswith('"}'):
                            # Find the last quote and add closing brace
                            last_quote = json_string.rfind('"')
                            if last_quote != -1:
                                completed_json = json_string[:last_quote + 1] + '}'
                                try:
                                    result = json.loads(completed_json)
                                    print(f"✅ Parsed JSON from completion: {result}")
                                    return result
                                except json.JSONDecodeError:
                                    print(f"❌ JSON completion failed")
                    
                    # Try regex fallback as last resort
                    sentiment_match = re.search(r'"sentiment_score":\s*(-?\d+\.?\d*)', json_string)
                    confidence_match = re.search(r'"confidence":\s*(\d+\.?\d*)', json_string)
                    summary_match = re.search(r'"summary":\s*"([^"]*(?:"[^"]*"[^"]*)*)"', json_string)
                    
                    if sentiment_match and confidence_match:
                        result = {
                            'sentiment_score': float(sentiment_match.group(1)),
                            'confidence': float(confidence_match.group(1)),
                            'summary': summary_match.group(1) if summary_match else "Summary unavailable"
                        }
                        print(f"✅ Parsed JSON from regex fallback: {result}")
                        return result
                    else:
                        print(f"❌ Regex fallback also failed for: {json_string}")
                        # Try to extract any numeric values that might be sentiment scores
                        any_number_match = re.search(r'(-?\d+\.?\d*)', json_string)
                        if any_number_match:
                            try:
                                potential_score = float(any_number_match.group(1))
                                # Clamp to valid range
                                sentiment_score = max(-1.0, min(1.0, potential_score))
                                result = {
                                    'sentiment_score': sentiment_score,
                                    'confidence': 0.3,  # Low confidence since parsing failed
                                    'summary': 'Sentiment analysis completed with fallback parsing'
                                }
                                print(f"✅ Parsed sentiment score from fallback: {result}")
                                return result
                            except ValueError:
                                pass
                        
                        return {
                            'sentiment_score': 0.0,
                            'confidence': 0.0,
                            'summary': 'Sentiment analysis unavailable - parsing failed'
                        }
            else:
                print(f"❌ No JSON brackets found in response: {content}")
                # Check if Ollama returned code instead of JSON
                if "import" in content or "def" in content or "print" in content:
                    print(f"⚠️ Ollama returned code instead of JSON. Using fallback sentiment.")
                    return {
                        'sentiment_score': 0.0,
                        'confidence': 0.1,
                        'summary': 'Sentiment analysis unavailable - AI returned code instead of JSON'
                    }
                else:
                    return {
                        'sentiment_score': 0.0,
                        'confidence': 0.0,
                        'summary': 'Sentiment analysis unavailable - no valid JSON found'
                    }

        except Exception as e:
            # If parsing fails, log the full response and return a fallback neutral sentiment
            print(f"[ERROR] Could not parse AI response: {content[:500]}... Exception: {e}")
            result = {
                "sentiment_score": 0.0,
                "confidence": 0.5,
                "summary": "Sentiment analysis unavailable"
            }
        
        # Ensure result is a dictionary before validation
        if not isinstance(result, dict):
            raise Exception(f"Invalid result format: {type(result)}")
            
        # Validate the response
        sentiment_score = max(-1, min(1, float(result.get("sentiment_score", 0))))
        confidence = max(0, min(1, float(result.get("confidence", 0))))
        
        # Provide fallback for zero confidence cases
        if confidence == 0:
            print(f"⚠️ AI provider {selected_provider} returned zero confidence for {symbol}, using neutral fallback")
            return {
                "sentiment_score": 0.0,
                "confidence": 0.1,  # Minimal confidence for fallback
                "summary": f"Neutral sentiment fallback for {symbol} - insufficient data for confident analysis"
            }
        
        # Add analysis metadata
        analysis_metadata = {
            "stock_specific_count": len(stock_specific_news),
            "general_news_count": len(general_news),
            "total_weight": total_weight,
            "stock_specific_ratio": len(stock_specific_news) / len(combined_news) if combined_news else 0,
            "is_crypto": is_crypto
        }
        
        return {
            "sentiment_score": sentiment_score,
            "confidence": confidence,
            "summary": result.get("summary", "Analysis completed"),
            "provider": provider_used,
            "analysis_metadata": analysis_metadata,
        }

    def _is_stock_specific_news(self, headline: str, summary: str, symbol: str) -> bool:
        """
        Determine if news is specific to the given stock symbol
        Args:
            headline: News headline
            summary: News summary
            symbol: Stock symbol to check for
        Returns:
            True if news is specific to the stock, False if general market news
        """
        if not symbol:
            return False
            
        # Convert to lowercase for case-insensitive matching
        text = (headline + " " + summary).lower()
        symbol_lower = symbol.lower()
        
        # Check for direct symbol mentions
        if symbol_lower in text:
            return True
            
        # Check for symbol in parentheses (common format)
        if f"({symbol_lower})" in text:
            return True
            
        # Check for company name variations
        company_names = {
            "AAPL": ["apple", "iphone", "ipad", "mac", "ios"],
            "MSFT": ["microsoft", "windows", "azure", "office", "xbox"],
            "GOOGL": ["google", "alphabet", "youtube", "android", "chrome"],
            "AMZN": ["amazon", "aws", "alexa", "prime", "bezos"],
            "TSLA": ["tesla", "elon musk", "electric vehicle", "ev", "model"],
            "META": ["meta", "facebook", "instagram", "whatsapp", "zuckerberg"],
            "NVDA": ["nvidia", "gpu", "ai chip", "graphics", "cuda"],
            "NFLX": ["netflix", "streaming", "hastings"],
            "AMD": ["amd", "ryzen", "radeon", "lisa su"],
            "CRM": ["salesforce", "benioff"],
            "UBER": ["uber", "rideshare", "khosrowshahi"],
            "COIN": ["coinbase", "crypto exchange", "armstrong"],
            "PLTR": ["palantir", "karp"],
            "SNOW": ["snowflake", "frank slootman"],
            "ZM": ["zoom", "video conference", "yuan"],
            "ANET": ["arista networks", "arista"],
            "AZO": ["autozone", "auto zone"],
            "ALL": ["allstate", "all state"],
            "ALB": ["albemarle", "lithium"],
            "AES": ["aes corporation", "aes corp"],
        }
        
        # Check for company name mentions
        if symbol in company_names:
            for name in company_names[symbol]:
                if name in text:
                    return True
        
        # Check for general market terms that indicate non-specific news
        general_market_terms = [
            "market", "dow jones", "s&p 500", "nasdaq", "federal reserve", "fed",
            "wall street", "trading", "investors", "bulls", "bears", "rally",
            "selloff", "volatility", "earnings season", "economic data",
            "inflation", "interest rates", "recession", "recovery"
        ]
        
        # If text contains mostly general market terms, it's likely general news
        general_term_count = sum(1 for term in general_market_terms if term in text)
        if general_term_count >= 2:  # If 2+ general terms, likely general news
            return False
            
        return False  # Default to general news if uncertain

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


