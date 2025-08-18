"""Full application smoke test based on UI walkthrough instructions."""
import unittest
import requests
import socketio


class FullApplicationTest(unittest.TestCase):
    """Smoke test that verifies every major page and feature loads."""

    BASE_URL = "http://localhost:5001"

    def setUp(self):
        self.session = requests.Session()
        try:
            resp = self.session.get(self.BASE_URL, timeout=5)
            if resp.status_code != 200:
                self.skipTest("Application not running on port 5001")
        except requests.exceptions.RequestException:
            self.skipTest("Application not running on port 5001")

    def _get(self, path):
        return self.session.get(f"{self.BASE_URL}{path}")

    def test_01_dashboard_page(self):
        """Home page loads and contains Trading AI branding."""
        resp = self._get("/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Trading AI", resp.text)

    def test_02_stocks_page(self):
        resp = self._get("/stocks")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("S&P 500", resp.text)
        api = self.session.post(f"{self.BASE_URL}/api/analyze_stock", json={"symbol": "AAPL"})
        self.assertEqual(api.status_code, 200)

    def test_03_crypto_page(self):
        resp = self._get("/crypto")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Crypto", resp.text)
        api = self.session.post(f"{self.BASE_URL}/api/crypto_analysis", json={"symbols": ["BTC"]})
        self.assertEqual(api.status_code, 200)

    def test_04_portfolio_page(self):
        resp = self._get("/portfolio_page")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Portfolio", resp.text)
        api = self._get("/api/portfolio")
        self.assertEqual(api.status_code, 200)

    def test_05_opportunities_page(self):
        resp = self._get("/opportunities")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Opportunities", resp.text)
        news = self._get("/api/news_opportunities")
        self.assertEqual(news.status_code, 200)

    def test_06_recommendations_page(self):
        resp = self._get("/recommendations")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Recommendations", resp.text)
        api = self._get("/api/recommendations")
        self.assertEqual(api.status_code, 200)

    def test_07_backtest_page(self):
        resp = self._get("/backtest")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Backtest", resp.text)

    def test_08_system_status_page(self):
        resp = self._get("/system_status")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("System Status", resp.text)
        api = self._get("/api/system_status")
        self.assertEqual(api.status_code, 200)

    def test_09_logs_page(self):
        resp = self._get("/logs")
        if resp.status_code != 200:
            self.skipTest("Logs page unavailable")
        self.assertIn("Logs", resp.text)
        api = self._get("/api/logs")
        self.assertEqual(api.status_code, 200)

    def test_10_reporting_page(self):
        resp = self._get("/reporting")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Reporting", resp.text)

    def test_11_telegram(self):
        resp = self._get("/api/telegram/test")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("working", data)

    def test_12_tier_system(self):
        resp = self._get("/api/tier/status")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("success", data)

    def test_13_job_scheduler(self):
        resp = self._get("/api/job_schedules")
        self.assertEqual(resp.status_code, 200)

    def test_14_real_time_updates(self):
        client = socketio.Client()
        try:
            client.connect(self.BASE_URL)
            connected = True
        except Exception:
            connected = False
        finally:
            if client.connected:
                client.disconnect()
        self.assertTrue(connected, "WebSocket connection failed")

    def test_15_mobile_responsiveness(self):
        resp = self._get("/")
        self.assertIn('<meta name="viewport"', resp.text)

    def test_16_error_handling(self):
        resp = self.session.post(f"{self.BASE_URL}/api/analyze_stock", json={"symbol": "INVALID"})
        self.assertIn(resp.status_code, [200, 400])


if __name__ == "__main__":
    unittest.main()

