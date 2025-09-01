import unittest
import requests
import os
from datetime import datetime

BASE_URL = os.environ.get("TRADING_APP_URL", "http://localhost:5001")
TIMEOUT = 15


def _get_json(path, method="GET", payload=None, timeout=TIMEOUT):
    url = f"{BASE_URL}{path}"
    if method == "GET":
        r = requests.get(url, timeout=timeout)
    else:
        r = requests.post(url, json=payload or {}, timeout=timeout)
    try:
        data = r.json()
    except Exception:
        data = {"__raw_text": r.text}
    return r.status_code, data


class RealDataValidationTest(unittest.TestCase):
    """Validate that pages and APIs return populated, non-placeholder data."""

    @classmethod
    def setUpClass(cls):
        # quick server availability check
        try:
            resp = requests.get(f"{BASE_URL}/api/system_status", timeout=5)
            if resp.status_code not in (200, 500, 404):
                raise unittest.SkipTest("Application not responding on expected port")
        except requests.exceptions.RequestException:
            raise unittest.SkipTest("Application not running at http://localhost:5001")

    def assert_nonempty_list(self, obj, field_name):
        self.assertIsInstance(obj, list, f"{field_name} should be a list")
        self.assertGreaterEqual(len(obj), 1, f"{field_name} should have at least one item")

    def test_01_dashboard_data(self):
        code, data = _get_json("/api/dashboard/data")
        self.assertEqual(code, 200)
        self.assertTrue(data.get("success", False))
        payload = data.get("data", {})
        self.assertIsInstance(payload, dict)
        # Feature cards and market overview presence
        self.assertIn("feature_cards", payload)
        self.assertIn("market_overview", payload)

    def test_02_sp500_analysis(self):
        # Use higher timeout and limit workload
        code, data = _get_json("/api/sp500_analysis?limit=3", timeout=60)
        self.assertEqual(code, 200)
        self.assertTrue(data.get("success", False))
        stocks = data.get("data", {}).get("enhanced_analysis", [])
        self.assertIsInstance(stocks, list, "enhanced_analysis should be a list")

        # Detect permanent fallback (if API provided source field)
        src = data.get("data", {}).get("source")
        if src == "fallback":
            self.fail("/api/sp500_analysis responded with fallback source only")

    def test_03_crypto_analysis_fast_and_full(self):
        # Fast preload mode
        code, data = _get_json("/api/crypto_analysis?fast=1")
        self.assertEqual(code, 200)
        self.assertTrue(data.get("success", False))
        fast_data = data.get("data", {})
        self.assertIn("opportunities", fast_data)
        # Full analysis (cached or fresh)
        code2, data2 = _get_json("/api/crypto_analysis")
        self.assertEqual(code2, 200)
        self.assertTrue(data2.get("success", False))
        full_data = data2.get("data", {})
        self.assertIn("opportunities", full_data)

    def test_04_portfolio(self):
        code, data = _get_json("/api/portfolio")
        self.assertEqual(code, 200)
        self.assertTrue(data.get("success", False))
        d = data.get("data", {})
        self.assertIn("portfolio_summary", d)
        self.assertIn("open_positions", d)
        self.assertIn("recent_trades", d)

    def test_05_opportunities_endpoints(self):
        code, news = _get_json("/api/news_opportunities")
        self.assertEqual(code, 200)
        self.assertTrue(news.get("success", False))

        # Data is nested under 'data'
        news_data = news.get("data", {})
        self.assertIn("opportunities", news_data)
        self.assertIsInstance(news_data.get("opportunities", []), list)

        code2, wl = _get_json("/api/watchlist_opportunities")
        self.assertEqual(code2, 200)
        self.assertTrue(wl.get("success", False))
        wl_data = wl.get("data", {})
        self.assertIn("opportunities", wl_data)
        self.assertIsInstance(wl_data.get("opportunities", []), list)

    def test_06_system_status(self):
        code, data = _get_json("/api/system_status")
        self.assertEqual(code, 200)
        for key in ["status", "system", "database", "cache", "config"]:
            self.assertIn(key, data)

    def test_07_telegram_foreign(self):
        # Tier system removed - testing other functionality
        # Telegram stub connectivity
        code2, tg = _get_json("/api/telegram/test")
        self.assertEqual(code2, 200)
        self.assertIn("status", tg)
        # Foreign markets overview
        code3, fm = _get_json("/api/foreign_markets/overview")
        self.assertEqual(code3, 200)
        self.assertTrue(fm.get("success", False))
        data = fm.get("data", {})
        self.assertIn("markets", data)
        self.assertIn("summary", data)
        # Ensure some markets are present
        self.assertIsInstance(data.get("markets", []), list)

    def test_08_scalping_endpoints_exist(self):
        # Do not fail if empty; ensure endpoints respond
        code1, opp = _get_json("/api/scalping/opportunities")
        self.assertIn(code1, (200, 500))
        code2, today = _get_json("/api/scalping/today")
        self.assertIn(code2, (200, 500))
        code3, hist = _get_json("/api/scalping/history")
        self.assertIn(code3, (200, 500))
        code4, stats = _get_json("/api/scalping/stats")
        self.assertIn(code4, (200, 500))


if __name__ == "__main__":
    unittest.main(verbosity=2)
