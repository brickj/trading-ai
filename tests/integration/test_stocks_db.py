"""Integration tests for stocks page database functionality."""
import json
import pytest
from datetime import datetime, timedelta

# Test data
SAMPLE_MARKET_MOVERS = [
    {
        'symbol': 'AAPL',
        'type': 'GAINER',
        'price': 150.25,
        'change_amount': 2.50,
        'change_percent': 1.69,
        'volume': 1000000,
        'analysis_data': {
            'symbol': 'AAPL',
            'company_name': 'Apple Inc.',
            'sector': 'Technology',
            'recommendation': 'BUY',
            'confidence': 0.85
        }
    },
    {
        'symbol': 'MSFT',
        'type': 'GAINER',
        'price': 300.50,
        'change_amount': 4.25,
        'change_percent': 1.43,
        'volume': 2000000,
        'analysis_data': {
            'symbol': 'MSFT',
            'company_name': 'Microsoft Corporation',
            'sector': 'Technology',
            'recommendation': 'HOLD',
            'confidence': 0.75
        }
    },
    {
        'symbol': 'TSLA',
        'type': 'LOSER',
        'price': 250.75,
        'change_amount': -5.25,
        'change_percent': -2.05,
        'volume': 3000000,
        'analysis_data': {
            'symbol': 'TSLA',
            'company_name': 'Tesla Inc.',
            'sector': 'Consumer Cyclical',
            'recommendation': 'SELL',
            'confidence': 0.65
        }
    }
]

class TestStocksPageDB:
    """Test suite for stocks page database functionality."""

    def test_market_movers_endpoint(self, test_client, db_connection):
        """Test the /api/preloaded_data endpoint returns correct market movers."""
        # Insert test data
        with db_connection.cursor() as cur:
            cur.execute("TRUNCATE TABLE market_movers CASCADE")
            
            for mover in SAMPLE_MARKET_MOVERS:
                cur.execute("""
                    INSERT INTO market_movers 
                    (symbol, type, price, change_amount, change_percent, volume, analysis_data)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    mover['symbol'],
                    mover['type'],
                    mover['price'],
                    mover['change_amount'],
                    mover['change_percent'],
                    mover['volume'],
                    json.dumps(mover['analysis_data'])
                ))
            db_connection.commit()

        # Test API endpoint
        response = test_client.get('/api/preloaded_data')
        assert response.status_code == 200
        data = response.get_json()
        
        # Verify response structure
        assert 'data' in data
        assert 'enhanced_analysis' in data['data']
        assert isinstance(data['data']['enhanced_analysis'], list)
        
        # Verify data integrity
        for i, mover in enumerate(SAMPLE_MARKET_MOVERS):
            api_mover = data['data']['enhanced_analysis'][i]
            assert api_mover['symbol'] == mover['symbol']
            assert float(api_mover['price']) == pytest.approx(mover['price'])
            assert float(api_mover['change_percent']) == pytest.approx(mover['change_percent'])

    def test_stocks_page_rendering(self, test_client, db_connection):
        """Test that the stocks page renders market data correctly."""
        # Insert test data
        with db_connection.cursor() as cur:
            cur.execute("TRUNCATE TABLE market_movers CASCADE")
            
            for mover in SAMPLE_MARKET_MOVERS:
                cur.execute("""
                    INSERT INTO market_movers 
                    (symbol, type, price, change_amount, change_percent, volume, analysis_data)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    mover['symbol'],
                    mover['type'],
                    mover['price'],
                    mover['change_amount'],
                    mover['change_percent'],
                    mover['volume'],
                    json.dumps(mover['analysis_data'])
                ))
            db_connection.commit()

        # Test page rendering
        response = test_client.get('/stocks')
        assert response.status_code == 200
        html = response.data.decode('utf-8')
        
        # Check that all test symbols are in the response
        for mover in SAMPLE_MARKET_MOVERS:
            assert mover['symbol'] in html
            
            # Check that price and change are properly formatted
            if mover['change_percent'] > 0:
                assert f"+{mover['change_percent']:.2f}%" in html
            else:
                assert f"{mover['change_percent']:.2f}%" in html

    def test_empty_market_movers(self, test_client, db_connection):
        """Test behavior when no market movers are available."""
        # Clear the test data
        with db_connection.cursor() as cur:
            cur.execute("TRUNCATE TABLE market_movers CASCADE")
            db_connection.commit()
        
        # Test API endpoint with no data
        response = test_client.get('/api/preloaded_data')
        assert response.status_code == 200
        data = response.get_json()
        
        assert data['data']['enhanced_analysis'] == []
        assert data['data']['total_analyzed'] == 0
        assert data['data']['opportunities_found'] == 0
