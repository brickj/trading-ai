# Sentiment Analysis Overview

## News collection and filtering
- The `DataFetcher` aggregates company news from multiple upstream sources (Alpha Vantage, Reddit, Finnhub, and Yahoo Finance), deduplicates by headline, and filters aggressively for symbol-specific coverage so that the downstream model receives focused inputs. This routine also injects deterministic fallback blurbs when few articles survive filtering to keep the analysis pipeline alive.
- News items are sorted by recency and the source mix is logged for transparency before the sentiment step runs.

## Prompt preparation and scoring
- `SentimentAnalyzer.analyze_news_sentiment` merges stock-specific and general articles, applying higher weights to ticker-focused pieces so their tone dominates the final score.
- Each article now contributes a compact bullet that contains the headline, an automatically shortened summary, its weighting factor, and (when available) the originating source. This keeps the language model prompt short while still conveying the main idea of every article that made it through filtering while giving the LLM visibility into repeatedly accurate outlets.
- The analyzer builds a context-specific prompt (crypto vs. equities), dispatches it to the configured provider (Ollama, DeepSeek, or OpenAI), and performs defensive parsing of the JSON payload before returning a normalized `sentiment_score`, `confidence`, and summary string.

## Historical optimization without RAG
- Before the prompt is built, the combined news set plus optional historical sentiment records are forwarded to a lightweight Go helper (`go/cmd/sentiment_optimizer`). The helper re-weights each article using:
  - historical alignment between prior sentiment calls and realized returns per news source;
  - recency decay to keep stale articles from dominating the prompt; and
  - aggregate drift indicators that surface whether the underlying sentiment tends to over- or under-shoot actual price moves.
- The Go process returns calibrated weights along with a baseline sentiment shift and confidence nudge. The Python analyzer applies these adjustments post-LLM to keep the final score grounded in observed outcomes while avoiding a full retrieval-augmented generation (RAG) setup.
- Historical records can be supplied programmatically (via the `historical_sentiment` argument) or by pointing `Config.HISTORICAL_SENTIMENT_PATH` at a JSON file shaped as `{ "TICKER": [{"sentiment": 0.2, "realized_return": 0.15, ...}] }`. Missing or unreadable data gracefully fall back to the default recency heuristics with clear log messages.
- Optimizer diagnostics (per-source accuracy, baseline drift, and notes on the applied adjustments) are returned in `analysis_metadata['go_optimizer']` so the UI or downstream analytics can highlight why the score moved.

## Fallback behaviour
- When AI providers are unreachable or return invalid payloads, the analyzer drops to a neutral sentiment response. If news is entirely unavailable, price-based heuristics (`analyze_price_based_sentiment`) generate a backup sentiment score from price momentum and technical cues.

## Easy wins to improve recommendations
- Tighten the summarization step further by trimming redundant boilerplate ("press release", "reuters", etc.) to buy more prompt space for substantive facts.
- Expand metadata returned to the UI (for example, include per-article confidence heuristics such as source credibility) so the frontend can visualize why the score looks the way it does. The Go optimizer now exposes these credibility signals by source, but the frontend can bubble them up more prominently.
- Cache per-article sentiment snippets to avoid re-querying the LLM when the same article appears across multiple tickers, reducing latency and cost while improving consistency.
- Blend the current news-driven score with the historical backtest confidence that already powers strategy ranking to highlight ideas that align both with sentiment and with proven performance.
- Track the predictive quality of generated sentiment versus realized returns inside a lightweight store so the Go helper's baseline and confidence tweaks can become more personalized over time (e.g., per-sector or per-volatility regime).
