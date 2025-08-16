# Foreign Markets UI Access & Testing Guide

## **🌍 Pages with Foreign Market Access:**

### **1. Dashboard (`/`) - Main Page**
### **2. Opportunities (`/opportunities`) - Trading Opportunities**  
### **3. Stocks (`/stocks`) - Individual Stock Analysis**
### **4. Portfolio (`/portfolio_page`) - Portfolio Management**
### **5. Recommendations (`/recommendations`) - AI Recommendations**
### **6. System Status (`/system_status`) - System Overview**

---

## **🧪 Foreign Markets Test Checklist:**

### **✅ Test 1: Dashboard Page (`/`)**
- [ ] Navigate to `http://localhost:5001/`
- [ ] Look for foreign stocks in the main dashboard
- [ ] **Verify**: You see stocks like `HSBA.L`, `7203.T`, `SAP.DE` with exchange badges
- [ ] **Check**: Exchange badges show (e.g., "LSE", "JPX", "XETRA")
- [ ] **Check**: Currency badges show (e.g., "GBP", "JPY", "EUR")

### **✅ Test 2: Opportunities Page (`/opportunities`)**
- [ ] Navigate to `http://localhost:5001/opportunities`
- [ ] **Test Market Filter**: Use dropdown to filter by specific markets:
  - [ ] Select "UK" → Should show only `.L` stocks (HSBA.L, BP.L)
  - [ ] Select "Japan" → Should show only `.T` stocks (7203.T, 6758.T)
  - [ ] Select "Germany" → Should show only `.DE` stocks (SAP.DE, BMW.DE)
  - [ ] Select "Canada" → Should show only `.TO` stocks (SHOP.TO, RY.TO)
  - [ ] Select "Hong Kong" → Should show only `.HK` stocks (0700.HK, 0005.HK)
  - [ ] Select "France" → Should show only `.PA` stocks (MC.PA, OR.PA)
- [ ] **Verify Exchange Badges**: Each foreign stock shows exchange name
- [ ] **Verify Currency Badges**: Each foreign stock shows currency code

### **✅ Test 3: Individual Stock Analysis**
- [ ] **Test UK Stock**: Go to `http://localhost:5001/api/analyze_stock` (POST)
  - [ ] Send: `{"symbol": "HSBA.L"}`
  - [ ] **Verify**: Returns analysis with price data and sentiment
- [ ] **Test Japanese Stock**: Send: `{"symbol": "7203.T"}`
  - [ ] **Verify**: Returns analysis with price data and sentiment
- [ ] **Test German Stock**: Send: `{"symbol": "SAP.DE"}`
  - [ ] **Verify**: Returns analysis with price data and sentiment

### **✅ Test 4: Stocks Page (`/stocks`)**
- [ ] Navigate to `http://localhost:5001/stocks`
- [ ] **Search for foreign symbols**:
  - [ ] Search "HSBA.L" → Should find HSBC Holdings
  - [ ] Search "7203.T" → Should find Toyota Motor
  - [ ] Search "SAP.DE" → Should find SAP SE
- [ ] **Verify**: Foreign stocks appear with proper exchange/currency info

### **✅ Test 5: Watchlist Verification**
- [ ] Go to `http://localhost:5001/api/watchlist/config`
- [ ] **Verify**: Foreign symbols are in the stocks array:
  - [ ] `0005.HK`, `0700.HK` (Hong Kong)
  - [ ] `6758.T`, `7203.T` (Japan)
  - [ ] `SAP.DE`, `BMW.DE` (Germany)
  - [ ] `SHOP.TO`, `RY.TO` (Canada)
  - [ ] `HSBA.L`, `BP.L` (UK)
  - [ ] `MC.PA`, `OR.PA` (France)
  - [ ] `ASML.AS` (Netherlands)
  - [ ] `VALE3.SA` (Brazil)
  - [ ] `TSM` (Taiwan)

### **✅ Test 6: Price Data Fallback Test**
- [ ] **Test Alpha Vantage Coverage**: Use symbols Alpha Vantage covers
  - [ ] `HSBA.L` (UK) → Should work via Alpha Vantage
  - [ ] `SAP.DE` (Germany) → Should work via Alpha Vantage
- [ ] **Test yfinance Fallback**: Use symbols Alpha Vantage misses
  - [ ] `7203.T` (Japan) → Should fallback to yfinance
  - [ ] `0700.HK` (Hong Kong) → Should fallback to yfinance

### **✅ Test 7: UI Badge Display**
- [ ] **Check Exchange Badges**: Look for these specific badges:
  - [ ] **LSE** (for `.L` stocks)
  - [ ] **JPX** (for `.T` stocks) 
  - [ ] **XETRA** (for `.DE` stocks)
  - [ ] **TSX** (for `.TO` stocks)
  - [ ] **HKEX** (for `.HK` stocks)
  - [ ] **Euronext** (for `.PA` stocks)
- [ ] **Check Currency Badges**: Look for these currencies:
  - [ ] **GBP** (UK), **JPY** (Japan), **EUR** (Germany/France)
  - [ ] **CAD** (Canada), **HKD** (Hong Kong)

---

## **🚨 Expected Results:**
- **28 total stocks** in watchlist (including 15 foreign + 13 US)
- **Exchange/currency badges** visible on all foreign stocks
- **Market filter** working on Opportunities page
- **Price data** available for all foreign symbols
- **Analysis API** returning data for foreign stocks

## **🔧 Quick Verification Command:**
```bash
# Check total watchlist count
curl "http://localhost:5001/api/watchlist/config" | grep -o '"stocks": \[.*\]' | wc -w

# Should show 28 stocks total
```

## **🌍 Foreign Markets Added:**

### **🇬🇧 UK (LSE)** - `.L` suffix
- `HSBA.L` - HSBC Holdings
- `BP.L` - BP plc

### **🇯🇵 Japan (JPX)** - `.T` suffix  
- `7203.T` - Toyota Motor
- `6758.T` - Sony Group

### **🇩🇪 Germany (XETRA)** - `.DE` suffix
- `SAP.DE` - SAP SE
- `BMW.DE` - BMW Group

### **🇨🇦 Canada (TSX)** - `.TO` suffix
- `SHOP.TO` - Shopify
- `RY.TO` - Royal Bank of Canada

### **🇭🇰 Hong Kong (HKEX)** - `.HK` suffix
- `0700.HK` - Tencent
- `0005.HK` - HSBC Holdings

### **🇫🇷 France (Euronext)** - `.PA` suffix
- `MC.PA` - LVMH
- `OR.PA` - L'Oréal

### **🇳🇱 Netherlands (AMS)** - `.AS` suffix
- `ASML.AS` - ASML Holding

### **🇧🇷 Brazil (B3)** - `.SA` suffix
- `VALE3.SA` - Vale SA

### **🇹🇼 Taiwan** - No suffix
- `TSM` - Taiwan Semiconductor

## **💡 Data Sources:**
- **Alpha Vantage**: Covers UK, Germany, Canada, France, Netherlands, Brazil, Taiwan
- **yfinance Fallback**: Covers Japan, Hong Kong, Australia, South Korea, Switzerland, India
- **Automatic Fallback**: When Alpha Vantage fails, yfinance automatically provides data

---

**Run through this checklist to verify all foreign markets are working correctly!** 🚀
