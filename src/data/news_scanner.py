#!/usr/bin/env python3
"""
Standalone News Scanner for Options Trading Sentiment Analysis
This script can be run independently to scan for news-driven trading opportunities.
It provides both command-line output and can save results to JSON files.
Usage:
    python news_scanner.py --mode news          # News-driven opportunities only
    python news_scanner.py --mode watchlist     # Watchlist opportunities only
    python news_scanner.py --mode all           # Both types
    python news_scanner.py --save results.json  # Save to JSON file
    python news_scanner.py --continuous         # Run continuously with updates
"""

import argparse
import json
import time
from datetime import datetime
from .news_monitor import NewsMonitor
from ..core.watchlist_manager import WatchlistManager
from ..core.config import Config

watchlist_manager = WatchlistManager()

# Replace Config.WATCHLIST_STOCKS and Config.WATCHLIST_CRYPTO with DB-driven lists
# Replace Config.NEWS_CATEGORIES, Config.MIN_NEWS_ARTICLES,
# Config.NEWS_CONFIDENCE_THRESHOLD, Config.NEWS_SENTIMENT_THRESHOLD with
# reasonable defaults

NEWS_CATEGORIES = ["business", "markets", "technology", "crypto"]
MIN_NEWS_ARTICLES = 3
NEWS_CONFIDENCE_THRESHOLD = 0.5
NEWS_SENTIMENT_THRESHOLD = 0.3


class NewsScanner:
    def __init__(self):
        self.monitor = NewsMonitor()

    def scan_opportunities(self, mode="all", save_file=None, verbose=True):
        """
        Scan for trading opportunities
        Args:
            mode: 'news', 'watchlist', or 'all'
            save_file: Optional file path to save results
            verbose: Print detailed output
        """
        if verbose:
            print("\n🔍 Scanning for {mode} opportunities...")
            print("⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("=" * 60)
        try:
            if mode == "news":
                trending_symbols = self.monitor.scan_trending_news()
                opportunities = self.monitor.analyze_news_driven_opportunities(
                    trending_symbols
                )
                results = {"news_driven": opportunities, "watchlist": []}
            elif mode == "watchlist":
                opportunities = self.monitor.analyze_watchlist_opportunities()
                results = {"news_driven": [], "watchlist": opportunities}
            else:  # all - combine both manually
                trending_symbols = self.monitor.scan_trending_news()
                news_opportunities = self.monitor.analyze_news_driven_opportunities(
                    trending_symbols
                )
                watchlist_opportunities = self.monitor.analyze_watchlist_opportunities()
                results = {
                    "news_driven": news_opportunities,
                    "watchlist": watchlist_opportunities,
                    "total_opportunities": len(news_opportunities)
                    + len(watchlist_opportunities),
                    "timestamp": datetime.now().isoformat(),
                }
            if verbose:
                self._print_results(results, mode)
            if save_file:
                self._save_results(results, save_file)
                if verbose:
                    print("\n💾 Results saved to {save_file}")
            return results
        except Exception:
            print("❌ Error scanning opportunities: {e}")
            return None

    def _print_results(self, results, mode):
        """Print formatted results to console"""
        news_opps = results.get("news_driven", [])
        watchlist_opps = results.get("watchlist", [])
        total_opps = len(news_opps) + len(watchlist_opps)
        print("📊 Found {total_opps} total opportunities")
        if mode in ["news", "all"] and news_opps:
            print("\n📰 News-Driven Opportunities ({len(news_opps)}):")
            print("-" * 40)
            for opp in news_opps:
                self._print_opportunity(opp)
        if mode in ["watchlist", "all"] and watchlist_opps:
            print("\n📋 Watchlist Opportunities ({len(watchlist_opps)}):")
            print("-" * 40)
            for opp in watchlist_opps:
                self._print_opportunity(opp)
        if total_opps == 0:
            print("🔍 No opportunities found at this time.")
            print("💡 Try again later or adjust your watchlist in config.py")

    def _print_opportunity(self, opp):
        """Print a single opportunity"""
        opp["symbol"]
        opp["signal_data"]["action"]
        opp["sentiment_data"]["sentiment_score"]
        opp["sentiment_data"]["confidence"]
        opp["price_data"]["current_price"]
        opp["trade_signal"]["strike_price"]
        opp["trade_signal"]["option_price"] * opp["trade_signal"]["position_size"]
        print("📈 {symbol} - {action}")
        print("   💰 Price: ${price:.2f} → Strike: ${strike:.2f}")
        print("   🧠 Sentiment: {sentiment:.3f} (Confidence: {confidence:.1%})")
        print(
            "   💵 Total Cost: ${cost:.2f} ({opp['trade_signal']['position_size']} contracts)"
        )
        print("   📰 News Articles: {opp['news_count']}")
        if opp.get("articles"):
            print(
                "   📄 Latest: "
                f"{opp['articles'][0].get('headline', 'No headline')[:60]}..."
            )
        print()

    def _save_results(self, results, filename):
        """Save results to JSON file"""
        # Add timestamp and metadata
        output = {
            "timestamp": datetime.now().isoformat(),
            "total_opportunities": len(results.get("news_driven", []))
            + len(results.get("watchlist", [])),
            "config": {
                "watchlist_stocks": watchlist_manager.get_stocks(),
                "watchlist_crypto": [],  # No crypto support
                "sentiment_threshold": Config.SENTIMENT_THRESHOLD,
                "news_sentiment_threshold": NEWS_SENTIMENT_THRESHOLD,
            },
            "results": results,
        }
        with open(filename, "w") as f:
            json.dump(output, f, indent=2, default=str)

    def continuous_scan(self, interval_minutes=30, mode="all"):
        """
        Run continuous scanning with periodic updates
        Args:
            interval_minutes: Minutes between scans
            mode: Scan mode ('news', 'watchlist', 'all')
        """
        print("🔄 Starting continuous scanning (every {interval_minutes} minutes)")
        print("📊 Mode: {mode}")
        print("⏹️  Press Ctrl+C to stop")
        print("=" * 60)
        try:
            while True:
                self.scan_opportunities(mode=mode, verbose=True)
                print("\n⏳ Next scan in {interval_minutes} minutes...")
                print("=" * 60)
                time.sleep(interval_minutes * 60)
        except KeyboardInterrupt:
            print("\n\n⏹️  Scanning stopped by user")
        except Exception:
            print("\n❌ Error in continuous scanning: {e}")

    def _process_news_item(self, news_item):
        """Process a single news item"""
        # TODO: Implement news item processing logic


def main():
    parser = argparse.ArgumentParser(
        description="Scan for news-driven trading opportunities",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python news_scanner.py                           # Scan all opportunities
  python news_scanner.py --mode news               # News-driven only
  python news_scanner.py --mode watchlist          # Watchlist only
  python news_scanner.py --save results.json       # Save to file
  python news_scanner.py --continuous              # Run continuously
  python news_scanner.py --continuous --interval 15 # Every 15 minutes
        """,
    )
    parser.add_argument(
        "--mode",
        choices=["news", "watchlist", "all"],
        default="all",
        help="Type of opportunities to scan for (default: all)",
    )
    parser.add_argument("--save", metavar="FILE", help="Save results to JSON file")
    parser.add_argument(
        "--continuous", action="store_true", help="Run continuous scanning"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=30,
        help="Minutes between scans in continuous mode (default: 30)",
    )
    parser.add_argument("--quiet", action="store_true", help="Suppress detailed output")
    args = parser.parse_args()
    # Initialize scanner
    scanner = NewsScanner()
    # Print configuration info
    if not args.quiet:
        print("🚀 Options Trading News Scanner")
        print("📋 Watchlist Stocks: {len(watchlist_manager.get_stocks())} symbols")
        print("🎯 Sentiment Threshold: {Config.SENTIMENT_THRESHOLD}")
        print("📰 News Sentiment Threshold: {NEWS_SENTIMENT_THRESHOLD}")
    # Run scanner
    if args.continuous:
        scanner.continuous_scan(interval_minutes=args.interval, mode=args.mode)
    else:
        scanner.scan_opportunities(
            mode=args.mode, save_file=args.save, verbose=not args.quiet
        )


if __name__ == "__main__":
    main()
