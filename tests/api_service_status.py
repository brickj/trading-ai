"""API availability checking script for Trading AI external integrations.

This script probes every external API that the application integrates with and
reports whether the endpoint is reachable with the currently configured
credentials. It is intentionally written as a standalone diagnostic utility so
that it can be run manually (``python tests/api_service_status.py``) without
requiring the rest of the test suite.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Optional, Tuple

import importlib.util
import requests


REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = REPO_ROOT / "src" / "core" / "config.py"

try:
    spec = importlib.util.spec_from_file_location("trading_ai_config", CONFIG_PATH)
    if spec is None or spec.loader is None:  # pragma: no cover - defensive guard
        raise ImportError(f"Unable to load configuration module from {CONFIG_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    Config = getattr(module, "Config")
except Exception as exc:  # pragma: no cover - defensive guard for import errors
    print(f"❌ Unable to import configuration: {exc}")
    sys.exit(1)


StatusTuple = Tuple[str, str]
ResultType = Tuple[str, StatusTuple]
Validator = Callable[[requests.Response], Tuple[bool, str]]
SkipEvaluator = Callable[[], Optional[str]]


NEWS_API_KEY = getattr(Config, "NEWS_API_KEY", getattr(Config, "NEWSAPI_API_KEY", ""))
MARKETAUX_API_KEY = getattr(Config, "MARKETAUX_API_KEY", "")
OLLAMA_BASE_URL = getattr(Config, "OLLAMA_BASE_URL", "http://localhost:11434")

@dataclass
class EndpointTest:
    """Definition of a single API probe."""

    name: str
    method: str
    url: str
    params: Optional[Dict[str, str]] = None
    headers: Optional[Dict[str, str]] = None
    data: Optional[Dict[str, str]] = None
    json_body: Optional[Dict[str, object]] = None
    auth: Optional[Tuple[str, str]] = None
    timeout: int = 20
    skip_if: Optional[SkipEvaluator] = None
    validator: Optional[Validator] = None


def _is_missing(value: Optional[str]) -> bool:
    """Return ``True`` when a configuration value is missing or a placeholder."""

    if value is None:
        return True
    normalized = str(value).strip()
    if not normalized:
        return True
    lower = normalized.lower()
    return lower in {"none", "null"} or "your_" in lower or "changeme" in lower


def _require_key(value: Optional[str], description: str) -> SkipEvaluator:
    """Return a skip evaluator that reports missing API credentials."""

    def _inner() -> Optional[str]:
        if _is_missing(value):
            return f"Missing or placeholder credentials for {description}"
        return None

    return _inner


def _require_enabled(flag: bool, description: str) -> SkipEvaluator:
    """Return a skip evaluator controlled by a boolean feature flag."""

    def _inner() -> Optional[str]:
        if not flag:
            return f"{description} integration disabled"
        return None

    return _inner


def _combine_skip_evaluators(*evaluators: Optional[SkipEvaluator]) -> SkipEvaluator:
    """Combine multiple skip evaluators into a single callable."""

    valid_evaluators = [e for e in evaluators if e is not None]

    def _inner() -> Optional[str]:
        for evaluator in valid_evaluators:
            reason = evaluator()
            if reason:
                return reason
        return None

    return _inner


def _default_validator(response: requests.Response) -> Tuple[bool, str]:
    """Basic validator that treats any 2xx status code as success."""

    return response.ok, f"status={response.status_code}"


def _connection_validator(response: requests.Response) -> Tuple[bool, str]:
    """Validator that treats any successful connection (status < 500) as OK."""

    status = response.status_code
    return status < 500, f"status={status}"


def build_tests() -> Iterable[EndpointTest]:
    """Create the list of API probes derived from the codebase."""

    tests: List[EndpointTest] = [
        EndpointTest(
            name="Alpha Vantage (GLOBAL_QUOTE)",
            method="GET",
            url="https://www.alphavantage.co/query",
            params={
                "function": "GLOBAL_QUOTE",
                "symbol": "IBM",
                "apikey": Config.ALPHA_VANTAGE_API_KEY,
            },
            skip_if=_require_key(Config.ALPHA_VANTAGE_API_KEY, "Alpha Vantage"),
        ),
        EndpointTest(
            name="Finnhub Quote",
            method="GET",
            url="https://finnhub.io/api/v1/quote",
            params={"symbol": "AAPL", "token": Config.FINNHUB_API_KEY},
            skip_if=_require_key(Config.FINNHUB_API_KEY, "Finnhub"),
        ),
        EndpointTest(
            name="NewsAPI Everything",
            method="GET",
            url="https://newsapi.org/v2/everything",
            params={"q": "stocks", "pageSize": "1", "apiKey": NEWS_API_KEY},
            skip_if=_require_key(NEWS_API_KEY, "NewsAPI"),
        ),
        EndpointTest(
            name="CryptoPanic Posts",
            method="GET",
            url="https://cryptopanic.com/api/v1/posts/",
            params={"auth_token": Config.CRYPTOPANIC_API_KEY, "public": "true"},
            skip_if=_require_key(Config.CRYPTOPANIC_API_KEY, "CryptoPanic"),
        ),
        EndpointTest(
            name="Yahoo Finance Chart",
            method="GET",
            url="https://query1.finance.yahoo.com/v8/finance/chart/AAPL",
        ),
        EndpointTest(
            name="CoinGecko Bitcoin Page",
            method="GET",
            url="https://coingecko.com/en/coins/bitcoin",
            skip_if=_require_enabled(getattr(Config, "COINGECKO_ENABLED", False), "CoinGecko"),
        ),
        EndpointTest(
            name="Wikipedia S&P 500 Constituents",
            method="GET",
            url="https://en.wikipedia.org/wiki/List_of_S%26P_500_companies",
            headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
            },
        ),
        EndpointTest(
            name="Reddit OAuth Token",
            method="POST",
            url="https://www.reddit.com/api/v1/access_token",
            headers={"User-Agent": "trading-ai-diagnostics/0.1"},
            data={"grant_type": "client_credentials"},
            auth=(Config.REDDIT_CLIENT_ID, Config.REDDIT_SECRET_KEY),
            skip_if=_combine_skip_evaluators(
                _require_enabled(getattr(Config, "REDDIT_ENABLED", False), "Reddit"),
                _require_key(Config.REDDIT_CLIENT_ID, "Reddit client ID"),
                _require_key(Config.REDDIT_SECRET_KEY, "Reddit secret key"),
            ),
        ),
        EndpointTest(
            name="Marketaux News",
            method="GET",
            url="https://api.marketaux.com/v1/news/all",
            params={
                "api_token": MARKETAUX_API_KEY,
                "limit": "1",
                "language": "en",
                "countries": "us",
            },
            skip_if=_require_key(MARKETAUX_API_KEY, "Marketaux"),
        ),
        EndpointTest(
            name="Telegram getMe",
            method="GET",
            url=f"https://api.telegram.org/bot{Config.TELEGRAM_API_KEY}/getMe",
            skip_if=_require_key(Config.TELEGRAM_API_KEY, "Telegram"),
        ),
        EndpointTest(
            name="DeepSeek Chat",
            method="POST",
            url="https://api.deepseek.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {getattr(Config, 'DEEPSEEK_API_KEY', '')}", "Content-Type": "application/json"},
            json_body={
                "model": "deepseek-chat",
                "messages": [
                    {"role": "user", "content": "Ping"},
                ],
                "max_tokens": 5,
            },
            skip_if=_require_key(getattr(Config, "DEEPSEEK_API_KEY", None), "DeepSeek"),
        ),
        EndpointTest(
            name="OpenAI Chat",
            method="POST",
            url="https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {Config.OPENAI_API_KEY}",
                "Content-Type": "application/json",
            },
            json_body={
                "model": "gpt-3.5-turbo",
                "messages": [
                    {"role": "user", "content": "Ping"},
                ],
                "max_tokens": 5,
            },
            skip_if=_require_key(Config.OPENAI_API_KEY, "OpenAI"),
        ),
        EndpointTest(
            name="Ollama Local Service",
            method="GET",
            url=f"{OLLAMA_BASE_URL}/api/tags",
            timeout=5,
            validator=_connection_validator,
        ),
    ]

    # Go microservices (News, Signal, Risk, Portfolio, Data)
    if getattr(Config, "USE_GO_SERVICES", False):
        go_services = {
            "Go News Service": getattr(Config, "GO_NEWS_SERVICE_URL", "http://localhost:8081"),
            "Go Signal Service": getattr(Config, "GO_SIGNAL_SERVICE_URL", "http://localhost:8082"),
            "Go Risk Service": getattr(Config, "GO_RISK_SERVICE_URL", "http://localhost:8083"),
            "Go Portfolio Service": getattr(Config, "GO_PORTFOLIO_SERVICE_URL", "http://localhost:8084"),
            "Go Data Service": getattr(Config, "GO_DATA_SERVICE_URL", "http://localhost:8085"),
        }
        for name, base_url in go_services.items():
            tests.append(
                EndpointTest(
                    name=name,
                    method="GET",
                    url=base_url,
                    timeout=5,
                    validator=_connection_validator,
                )
            )

    return tests


def run_tests(tests: Iterable[EndpointTest]) -> List[ResultType]:
    """Execute each API probe and collect the results."""

    session = requests.Session()
    results: List[ResultType] = []

    for test in tests:
        skip_reason = test.skip_if() if test.skip_if else None
        if skip_reason:
            results.append((test.name, ("skipped", skip_reason)))
            continue

        try:
            response = session.request(
                method=test.method,
                url=test.url,
                params=test.params,
                headers=test.headers,
                data=test.data,
                json=test.json_body,
                auth=test.auth,
                timeout=test.timeout,
            )
            validator = test.validator or _default_validator
            ok, detail = validator(response)
            status = "success" if ok else "failure"
            results.append((test.name, (status, detail)))
        except requests.exceptions.RequestException as exc:
            results.append((test.name, ("failure", str(exc))))

    return results


def print_report(results: Iterable[ResultType]) -> None:
    """Pretty-print the API availability report."""

    status_emojis = {"success": "✅", "failure": "❌", "skipped": "⚪"}
    summary = {"success": 0, "failure": 0, "skipped": 0}

    print("\n=== Trading AI API Availability Report ===\n")
    for name, (status, detail) in results:
        summary[status] += 1
        emoji = status_emojis.get(status, "•")
        print(f"{emoji} {name}: {detail}")

    print("\nSummary:")
    for status in ("success", "failure", "skipped"):
        emoji = status_emojis.get(status, "•")
        print(f"  {emoji} {status.title()}: {summary[status]}")
    print()


def main() -> None:
    tests = list(build_tests())
    results = run_tests(tests)
    print_report(results)


if __name__ == "__main__":
    main()
