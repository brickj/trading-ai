# App Refactoring Plan - UPDATED (Based on Actual Codebase)

## 1. Goals
- Extract proprietary algorithms, DB access, and third‑party integrations into a private **core-service**.
- Leave only templates, static assets, and thin Flask routes in a public **app-ui** repo that talks to the core via HTTP.
- Maintain existing functionality with minimal downtime while improving performance and testability.

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
```
core-service (private)
 ├─ src/core, src/data, src/trading, src/utils
 ├─ REST API layer exposing analysis/backtest endpoints
 └─ owns DB schema, API keys, caching, background jobs

app-ui (public)
 ├─ templates, static assets, JS/CSS
 ├─ thin Flask blueprints + core_client
 └─ no direct DB/API access
```

## 4. Interface Contract (OpenAPI outline)
```yaml
paths:
  /analysis/stock:        {post: {symbol}}
  /analysis/bulk:         {post: {symbols[]}}
  /analysis/sp500:       {get: {limit?, refresh?}}
  /analysis/crypto:      {get: {refresh?}}
  /analysis/enhanced:    {post: {symbol}}
  /scalping/opportunities: {get: {}}
  /backtest/run:         {post: {symbol, days_back, initial_capital}}
  /backtest/recommendations: {get: {symbol?, days_back?}}
  /system/status:        {get: {}}
  /watchlist/{symbol}:   {get|post|delete}
```

## 5. Auth & Security Basics
- Short‑lived Bearer tokens issued by core-service
- CORS: core-service only allows UI domain(s)
- Basic IP/token rate limiting and request/response logging
- Secrets via environment variables

## 6. UPDATED Migration Phases

| Phase | Focus | Key Actions | Status |
|-------|-------|-------------|--------|
|~~0. Inventory~~|~~Tag files as UI vs Core~~|~~Identify modules to move~~|✅ **COMPLETE** |
|~~1. Route Modularization~~|~~Move routes out of app.py~~|~~Create blueprints and register routes~~|✅ **COMPLETE** |
|~~2. Service Layer~~|~~Isolate business logic~~|~~Create service classes~~|✅ **MOSTLY COMPLETE** |
|3. Core Extraction (Week 1)|Split repo and expose REST endpoints|Move `src/core`, `src/data`, `src/trading` to new `core-service`; implement REST API layer|❌ **NOT STARTED** |
|4. HTTP Client (Week 1-2)|Add core_client to UI|Create `core_client` module; replace direct imports with HTTP requests|❌ **NOT STARTED** |
|5. Data Layer Optimization (Week 2)|Connection pooling, repositories|Implement `DatabaseConnector`, standardize repositories, add Redis/TTL caching|❌ **NOT STARTED** |
|6. Performance Enhancements (Week 2-3)|Async & batching|Move long I/O tasks to background jobs, optimize SP500 analysis, batch queries|❌ **NOT STARTED** |
|7. Testing & Observability (Week 3)|Quality and monitoring|Unit tests for services/repos, integration tests hitting core API|❌ **NOT STARTED** |
|8. Cutover & Cleanup (Week 3-4)|Flip feature flags, retire legacy code|Remove remaining proprietary logic from UI repo|❌ **NOT STARTED** |

## 7. Immediate Next Steps (Phase 3)

### **Week 1: Core Extraction**
1. **Create `core-service` repository**
2. **Move proprietary modules**: `src/core`, `src/data`, `src/trading` → `core-service/src/`
3. **Implement REST API layer** in `core-service/src/api/`
4. **Add authentication** and CORS configuration
5. **Create OpenAPI specification**

### **Week 1-2: HTTP Client**
1. **Create `core_client` module** in `app-ui/src/web/`
2. **Replace direct imports** with HTTP client calls
3. **Update all route handlers** to use `core_client`
4. **Add error handling** and retry logic
5. **Test integration** between UI and core-service

## 8. Success Metrics
- UI repo contains only templates/static assets and thin Flask glue
- Core-service exposes documented endpoints and passes tests
- UI operates solely through `core_client`
- Secrets managed via env vars
- Test coverage ≥80% for service layer

## 9. Risks & Mitigation
| Risk | Impact | Mitigation |
|------|--------|------------|
| Hidden coupling between UI and core | Runtime failures | Comprehensive integration testing |
| Increased API call volume | Performance issues | Implement caching and batching |
| Authentication complexity | Security issues | Use proven token-based auth libraries |

## 10. Acceptance Criteria
- `app.py` remains <100 lines (currently 47)
- UI repo contains only templates/static assets and thin Flask glue
- Core-service exposes documented endpoints (`openapi.yaml`)
- UI operates solely through `core_client`
- All tests passing after split
- Consultant can develop UI independently using mock core-service
