#!/usr/bin/env python3
"""
Unit tests for sentiment analyzer functionality.
Tests the SentimentAnalyzer class and AI provider integration.
"""

import unittest
import sys
import os
from unittest.mock import Mock, patch, MagicMock

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from core.sentiment_analyzer import SentimentAnalyzer
from core.config import Config


class SentimentAnalyzerTest(unittest.TestCase):
    """Unit tests for SentimentAnalyzer class."""

    def setUp(self):
        """Set up test environment."""
        self.analyzer = SentimentAnalyzer()

        # Mock news data for testing
        self.mock_news = [
            {
                "headline": "Company reports strong quarterly earnings",
                "summary": "The company exceeded expectations with record profits",
                "datetime": 1640995200,  # 2022-01-01
                "source": "Financial News"
            },
            {
                "headline": "Stock price drops amid market concerns",
                "summary": "Investors are worried about economic uncertainty",
                "datetime": 1640995200,
                "source": "Market Watch"
            }
        ]

    def test_initialization(self):
        """Test SentimentAnalyzer initialization."""
        self.assertIsInstance(self.analyzer, SentimentAnalyzer)
        self.assertIsNotNone(self.analyzer.preferred_provider)
        self.assertIsNotNone(self.analyzer.ollama_base_url)
        self.assertIsNotNone(self.analyzer.ollama_model)

    def test_get_trading_signal_positive_sentiment(self):
        """Test trading signal generation for positive sentiment."""
        sentiment_data = {
            "sentiment_score": 0.8,
            "confidence": 0.9,
            "summary": "Very positive news"
        }

        signal = self.analyzer.get_trading_signal(sentiment_data)

        self.assertIsInstance(signal, dict)
        self.assertIn("action", signal)
        self.assertIn("signal_strength", signal)
        self.assertIn("reasoning", signal)

        # Positive sentiment should suggest CALL
        self.assertEqual(signal["action"], "CALL")
        self.assertGreater(signal["signal_strength"], 0.5)

    def test_get_trading_signal_negative_sentiment(self):
        """Test trading signal generation for negative sentiment."""
        sentiment_data = {
            "sentiment_score": -0.8,
            "confidence": 0.9,
            "summary": "Very negative news"
        }

        signal = self.analyzer.get_trading_signal(sentiment_data)

        self.assertIsInstance(signal, dict)
        self.assertIn("action", signal)
        self.assertIn("signal_strength", signal)
        self.assertIn("reasoning", signal)

        # Negative sentiment should suggest PUT
        self.assertEqual(signal["action"], "PUT")
        self.assertGreater(signal["signal_strength"], 0.5)

    def test_get_trading_signal_neutral_sentiment(self):
        """Test trading signal generation for neutral sentiment."""
        sentiment_data = {
            "sentiment_score": 0.05,
            "confidence": 0.6,
            "summary": "Mixed signals in the news"
        }

        signal = self.analyzer.get_trading_signal(sentiment_data)

        self.assertIsInstance(signal, dict)
        self.assertIn("action", signal)
        self.assertIn("signal_strength", signal)

        # Neutral sentiment should suggest HOLD
        self.assertEqual(signal["action"], "HOLD")
        self.assertEqual(signal["signal_strength"], 0)

    def test_get_trading_signal_low_confidence(self):
        """Test trading signal generation with low confidence."""
        sentiment_data = {
            "sentiment_score": 0.8,
            "confidence": 0.3,  # Low confidence
            "summary": "Limited news data"
        }

        signal = self.analyzer.get_trading_signal(sentiment_data)

        # Low confidence should result in HOLD
        self.assertEqual(signal["action"], "HOLD")
        self.assertEqual(signal["signal_strength"], 0)

    def test_get_mock_sentiment_data(self):
        """Test mock sentiment data generation."""
        mock_data = self.analyzer._get_mock_sentiment()

        self.assertIsInstance(mock_data, dict)
        self.assertIn("sentiment_score", mock_data)
        self.assertIn("confidence", mock_data)
        self.assertIn("summary", mock_data)
        self.assertIn("provider", mock_data)

        # Verify data types and ranges
        self.assertIsInstance(mock_data["sentiment_score"], (int, float))
        self.assertIsInstance(mock_data["confidence"], (int, float))
        self.assertIsInstance(mock_data["summary"], str)
        self.assertEqual(mock_data["provider"], "mock_data")

        # Verify ranges
        self.assertGreaterEqual(mock_data["sentiment_score"], -1.0)
        self.assertLessEqual(mock_data["sentiment_score"], 1.0)
        self.assertGreaterEqual(mock_data["confidence"], 0.0)
        self.assertLessEqual(mock_data["confidence"], 1.0)

    @patch('requests.post')
    def test_ollama_api_call_success(self, mock_post):
        """Test successful Ollama API call."""
        # Mock successful Ollama response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": '{"sentiment_score": 0.8, "confidence": 0.9, "summary": "Positive sentiment"}'
        }
        mock_post.return_value = mock_response

        messages = [{"role": "user", "content": "Test message"}]
        result = self.analyzer._call_ollama_api(messages)

        self.assertIsInstance(result, dict)
        self.assertIn("choices", result)
        self.assertIn("message", result["choices"][0])

    @patch('requests.post')
    def test_ollama_api_call_failure(self, mock_post):
        """Test Ollama API call failure."""
        # Mock failed Ollama response
        mock_post.side_effect = Exception("Connection error")

        messages = [{"role": "user", "content": "Test message"}]

        with self.assertRaises(Exception):
            self.analyzer._call_ollama_api(messages)

    @patch('requests.post')
    def test_deepseek_api_call_success(self, mock_post):
        """Test successful DeepSeek API call."""
        # Mock successful DeepSeek response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": '{"sentiment_score": 0.7, "confidence": 0.85, "summary": "Positive earnings report"}'
                }
            }]
        }
        mock_post.return_value = mock_response

        messages = [{"role": "user", "content": "Test message"}]
        result = self.analyzer._call_deepseek_api(messages)

        self.assertIsInstance(result, dict)
        self.assertIn("choices", result)

    @patch('requests.post')
    def test_deepseek_api_call_failure(self, mock_post):
        """Test DeepSeek API call failure."""
        # Mock failed DeepSeek response
        mock_response = Mock()
        mock_response.status_code = 402
        mock_response.json.return_value = {
            "error": {"message": "Insufficient Balance"}
        }
        mock_post.return_value = mock_response

        messages = [{"role": "user", "content": "Test message"}]

        with self.assertRaises(Exception):
            self.analyzer._call_deepseek_api(messages)

    def test_analyze_news_sentiment_empty_news(self):
        """Test sentiment analysis with empty news list."""
        with self.assertRaises(Exception) as context:
            self.analyzer.analyze_news_sentiment([])

        # Should raise exception for empty news
        self.assertIn("No news articles provided", str(context.exception))

    def test_analyze_news_sentiment_no_valid_content(self):
        """Test sentiment analysis with invalid news format."""
        invalid_news = [
            {"invalid": "format"},
            {"missing": "required_fields"}
        ]

        with self.assertRaises(Exception) as context:
            self.analyzer.analyze_news_sentiment(invalid_news)

        # Should raise exception for no valid content
        self.assertIn("No valid news content found", str(context.exception))

    def test_signal_strength_calculation(self):
        """Test signal strength calculation logic."""
        # Test positive sentiment
        sentiment_data = {"sentiment_score": 0.8, "confidence": 0.9}
        signal = self.analyzer.get_trading_signal(sentiment_data)
        expected_strength = 0.8 * 0.9
        self.assertAlmostEqual(signal["signal_strength"], expected_strength, places=2)

        # Test negative sentiment
        sentiment_data = {"sentiment_score": -0.6, "confidence": 0.8}
        signal = self.analyzer.get_trading_signal(sentiment_data)
        expected_strength = 0.6 * 0.8
        self.assertAlmostEqual(signal["signal_strength"], expected_strength, places=2)

    def test_sentiment_threshold_logic(self):
        """Test sentiment threshold logic."""
        # Test sentiment below threshold
        sentiment_data = {
            "sentiment_score": Config.SENTIMENT_THRESHOLD - 0.01,
            "confidence": 0.9
        }
        signal = self.analyzer.get_trading_signal(sentiment_data)
        self.assertEqual(signal["action"], "HOLD")

        # Test sentiment above threshold
        sentiment_data = {
            "sentiment_score": Config.SENTIMENT_THRESHOLD + 0.01,
            "confidence": 0.9
        }
        signal = self.analyzer.get_trading_signal(sentiment_data)
        self.assertEqual(signal["action"], "CALL")


class SentimentAnalyzerIntegrationTest(unittest.TestCase):
    """Integration tests for SentimentAnalyzer with different providers."""

    def setUp(self):
        """Set up test environment."""
        self.analyzer = SentimentAnalyzer()
        self.sample_news = [
            {
                "headline": "Company beats earnings expectations",
                "summary": "Strong quarterly results drive stock higher",
                "datetime": 1640995200,
                "source": "Financial Times"
            }
        ]

    def test_provider_fallback_mechanism(self):
        """Test that analyzer falls back when providers fail."""
        # Test with a non-existent provider (should raise helpful error)
        with self.assertRaises(Exception) as context:
            result = self.analyzer.analyze_news_sentiment(
                self.sample_news,
                ai_provider="nonexistent"
            )

        # Should get a helpful error message about supported providers
        error_message = str(context.exception)
        self.assertIn("Unknown AI provider", error_message)
        self.assertIn("ollama", error_message.lower())

        # Test that Ollama works as primary provider
        try:
            result = self.analyzer.analyze_news_sentiment(
                self.sample_news,
                ai_provider="ollama"
            )
            self.assertIn('sentiment_score', result)
            print("✅ Ollama provider working as expected")
        except Exception as e:
            if 'not running' in str(e):
                self.skipTest("Ollama service not running - install and start Ollama")
            else:
                raise

    def test_multiple_provider_consistency(self):
        """Test that different providers return consistent data structure."""
        # Use only Ollama for consistency tests since it's free and always available
        providers = ['ollama']  # Removed 'deepseek', 'openai' due to quota issues

        results = {}
        for provider in providers:
            with self.subTest(provider=provider):
                try:
                    result = self.analyzer.analyze_news_sentiment(
                        self.sample_news,
                        ai_provider=provider
                    )
                    # Store result for comparison
                    results[provider] = result
                    # Check required fields
                    self.assertIn('sentiment_score', result)
                    self.assertIn('confidence', result)
                    self.assertIn('summary', result)
                    self.assertIn('provider', result)
                    # Check data types and ranges
                    self.assertIsInstance(result['sentiment_score'], (int, float))
                    self.assertIsInstance(result['confidence'], (int, float))
                    self.assertIsInstance(result['summary'], str)
                    self.assertGreaterEqual(result['sentiment_score'], -1)
                    self.assertLessEqual(result['sentiment_score'], 1)
                    self.assertGreaterEqual(result['confidence'], 0)
                    self.assertLessEqual(result['confidence'], 1)
                    print(f"✅ {provider} provider working correctly")
                except Exception as e:
                    if 'quota' in str(e).lower() or 'balance' in str(e).lower():
                        self.skipTest(f"Skipping {provider} - API quota exceeded: {e}")
                    else:
                        raise

        # If we have multiple providers, check consistency
        if len(results) > 1:
            providers_list = list(results.keys())
            for i in range(len(providers_list)):
                for j in range(i + 1, len(providers_list)):
                    provider1, provider2 = providers_list[i], providers_list[j]
                    result1, result2 = results[provider1], results[provider2]

                    # Results should have same structure (not necessarily same values)
                    self.assertEqual(set(result1.keys()), set(result2.keys()))

    def test_json_parsing_robustness(self):
        """Test that the analyzer handles malformed JSON responses."""
        # This would require mocking the API responses with malformed JSON
        # For now, we'll test with valid news data
        result = self.analyzer.analyze_news_sentiment(self.sample_news)

        # Should always return valid structure
        self.assertIsInstance(result, dict)
        self.assertIn("sentiment_score", result)
        self.assertIn("confidence", result)
        self.assertIn("summary", result)
        self.assertIn("provider", result)


if __name__ == "__main__":
    unittest.main(verbosity=2)