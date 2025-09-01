import unittest
import time
import requests
import os
from tests.utils.validators import (
    is_iso_timestamp, is_percent_like, ensure_keys, is_number, within_range, recent_timestamp
)
from tests.utils.report_writer import ReportWriter

BASE_URL = os.environ.get("TRADING_APP_URL", "http://localhost:5001")


def get_json(path, timeout=30):
    url = f"{BASE_URL}{path}"
    t0 = time.time()
    r = requests.get(url, timeout=timeout)
    elapsed = time.time() - t0
    try:
        data = r.json()
    except Exception:
        data = {"__raw_text": r.text}
    return r.status_code, data, elapsed


class DeepValidationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = ReportWriter()
        # sanity check server
        try:
            code, data, _ = get_json("/api/system_status", timeout=10)
            if code not in (200, 500, 404):
                raise unittest.SkipTest("Server not responding correctly")
        except requests.exceptions.RequestException:
            raise unittest.SkipTest("Server unavailable at http://localhost:5001")

    @classmethod
    def tearDownClass(cls):
        path = cls.report.save()
        print(f"\nDeep validation report saved: {path}")

    def test_dashboard(self):
        code, data, t = get_json("/api/dashboard/data", timeout=30)
        self.assertEqual(code, 200)
        self.assertTrue(data.get("success", False))
        payload = data.get("data", {})
        missing = ensure_keys(payload, ["feature_cards", "market_overview", "last_analysis"])
        self.assertFalse(missing, f"Dashboard missing keys: {missing}")
        # Validate market_overview fields
        mo = payload.get("market_overview", {})
        missing = ensure_keys(mo, ["total_stocks", "active_analyses", "success_rate", "last_updated"])
        self.assertFalse(missing, f"market_overview missing: {missing}")
        self.assertTrue(is_number(mo.get("total_stocks", 0)))
        self.assertTrue(is_percent_like(mo.get("success_rate", "")))
        self.assertTrue(is_iso_timestamp(mo.get("last_updated")))
        self.report.record_endpoint("dashboard", {"status": code, "time": t, "market_overview": mo})

    def test_sp500_analysis_strict(self):
        code, data, t = get_json("/api/sp500_analysis?limit=3", timeout=120)
        self.assertEqual(code, 200)
        self.assertTrue(data.get("success", False))
        payload = data.get("data", {})
        analysis = payload.get("enhanced_analysis", [])
        self.assertIsInstance(analysis, list)
        self.assertGreaterEqual(len(analysis), 1, "enhanced_analysis empty (unexpected)")
        # No fallback allowed
        if payload.get("source") == "fallback":
            self.fail("sp500_analysis returned fallback source")
        # Validate first item schema
        item = analysis[0]
        miss = ensure_keys(item, ["symbol", "price_data", "sentiment_data", "comprehensive_analysis"]) \
            or ensure_keys(item.get("price_data", {}), ["current_price"]) \
            or ensure_keys(item.get("sentiment_data", {}), ["sentiment_score"]) \
            or ensure_keys(item.get("comprehensive_analysis", {}), ["top_recommendation"])
        self.assertFalse(miss, f"sp500_analysis schema missing: {miss}")
        self.assertTrue(is_number(item.get("price_data", {}).get("current_price")))
        self.assertTrue(within_range(item.get("sentiment_data", {}).get("sentiment_score"), -1, 1))
        if t > 90:
            self.fail(f"sp500_analysis too slow: {t:.1f}s")
        self.report.record_endpoint("sp500_analysis", {"status": code, "time": t, "count": len(analysis)})

    def test_crypto_analysis_strict(self):
        # fast
        code, data, t = get_json("/api/crypto_analysis?fast=1", timeout=45)
        self.assertEqual(code, 200)
        self.assertTrue(data.get("success", False))
        opps = data.get("data", {}).get("opportunities", [])
        self.assertIsInstance(opps, list)
        self.report.record_endpoint("crypto_fast", {"status": code, "time": t, "count": len(opps)})
        # full
        code2, data2, t2 = get_json("/api/crypto_analysis", timeout=120)
        self.assertEqual(code2, 200)
        self.assertTrue(data2.get("success", False))
        opps2 = data2.get("data", {}).get("opportunities", [])
        self.assertIsInstance(opps2, list)
        if t2 > 120:
            self.fail(f"crypto_analysis too slow: {t2:.1f}s")
        self.report.record_endpoint("crypto_full", {"status": code2, "time": t2, "count": len(opps2)})

    def test_portfolio_strict(self):
        code, data, t = get_json("/api/portfolio", timeout=30)
        self.assertEqual(code, 200)
        self.assertTrue(data.get("success", False))
        d = data.get("data", {})
        miss = ensure_keys(d, ["portfolio_summary", "open_positions", "recent_trades"])
        self.assertFalse(miss, f"portfolio missing: {miss}")
        ps = d.get("portfolio_summary", {})
        self.assertTrue(is_number(ps.get("current_capital", 0)))
        self.report.record_endpoint("portfolio", {"status": code, "time": t})

    def test_opportunities_strict(self):
        # news
        code, news, tn = get_json("/api/news_opportunities", timeout=45)
        self.assertEqual(code, 200)
        self.assertTrue(news.get("success", False))
        news_data = news.get("data", {})
        self.assertIn("opportunities", news_data)
        self.assertIsInstance(news_data.get("opportunities", []), list)
        # watchlist
        code2, wl, tw = get_json("/api/watchlist_opportunities", timeout=45)
        self.assertEqual(code2, 200)
        self.assertTrue(wl.get("success", False))
        wl_data = wl.get("data", {})
        self.assertIn("opportunities", wl_data)
        self.assertIsInstance(wl_data.get("opportunities", []), list)
        self.report.record_endpoint("opportunities", {"status_news": code, "status_watchlist": code2, "time_news": tn, "time_watchlist": tw, "news_count": len(news_data.get("opportunities", [])), "watchlist_count": len(wl_data.get("opportunities", []))})

    def test_system_status_strict(self):
        code, data, t = get_json("/api/system_status", timeout=30)
        self.assertEqual(code, 200)
        for key in ["status", "system", "database", "cache", "config"]:
            self.assertIn(key, data)
        self.report.record_endpoint("system_status", {"status": code, "time": t})

    def test_telegram_foreign_strict(self):
        # Tier system removed - testing other functionality
        code2, tg, t2 = get_json("/api/telegram/test", timeout=30)
        self.assertEqual(code2, 200)
        self.assertIn("status", tg)
        code3, fm, t3 = get_json("/api/foreign_markets/overview", timeout=60)
        self.assertEqual(code3, 200)
        self.assertTrue(fm.get("success", False))
        data = fm.get("data", {})
        self.assertIn("markets", data)
        self.assertIn("summary", data)
        markets = data.get("markets", [])
        self.assertIsInstance(markets, list)
        self.assertGreaterEqual(len(markets), 1, "no markets returned")
        # status class sanity
        allowed_status = {"Open", "Pre-Market", "After Hours", "Closed"}
        allowed_class = {"success", "warning", "secondary"}
        for m in markets[:5]:
            self.assertIn(m.get("status"), allowed_status)
            self.assertIn(m.get("status_class"), allowed_class)
        self.report.record_endpoint("foreign_markets_overview", {"status": code3, "time": t3, "markets": len(markets)})

    def test_scalping_endpoints_strict(self):
        endpoints = ["/api/scalping/opportunities", "/api/scalping/today", "/api/scalping/history", "/api/scalping/stats"]
        rec = {}
        for ep in endpoints:
            try:
                code, data, t = get_json(ep, timeout=30)
                rec[ep] = {"status": code, "time": t, "has_error": not data.get("success", True)}
                # treat persistent 500 as failure
                self.assertIn(code, (200,))
            except requests.exceptions.RequestException as e:
                self.fail(f"{ep} request failed: {e}")
        self.report.record_endpoint("scalping", rec)


if __name__ == "__main__":
    unittest.main(verbosity=2)
