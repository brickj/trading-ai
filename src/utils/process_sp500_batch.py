#!/usr/bin/env python3
"""
Script to process a batch of S&P 500 stocks and add their recommendations to the database.
This demonstrates how to process multiple stocks efficiently and store recommendations.
"""
from src.trading.enhanced_trading_strategy import EnhancedTradingStrategy
from src.core.sentiment_analyzer import SentimentAnalyzer
from src.data.data_fetcher import DataFetcher
from src.core.config import Config
import time
import sys
import os
import argparse

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)


def process_sp500_batch(batch_size=50, ai_provider="ollama"):
    """
    Process a batch of S&P 500 stocks and store recommendations in the database.
    Args:
        batch_size: Number of stocks to process (default: 50)
        ai_provider: AI provider to use for sentiment analysis (default: ollama)
    """
    print(f"🚀 Processing top {batch_size} S&P 500 stocks for recommendation database...")
    print("=" * 60)
    # Initialize components
    data_fetcher = DataFetcher()
    sentiment_analyzer = SentimentAnalyzer()
    enhanced_trading_strategy = EnhancedTradingStrategy()
    #     recommendation_manager = get_recommendation_manager()
    # Get stock symbols (limited to batch_size)
    sp500_symbols = data_fetcher.get_current_sp500_symbols()[:batch_size]
    print(f"📋 Processing {len(sp500_symbols)} stocks: {', '.join(sp500_symbols[:5])}...")
    print()
    # Keep track of success and failures
    successful = []
    failed = []
    # Process each stock
    for i, symbol in enumerate(sp500_symbols, 1):
        try:
            print(f"[{i}/{len(sp500_symbols)}] Processing {symbol}...")
            # Step 1: Get news data
            try:
                news_data = data_fetcher.get_company_news(symbol, days_back=7)
                print(f"  ✅ Got {len(news_data)} news articles for {symbol}")
            except Exception as e:
                print(f"  ❌ Failed to get news for {symbol}: {e}")
                failed.append((symbol, f"News error: {str(e)}"))
                continue
            # Step 2: Analyze sentiment
            try:
                # Get price data first for fallback
                price_data = data_fetcher.get_stock_price(symbol)
                # Analyze sentiment with fallback
                try:
                    if news_data and len(news_data) > 0:
                        sentiment_data = sentiment_analyzer.analyze_news_sentiment(
                            news_data, ai_provider=ai_provider
                        )
                    else:
                        # Fallback to price-based sentiment analysis
                        print(f"  📊 No news articles for {symbol}, using price-based sentiment analysis...")
                        sentiment_data = sentiment_analyzer.analyze_price_based_sentiment(price_data, symbol)
                except Exception as e:
                    # If news sentiment fails, try price-based analysis
                    if "No news articles provided for analysis" in str(e) or "No valid news content found" in str(e):
                        print(f"  📊 News analysis failed for {symbol}, falling back to price-based analysis...")
                        sentiment_data = sentiment_analyzer.analyze_price_based_sentiment(price_data, symbol)
                    else:
                        # Re-raise other types of errors
                        raise e
                print(
                    f"  ✅ Sentiment score: {sentiment_data['sentiment_score']:.2f} with {sentiment_data['confidence']:.2f} confidence"
                )
            except Exception as e:
                print(f"  ❌ Failed to analyze sentiment for {symbol}: {e}")
                failed.append((symbol, f"Sentiment error: {str(e)}"))
                continue
            # Step 3: Get price data (already fetched above)
            try:
                print(f"  ✅ Current price: ${price_data['current_price']:.2f}")
            except Exception as e:
                print(f"  ❌ Failed to get price for {symbol}: {e}")
                failed.append((symbol, f"Price error: {str(e)}"))
                continue
            # Step 4: Generate signal
            signal_data = sentiment_analyzer.get_trading_signal(sentiment_data)
            print(
                f"  ✅ Trading signal: {signal_data['action']} with {signal_data['confidence']:.2f} confidence"
            )
            # Step 5: Generate comprehensive recommendations
            try:
                comprehensive_result = enhanced_trading_strategy.get_comprehensive_recommendations(
                    symbol, price_data["current_price"], sentiment_data, signal_data
                )
                # Get recommendations
                comprehensive_result.get("all_recommendations", [])
                comprehensive_result.get("stock_recommendations", [])
                comprehensive_result.get("options_recommendations", [])
                print("  ✅ Generated recommendations")
                # Step 6: Check if recommendations were saved to database
                top_recommendation = comprehensive_result.get("top_recommendation")
                if top_recommendation:
                    top_recommendation.get("recommendation_type", "Unknown")
                    top_recommendation.get("action", "Unknown")
                    top_recommendation.get("confidence", 0)
                    print("  ✅ Top recommendation generated")
                successful.append(symbol)
            except Exception as e:
                print(f"  ❌ Failed to generate recommendations for {symbol}: {e}")
                failed.append((symbol, f"Recommendation error: {str(e)}"))
                continue
            # Sleep to avoid rate limiting
            time.sleep(2)
            print()
        except Exception as e:
            print(f"  ❌ Unexpected error processing {symbol}: {e}")
            failed.append((symbol, f"Unexpected error: {str(e)}"))
            print()
            continue
    # Print summary
    print("=" * 60)
    print("📊 Processing complete!")
    print(f"✅ Successfully processed: {len(successful)}/{len(sp500_symbols)} stocks")
    print(f"❌ Failed to process: {len(failed)}/{len(sp500_symbols)} stocks")
    if failed:
        print("\n❌ Failed stocks:")
        for symbol, error in failed:
            print(f"  - {symbol}: {error}")
    # Check recommendation stats
    print("\n📊 Recommendation database status:")
    # Note: Recommendation manager functionality temporarily disabled
    print("  - Recommendation stats temporarily unavailable")
    # Calculate total time for 500 stocks
    print(
        f"\n⏱️ Estimated time for all 500 S&P stocks: {(30 * 500 / 60):.1f} minutes ({(30 * 500 / 60 / 60):.1f} hours)"
    )
    return successful, failed


if __name__ == "__main__":
    # Set up command line argument parsing
    parser = argparse.ArgumentParser(
        description="Process a batch of S&P 500 stocks for recommendation database"
    )
    parser.add_argument(
        "--top",
        type=int,
        default=50,
        help="Number of top S&P 500 stocks to process (default: 50)",
    )
    parser.add_argument(
        "--provider",
        type=str,
        default="ollama",
        choices=["ollama", "deepseek", "openai"],
        help="AI provider to use for sentiment analysis (default: ollama)",
    )
    args = parser.parse_args()
    # Process batch with properly parsed arguments
    process_sp500_batch(batch_size=args.top, ai_provider=args.provider)
