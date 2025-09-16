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

> **Implementation note:** Start by covering the handful of endpoints the existing UI actually calls today (analysis detail, watchlist, opportunities, backtest results, portfolio overview). Treat the rest of the wishlist above as backlog items that can be exposed iteratively once the core boundary is stable.

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

### **Implementation Principles (keep it simple)**
- Reuse as much of the existing codebase as possible; only introduce new modules when it reduces coupling.
- Ship a thin HTTP layer in front of the existing services instead of rewriting business logic.
- Move files between repos only after the HTTP boundary is in place and verified by the UI.

## 6. Simplified Migration Plan

| Phase | Focus | Why it matters |
|-------|-------|----------------|
|✅ **0. Inventory** | Tag files as UI vs. Core | Already complete — confirms what stays private vs. shareable. |
|✅ **1. Route Modularization** | Keep UI endpoints together | Done — makes it easy to swap data sources later. |
|🟡 **2. Add API Boundary (Week 1)** | Introduce `/api` blueprint that wraps existing services | UI can fetch data only through HTTP; proves separation without moving files yet. |
|⚪ **3. Frontend API Client (Week 1)** | Replace direct imports with HTTP calls | Ensures UI works with the API layer and is ready to live in a separate repo. |
|⚪ **4. Repo Split (Week 2)** | Create `backend-service` (private) and `frontend-ui` (shareable) repos | Move only after UI runs fully on the API. |
|⚪ **5. Consultant Enablement (Week 2)** | Staging backend, docs, mock data | Lets consultant work without backend access. |
|⚪ **6. Hardening & Deploy (Week 3)** | Automated tests, monitoring, production rollout | Final polish before handing off to consultant. |

### **Phase 2 – Add API Boundary (Week 1)**
1. Introduce a dedicated `/api` blueprint in the current repo.
2. Expose read/write methods that the templates need by calling existing services (`AnalysisService`, `BacktestService`, etc.).
3. Implement request/response schemas (pydantic or dataclasses) for consistent payloads.
4. Lock down cross-origin access to only the planned frontend origin(s).

### **Phase 3 – Frontend API Client (Week 1)**
1. Build a `BackendAPIClient` that wraps HTTP calls (requests or httpx).
2. Update each blueprint in `src/web/routes` to call the client instead of importing core modules.
3. Provide simple fixtures or mock responses so UI can be exercised when the backend is offline.
4. Once all routes depend on the client, mark direct imports from `src/core`, `src/data`, and `src/trading` as deprecated.

### **Phase 4 – Repo Split (Week 2)**
1. Create the private `backend-service` repo and move the proprietary packages (`src/core`, `src/data`, `src/trading`, plus the new `/api` blueprint).
2. Keep the Flask UI (templates, static assets, thin routes, and the API client) in a new `frontend-ui` repo.
3. Replace local imports between repos with pip-installable packages or a git submodule during transition (short-term vendor folder works).
4. Add CI that runs UI integration tests against a staged backend container.

### **Phase 5 – Consultant Enablement (Week 2)**
1. Publish the OpenAPI schema and a Postman collection generated from the `/api` blueprint.
2. Spin up a staging backend (Docker compose or managed service) with anonymized/sample data.
3. Document how to point the frontend at staging vs. production via `.env` or config file.
4. Provide JSON fixtures so the consultant can run UI pages without live services when needed.

### **Phase 6 – Hardening & Deploy (Week 3)**
1. Add automated integration tests that hit the HTTP boundary.
2. Enable authentication/authorization (Bearer tokens or session cookies) and tighten CORS.
3. Roll production to the new backend service, update DNS/env vars on the frontend, and monitor.
4. Schedule periodic contract tests to catch breaking API changes early.

## 7. Success Metrics

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

## 8. Risks & Mitigation
| Risk | Impact | Mitigation |
|------|--------|------------|
| Hidden coupling between frontend and backend | Runtime failures | Comprehensive integration testing |
| Increased API call volume | Performance issues | Implement caching and batching |
| Consultant can't work independently | Project delays | Provide staging backend + mock data |
| API authentication complexity | Security issues | Use proven token-based auth libraries |
| Backend API changes break frontend | Development friction | Version API endpoints, maintain backward compatibility |

## 9. Acceptance Criteria

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
