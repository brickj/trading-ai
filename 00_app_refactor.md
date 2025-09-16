# App Refactoring & Service Split Plan (Unified)

## 1. Goals
- Detangle the monolithic `app.py` (5k+ lines) into modular blueprints, services, and repositories.
- Extract proprietary algorithms, DB access, and third‑party integrations into a private **core-service**.
- Leave only templates, static assets, and thin Flask routes in a public **app-ui** repo that talks to the core via HTTP.
- Maintain existing functionality with minimal downtime while improving performance and testability.

## 2. Current State Mapping (UPDATED - Based on Actual Code)
- **Proprietary modules**
  - `src/core` – DB layer, caching, watchlist, telegram, and low-level helpers (`db_utils`, `cache`, etc.).
  - `src/data` – `DataFetcher` and external market/news APIs.
  - `src/trading` – `trading_strategy.py`, `enhanced_trading_strategy.py` and related logic.
- **UI modules (ALREADY MODULARIZED)**
  - `src/web/app.py` – **47 lines** - just factory function, NO routes embedded
  - `src/web/routes/*` – **13 blueprints** with **70 route decorators** covering all endpoints
  - `src/web/services` – **4 services implemented**: `AnalysisService`, `BacktestService`, `DataService`, `ReportService`
  - `src/web/helpers.py`, `src/web/repositories`, `src/web/utils` – direct DB access via `src.core.database.get_db_connection`
  - Templates & static files under `src/web/templates` and `src/web/static`.
- **Current coupling & gaps**
  - UI modules import core classes directly (`Config`, `RecommendationManager`, `SentimentAnalyzer`, etc.)
  - Direct DB access through shared helpers instead of HTTP API
  - CORS remains wildcard; no token-based auth or rate limiting implemented yet
  - **ROUTE MODULARIZATION IS COMPLETE** - all endpoints moved to blueprints

## 3. Target Architecture
```
core-service (private)
 ├─ src/core, src/data, src/trading, src/utils
 ├─ REST API layer exposing analysis/backtest endpoints
 └─ owns DB schema, API keys, caching, background jobs

app-ui (shared)
 ├─ templates, static assets, JS/CSS
 ├─ thin Flask blueprints + `core_client`
 └─ no direct DB/API access

(optional) app-api
 └─ small public CRUD service if needed
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
Responses are JSON with `{error: string}` on failure.

## 5. Auth & Security Basics
- Short‑lived Bearer or HMAC tokens issued by core-service; UI sends `Authorization` header.
- CORS: core-service only allows UI domain(s); block wildcard.
- Basic IP/token rate limiting and request/response logging.
- Secrets via environment variables (`.env`, not committed); none in client JS.

## 6. Refactoring & Migration Phases
| Phase | Focus | Key Actions |
|-------|-------|-------------|
|0. Inventory|Tag files as UI vs Core|Identify modules to move; mark remaining 54 routes in `app.py`|
|1. Route Modularization (Week 1‑2)|Finish moving routes out of `app.py`|Audit existing blueprints (analysis, backtest, system, page, telegram, logging) and migrate remaining endpoints—dashboard, market movers, portfolio, foreign markets, news, watchlist, recommendations, opportunities, etc.—into dedicated blueprints; update `routes/__init__.py`|
|2. Service Layer Completion (Week 2‑3)|Isolate business logic|Harden current services (`AnalysisService`, `BacktestService`, `DataService`, `ReportService`) and add the missing `dashboard`, `market`, `portfolio`, `news`, and `recommendation` services; introduce dependency injection|
|3. Core Extraction & HTTP Client (Week 3‑4)|Split repo and expose REST endpoints|Move proprietary modules to new `core-service`; implement API layer; add `core_client` in UI; replace direct imports (`Config`, `RecommendationManager`, DB helpers, etc.) and SQL calls with HTTP requests|
|4. Data Layer Optimization (Week 4)|Connection pooling, repositories, caching|Implement `DatabaseConnector`, standardize repositories, add Redis/TTL caching, eliminate duplicate queries|
|5. Performance Enhancements (Week 4‑5)|Async & batching|Move long I/O tasks to background jobs, optimize SP500 analysis, batch queries, add in-memory caches|
|6. Testing & Observability (Week 5‑6)|Quality and monitoring|Unit tests for services/repos, integration tests hitting core API, logging & timing metrics, fix missing deps (`lxml`, XML parser)|
|7. Cutover & Cleanup (Week 6)|Flip feature flags, retire legacy code|Remove remaining proprietary logic from UI repo, finalize OpenAPI spec and docs|

## 7. Repo Layout & Key Files
`core-service/`
```
src/
  core/        # DB access, caching, logger, watchlist, telegram
  data/        # DataFetcher, news/historical jobs
  trading/     # Strategies and algorithms
  api/         # REST endpoints (analysis, backtest, scalping…)
  utils/       # job scheduler, postgres setup
tests/
openapi.yaml
.env.example    # DB_URL, API keys, token secret
docker-compose.yml
```

`app-ui/`
```
src/web/
  routes/      # thin blueprints calling core_client
  templates/   # HTML/Jinja templates
  static/      # JS/CSS assets
  core_client/ # wrapper around core-service REST API
tests/
openapi.yaml    # paths used by UI
.env.example    # CORE_BASE_URL, UI token, etc.
docker-compose.yml
```

## 8. Local & Staging Workflows
- **Local**: `docker-compose` can run UI + mock core for consultants. Swap in private core image by changing `CORE_BASE_URL`.
- **Staging**: UI points to remote core over HTTPS with short-lived tokens. CORS allows only staging UI domain. Use dev proxy to avoid localhost HTTPS issues.

## 9. Data & DB Safety
- Provide masked/anonymized datasets; remove production keys.
- Core-service uses least-privilege Postgres role.
- All DB access lives inside core-service; UI accesses data only via HTTP.
- Document required env vars in `.env.example`.

## 10. Risks & Effort
| Risk | Impact | Effort |
|------|--------|-------|
|Hidden coupling between UI and core modules|Runtime failures after split|Medium|
|DB logic or tokens embedded in templates|Security leakage|Small|
|Increased API call volume via proxy|Potential rate limits|Medium|
|Consultant requires additional endpoints|Scope creep|Medium‑High|

## 11. Acceptance Criteria
- `app.py` reduced to <2,500 lines with remaining routes delegated to blueprints and services.
- UI repo contains only templates/static assets and thin Flask glue; no proprietary logic or DB/API access.
- Core-service exposes documented endpoints (`openapi.yaml`) and passes unit/integration tests.
- UI operates solely through `core_client`; feature flags allow gradual cutover.
- Secrets managed via env vars; CI pipelines green for both repos.
- Consultant can develop UI independently using mock or staged core-service.

## 12. Success Metrics
- Lines in `app.py` <2,500 and cyclomatic complexity ↓40%.
- SP500 analysis response time <30 s; market_movers <2 s; dashboard load <3 s.
- Test coverage ≥80% for service layer; all tests passing after split.

