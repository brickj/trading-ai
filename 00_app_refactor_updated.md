# App Refactoring Plan - UPDATED (Based on Actual Codebase)

## 1. Goals

### **PRIMARY OBJECTIVE: Enable UI Consultant Collaboration**
**Goal**: Separate frontend and backend so a UI consultant can work on the frontend without access to proprietary backend code.

### **Specific Requirements:**
- **Frontend Repository**: Contains ONLY UI code (templates, CSS, JavaScript, API client)
- **Backend Repository**: Contains ALL business logic, algorithms, database access, API keys
- **Communication**: Frontend → Backend via HTTP API calls only
- **Consultant Access**: Frontend repo + API documentation + staging backend instance
- **Security**: Consultant never sees backend source code or production data

### **Business Benefits:**
- Consultant can work independently on UI improvements
- Proprietary trading algorithms remain protected
- Clear separation of concerns for future development
- Maintain existing functionality with minimal downtime

## 2. ACTUAL Current State (Based on Reading the Code)

### **What's Already Done:**
- ✅ **Route Modularization COMPLETE**: `app.py` is only 47 lines (factory function only)
- ✅ **70 route decorators** across **13 blueprint files** (analysis, backtest, system, page, telegram, logging, dashboard, market, admin, report, opportunity, recommendation, portfolio)
- ✅ **Service Layer EXISTS**: 4 services implemented (`AnalysisService`, `BacktestService`, `DataService`, `ReportService`)
- ✅ **Core modules separated**: `src/core`, `src/data`, `src/trading` are isolated
- ✅ **Blueprint registration**: All routes properly registered in `routes/__init__.py`

### **Current Architecture:**
```
src/
├─ core/           # DB layer, caching, watchlist, telegram, algorithms
├─ data/           # DataFetcher, external APIs
├─ trading/        # Trading strategies
└─ web/
   ├─ app.py       # 47 lines - factory function only
   ├─ routes/      # 13 blueprints with 70 routes
   ├─ services/    # 4 business logic services
   ├─ templates/   # HTML/Jinja templates
   └─ static/      # JS/CSS assets
```

### **Current Coupling Issues:**
- UI modules import core classes directly (`Config`, `RecommendationManager`, `SentimentAnalyzer`)
- Direct DB access through `src.core.database.get_db_connection`
- No HTTP API layer between UI and core
- CORS wildcard, no authentication
- Tight coupling makes testing difficult

## 3. Target Architecture

### **Backend Service (Private - Your Repo)**
```
backend-service/
 ├─ src/core/          # Proprietary algorithms, DB access
 ├─ src/data/          # External API integrations  
 ├─ src/trading/       # Trading strategies
 ├─ src/api/           # REST API endpoints
 ├─ database/          # DB schema, migrations
 └─ config/            # API keys, secrets, environment
```

### **Frontend Repository (Public - Consultant Access)**
```
frontend/
 ├─ templates/         # HTML/Jinja templates
 ├─ static/           # CSS, JavaScript, images
 ├─ src/api_client/   # HTTP client for backend API
 ├─ src/routes/       # Thin Flask routes (API calls only)
 └─ requirements.txt  # Minimal dependencies
```

### **Key Separation Principles:**
- **Backend**: Contains ALL business logic, database access, API keys, algorithms
- **Frontend**: Contains ONLY UI code, templates, static assets, API client
- **Communication**: Frontend → Backend via HTTP API calls only
- **Consultant Access**: Frontend repo + API documentation + test backend instance

## 4. Backend API Contract (OpenAPI Specification)

### **Complete API Endpoints for Frontend**
```yaml
# Backend Service API (http://backend-service:5000/api)
paths:
  # Analysis Endpoints
  /api/analysis/stock:        {post: {symbol, analysis_type?}}
  /api/analysis/bulk:         {post: {symbols[], analysis_type?}}
  /api/analysis/sp500:       {get: {limit?, refresh?}}
  /api/analysis/crypto:      {get: {refresh?}}
  /api/analysis/enhanced:    {post: {symbol}}
  
  # Trading & Opportunities
  /api/scalping/opportunities: {get: {limit?, refresh?}}
  /api/opportunities/watchlist: {get: {limit?}}
  /api/opportunities/news:    {get: {limit?}}
  
  # Backtesting
  /api/backtest/run:         {post: {symbol, days_back, initial_capital}}
  /api/backtest/recommendations: {get: {symbol?, days_back?}}
  /api/backtest/results:     {get: {symbol?, limit?}}
  
  # Portfolio & Trading
  /api/portfolio:            {get: {}}
  /api/portfolio/positions:  {get: {}}
  /api/portfolio/trades:     {get: {limit?}}
  
  # System & Reports
  /api/system/status:        {get: {}}
  /api/system/metrics:       {get: {}}
  /api/reports/performance:  {get: {days_back?}}
  /api/reports/logs:         {get: {level?, limit?}}
  
  # Watchlist Management
  /api/watchlist:            {get: {}}
  /api/watchlist/{symbol}:   {get|post|delete}
  
  # Market Data
  /api/market/status:        {get: {}}
  /api/market/movers:        {get: {}}
  /api/market/foreign:       {get: {}}
  /api/market/events:        {get: {weeks_back?, weeks_ahead?}}
```

### **Frontend API Client Interface**
```python
# Frontend will use this client to call backend
class BackendAPIClient:
    def get_portfolio_data(self) -> dict
    def get_analysis_data(self, symbol: str) -> dict
    def get_scalping_opportunities(self) -> list
    def run_backtest(self, symbol: str, days: int) -> dict
    # ... all other API methods
```

## 5. Consultant Collaboration Setup

### **What Consultant Gets:**
- **Frontend repository** (public GitHub repo)
- **API documentation** (OpenAPI spec + Postman collection)
- **Test backend instance** (staging environment)
- **Mock data responses** for development
- **Development guide** with setup instructions

### **What Consultant Does NOT Get:**
- Backend source code
- Database access
- API keys or secrets
- Production environment access
- Proprietary algorithms

### **Security & Access:**
- **API Authentication**: Bearer tokens for backend access
- **CORS**: Backend only allows frontend domain(s)
- **Rate Limiting**: Prevents abuse of backend API
- **Environment Variables**: All secrets in backend only
- **Staging Backend**: Consultant gets test instance with sample data

## 6. UPDATED Migration Phases

| Phase | Focus | Key Actions | Status |
|-------|-------|-------------|--------|
|~~0. Inventory~~|~~Tag files as UI vs Core~~|~~Identify modules to move~~|✅ **COMPLETE** |
|~~1. Route Modularization~~|~~Move routes out of app.py~~|~~Create blueprints and register routes~~|✅ **COMPLETE** |
|~~2. Service Layer~~|~~Isolate business logic~~|~~Create service classes~~|✅ **MOSTLY COMPLETE** |
|3. Backend Service Creation (Week 1)|Extract backend with API layer|Move `src/core`, `src/data`, `src/trading` to `backend-service`; implement REST API|❌ **NOT STARTED** |
|4. Frontend Repository Creation (Week 1)|Create consultant-accessible frontend|Extract templates/static to `frontend` repo; create API client|❌ **NOT STARTED** |
|5. API Client Implementation (Week 1-2)|Replace direct imports with HTTP calls|Create `BackendAPIClient`; update all routes to use API calls|❌ **NOT STARTED** |
|6. Consultant Setup (Week 2)|Enable consultant collaboration|Create staging backend; API docs; frontend development guide|❌ **NOT STARTED** |
|7. Testing & Validation (Week 2-3)|Ensure separation works|Integration tests; consultant can work independently|❌ **NOT STARTED** |
|8. Production Deployment (Week 3-4)|Deploy separated services|Deploy backend service; update frontend to use production API|❌ **NOT STARTED** |

## 7. Immediate Next Steps (Phase 3-4)

### **Week 1: Backend Service Creation**
1. **Create `backend-service` repository** (private)
2. **Move proprietary modules**: `src/core`, `src/data`, `src/trading` → `backend-service/src/`
3. **Implement REST API layer** in `backend-service/src/api/`
4. **Add authentication** and CORS configuration
5. **Create OpenAPI specification** and Postman collection

### **Week 1: Frontend Repository Creation**
1. **Create `frontend` repository** (public)
2. **Move UI components**: `templates/`, `static/` → `frontend/`
3. **Create `BackendAPIClient`** module for HTTP communication
4. **Extract thin Flask routes** that only call API client
5. **Create development guide** for consultant

### **Week 2: Consultant Setup**
1. **Deploy staging backend** with sample data
2. **Create API documentation** (OpenAPI + Postman)
3. **Set up consultant access** to frontend repo
4. **Test consultant workflow** independently
5. **Create mock data responses** for offline development

## 8. Success Metrics

### **Frontend/Backend Separation:**
- ✅ **Frontend repo** contains ONLY templates, static assets, and API client
- ✅ **Backend repo** contains ALL business logic, database access, and algorithms
- ✅ **No direct imports** between frontend and backend modules
- ✅ **All communication** via HTTP API calls only

### **Consultant Collaboration:**
- ✅ **Consultant can work independently** using only frontend repo
- ✅ **API documentation** complete and accessible
- ✅ **Staging backend** available for testing
- ✅ **Mock data** available for offline development

### **Technical Requirements:**
- ✅ **Backend API** exposes all necessary endpoints
- ✅ **Frontend routes** are thin and only call API client
- ✅ **Authentication** and CORS properly configured
- ✅ **Test coverage** ≥80% for both services

## 9. Risks & Mitigation
| Risk | Impact | Mitigation |
|------|--------|------------|
| Hidden coupling between frontend and backend | Runtime failures | Comprehensive integration testing |
| Increased API call volume | Performance issues | Implement caching and batching |
| Consultant can't work independently | Project delays | Provide staging backend + mock data |
| API authentication complexity | Security issues | Use proven token-based auth libraries |
| Backend API changes break frontend | Development friction | Version API endpoints, maintain backward compatibility |

## 10. Acceptance Criteria

### **Frontend Repository:**
- ✅ Contains ONLY templates, static assets, and API client
- ✅ No direct database access or proprietary algorithms
- ✅ All business logic calls backend via HTTP API
- ✅ Consultant can clone and run independently

### **Backend Repository:**
- ✅ Contains ALL business logic, database access, and algorithms
- ✅ Exposes complete REST API with OpenAPI documentation
- ✅ Implements authentication and CORS properly
- ✅ Provides staging environment for consultant testing

### **Consultant Workflow:**
- ✅ Consultant can access frontend repo without backend access
- ✅ Consultant can develop UI using staging backend or mock data
- ✅ API documentation is complete and up-to-date
- ✅ Frontend changes don't require backend code access
