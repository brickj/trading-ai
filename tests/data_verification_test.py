import unittest
import json
import requests
import psycopg2
import psycopg2.extras
import importlib.util
from pathlib import Path

try:
    from src.core.config import Config  # type: ignore
except ModuleNotFoundError:  # Fallback if config.py is not present
    config_path = Path(__file__).resolve().parent.parent / "src" / "core" / "config.template.py"
    spec = importlib.util.spec_from_file_location("config_template", config_path)
    config_module = importlib.util.module_from_spec(spec)  # type: ignore
    assert spec.loader is not None
    spec.loader.exec_module(config_module)  # type: ignore
    Config = config_module.Config  # type: ignore


class DataVerificationTest(unittest.TestCase):
    """Verify that data returned by API endpoints matches database tables."""

    BASE_URL = "http://localhost:5001"

    def setUp(self):
        self.session = requests.Session()
        # Ensure application is running
        try:
            resp = self.session.get(self.BASE_URL, timeout=5)
            if resp.status_code != 200:
                self.skipTest("Application not running on port 5001")
        except requests.RequestException:
            self.skipTest("Application not running on port 5001")
        # Ensure database connection works
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
        except Exception:
            self.skipTest("Database not available")

    def _get_connection(self):
        return psycopg2.connect(
            Config.DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor
        )

    def _query(self, query, params=None):
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params or [])
                return cur.fetchall()

    # --- Market Movers ---
    def test_market_movers_matches_table(self):
        rows = self._query(
            "SELECT symbol, type, change_percent, price, volume, timestamp FROM market_movers ORDER BY timestamp DESC"
        )
        gainers, losers = [], []
        for row in rows:
            item = {
                "symbol": row["symbol"],
                "type": row["type"].lower() if row["type"] else "unknown",
                "change_percent": row["change_percent"],
                "price": row["price"],
                "volume": row["volume"],
                "timestamp": row["timestamp"].isoformat() if row["timestamp"] else None,
            }
            if row["type"] == "GAINER":
                gainers.append(item)
            elif row["type"] == "LOSER":
                losers.append(item)
        gainers.sort(key=lambda x: x["change_percent"], reverse=True)
        losers.sort(key=lambda x: x["change_percent"])
        expected = {
            "gainers": gainers[:3],
            "losers": losers[:3],
            "total_gainers": len(gainers),
            "total_losers": len(losers),
        }
        resp = self.session.get(f"{self.BASE_URL}/api/market_movers", timeout=10)
        self.assertEqual(resp.status_code, 200)
        api_data = resp.json().get("data", {})
        self.assertEqual(api_data.get("total_gainers"), expected["total_gainers"])
        self.assertEqual(api_data.get("total_losers"), expected["total_losers"])
        self.assertEqual(api_data.get("gainers"), expected["gainers"])
        self.assertEqual(api_data.get("losers"), expected["losers"])

    # --- Opportunities ---
    def _get_opportunities_from_table(self, table):
        rows = self._query(
            f"SELECT opportunities FROM {table} ORDER BY timestamp DESC LIMIT 1"
        )
        if not rows:
            return []
        opps = rows[0]["opportunities"]
        if isinstance(opps, str):
            try:
                opps = json.loads(opps)
            except json.JSONDecodeError:
                opps = []
        return opps or []

    def _verify_opportunities(self, endpoint, table):
        table_opps = self._get_opportunities_from_table(table)
        resp = self.session.get(f"{self.BASE_URL}{endpoint}", timeout=10)
        self.assertEqual(resp.status_code, 200)
        api_json = resp.json()
        if "data" in api_json and isinstance(api_json["data"], dict) and "opportunities" in api_json["data"]:
            api_opps = api_json["data"]["opportunities"]
        elif "opportunities" in api_json:
            api_opps = api_json["opportunities"]
        else:
            self.fail("API response missing opportunities field")
        self.assertEqual(len(api_opps), len(table_opps))
        if api_opps and table_opps:
            self.assertEqual(api_opps[0], table_opps[0])

    def test_news_opportunities_matches_table(self):
        self._verify_opportunities(
            "/api/news_opportunities", "preloaded_news_opportunities"
        )

    def test_watchlist_opportunities_matches_table(self):
        self._verify_opportunities(
            "/api/watchlist_opportunities", "preloaded_watchlist_opportunities"
        )


if __name__ == "__main__":
    unittest.main()
