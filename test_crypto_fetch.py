from src.data.data_fetcher import DataFetcher

data_fetcher = DataFetcher()

for symbol in ['BTC', 'ETH', 'SOL', 'USDT']:
    try:
        price_data = data_fetcher.get_crypto_price(symbol)
        price = price_data.get('current_price', 0)
        change = price_data.get('change_24h', 0)
        market_cap = price_data.get('market_cap', 0)
        print(f'{symbol}: Price=${price:,.2f}, Change={change:.2f}%, Market Cap=${market_cap:,.0f}')
    except Exception as e:
        print(f'{symbol}: Error - {e}') 