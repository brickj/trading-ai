#!/usr/bin/env python3
import requests
import json

def show_foreign_markets():
    print("🌍 Foreign Markets Status Report")
    print("=" * 60)
    
    # Get watchlist opportunities
    try:
        response = requests.get("http://localhost:5001/api/watchlist_opportunities")
        if response.status_code == 200:
            data = response.json()
            opportunities = data['data']['opportunities']
            
            # Filter foreign markets
            foreign_opps = [o for o in opportunities if '.' in o.get('symbol', '')]
            
            print(f"📊 Total Opportunities: {len(opportunities)}")
            print(f"🌍 Foreign Markets: {len(foreign_opps)}")
            print(f"🇺🇸 US Markets: {len(opportunities) - len(foreign_opps)}")
            print()
            
            if foreign_opps:
                print("🌍 FOREIGN MARKET OPPORTUNITIES:")
                print("-" * 60)
                
                # Group by market
                markets = {
                    'UK': [o for o in foreign_opps if o['symbol'].endswith('.L')],
                    'Japan': [o for o in foreign_opps if o['symbol'].endswith('.T')],
                    'Germany': [o for o in foreign_opps if o['symbol'].endswith('.DE')],
                    'Canada': [o for o in foreign_opps if o['symbol'].endswith('.TO')],
                    'Hong Kong': [o for o in foreign_opps if o['symbol'].endswith('.HK')],
                    'France': [o for o in foreign_opps if o['symbol'].endswith('.PA')],
                    'Netherlands': [o for o in foreign_opps if o['symbol'].endswith('.AS')],
                    'Brazil': [o for o in foreign_opps if o['symbol'].endswith('.SA')],
                    'Taiwan': [o for o in foreign_opps if o['symbol'].endswith('.TW') or o['symbol'] == 'TSM']
                }
                
                for market, opps in markets.items():
                    if opps:
                        print(f"\n🇺🇳 {market.upper()}:")
                        for opp in opps:
                            symbol = opp['symbol']
                            price = opp.get('price_data', {}).get('current_price', 'N/A')
                            action = opp.get('signal_data', {}).get('action', 'HOLD')
                            confidence = opp.get('signal_data', {}).get('confidence', 0)
                            
                            # Get exchange and currency
                            if symbol.endswith('.L'):
                                exchange, currency = 'LSE', 'GBP'
                            elif symbol.endswith('.T'):
                                exchange, currency = 'TSE', 'JPY'
                            elif symbol.endswith('.DE'):
                                exchange, currency = 'XETRA', 'EUR'
                            elif symbol.endswith('.TO'):
                                exchange, currency = 'TSX', 'CAD'
                            elif symbol.endswith('.HK'):
                                exchange, currency = 'HKEX', 'HKD'
                            elif symbol.endswith('.PA'):
                                exchange, currency = 'Euronext', 'EUR'
                            elif symbol.endswith('.AS'):
                                exchange, currency = 'AMS', 'EUR'
                            elif symbol.endswith('.SA'):
                                exchange, currency = 'B3', 'BRL'
                            else:
                                exchange, currency = 'NYSE/NASDAQ', 'USD'
                            
                            print(f"  📈 {symbol} | {exchange} | {currency} | ${price} | {action} | {confidence:.1%}")
                
                print("\n" + "=" * 60)
                print("✅ Foreign markets are working in the backend!")
                print("🔧 To see them in the UI: Go to /opportunities and click 'Refresh'")
                
            else:
                print("❌ No foreign market opportunities found")
                
        else:
            print(f"❌ Failed to get opportunities: HTTP {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    show_foreign_markets()

