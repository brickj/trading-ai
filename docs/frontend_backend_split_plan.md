# Frontend/Backend Repository Split Plan

## 1. Executive Summary
- **Goal**: Separate the monolithic Trading AI project into two independently deployable repositories: a Flask-based backend API/service repo and a front-end UI repo.
- **Difficulty**: **High (≈4/5)**. The current Flask app intertwines server-rendered templates, Socket.IO streaming, Redis/PostgreSQL caches, and ~80 REST endpoints, so the split requires careful untangling of routing, shared helpers, and deployment scripts.
- **Key Risks**: Maintaining API parity for existing JavaScript clients, replacing Flask template rendering, coordinating WebSocket events (`analysis_progress`, `watchlist_progress`, `sp500_progress`), and preserving the job scheduler/Go subprocess integrations.

## 2. Current Architecture Assessment
- **Backend logic** lives in `src/core`, `src/data`, and `src/trading` packages. Flask routes import these services directly via central dependency wiring (`src/web/dependencies.py`).【F:src/web/dependencies.py†L1-L26】
- **Flask web layer** (`src/web`) combines page routes that render Jinja templates with API routes returning JSON. `register_routes` wires 15+ blueprints and emits Socket.IO events from route handlers.【F:src/web/routes/__init__.py†L1-L40】【F:src/web/routes/opportunity_routes.py†L1-L110】【F:src/web/routes/opportunity_routes.py†L200-L302】
- **Front-end assets**: Jinja templates in `src/web/templates` and static JS/CSS in `src/web/static`. JavaScript code assumes same-origin endpoints (`fetch('/api/...')`) and consumes structured responses from helper utilities (`create_api_response`).【F:src/web/static/js/dashboard.js†L1-L88】【F:src/web/helpers.py†L1-L76】
- **Startup orchestration**: `start_app.py` bootstraps env variables, schedulers, dependency checks, and launches the Flask/Socket.IO server in-process. It couples web serving with background jobs and service health checks.【F:start_app.py†L1-L120】
- **External dependencies**: PostgreSQL (via `src/core/database.py`), Redis cache, APScheduler jobs, and optional Go sentiment optimizer invoked from Python services. These belong with the backend service.

## 3. Separation Challenges
1. **Template Rendering vs API Responses**: Page blueprints (`page_routes.py`, `backtest_routes.py`, etc.) render templates. After separation, the front-end repo must replace these Jinja views with a static build (React/Vue or vanilla JS) that calls the backend API endpoints. Navigation logic embedded in templates (e.g., `navbar.html`) must be reimplemented client-side.【F:src/web/routes/page_routes.py†L1-L183】【F:src/web/templates/navbar.html†L1-L160】
2. **Shared Helpers**: Helpers (`src/web/helpers.py`, `src/web/utils/*`) and repositories are imported by API routes and front-end templates. Backend-only logic (formatters, DB access) must stay with the API; UI-specific utilities (DOM manipulation, CSS) move to the front-end.
3. **Socket.IO/WebSocket Events**: Real-time progress updates are emitted directly from Flask routes (`socketio.emit`). A standalone backend must continue emitting these events; the front-end repo must connect via an environment-configurable Socket.IO URL and handle CORS credentials.【F:src/web/static/js/base.js†L100-L118】【F:src/web/routes/opportunity_routes.py†L250-L302】
4. **Scheduler & Background Jobs**: `start_app.py` spawns APScheduler tasks alongside the Flask app. Backend deployment scripts must preserve this lifecycle, while the front-end repo should drop scheduler concerns.
5. **Go Integration & Batch Processor**: Routes trigger Go services and CPU-heavy batch processing (`src/core/go_services.py`, `src/core/batch_processor.py`). These remain backend responsibilities, but API contracts must expose progress/state so the new front-end can display results without template coupling.

## 4. Proposed Split Plan
### Phase 0 – Discovery & Contract Freezing
1. **Endpoint Inventory**: Export a list of all API routes (~81) and classify by purpose (analysis, portfolio, admin, etc.). Capture request/response schemas by sampling code paths and JSON helpers.【F:src/web/routes/analysis_routes.py†L1-L120】
2. **WebSocket Event Map**: Document every emitted event name, payload shape, and triggering workflow (`analysis_progress`, `watchlist_progress`, `sp500_progress`).
3. **UI Feature Catalog**: For each template (dashboard, opportunities, portfolio, etc.), map which endpoints it consumes and any inline logic.
4. **Shared Asset Audit**: Identify static assets that can be reused directly (CSS, icons) vs. those needing refactoring (Jinja macros, template inheritance).
5. **Config & Secrets Review**: List environment variables and config files consumed by the web layer (`Config`, `.env`, `config/secrets.yaml`). Decide which belong to backend vs. front-end build tooling.

### Phase 1 – Backend Extraction
1. **Create `trading-ai-backend` repo** containing:
   - `src/core`, `src/data`, `src/trading`, and a renamed `src/api` (former `src/web` minus templates/static).
   - `start_backend.py` derived from `start_app.py` (strip UI-specific checks, keep scheduler, CORS/Socket.IO configuration).
   - Requirements, Dockerfile, and CI pipeline tailored to API service.
2. **Refactor Flask blueprints**:
   - Remove template-rendering routes or convert them to JSON metadata endpoints consumed by the front-end.
   - Consolidate helper utilities into backend-specific modules (e.g., move `create_api_response` under `src/api/utils`).
3. **CORS & Socket.IO Configuration**: Parameterize allowed origins and Socket.IO namespaces to accept requests from the new front-end domain(s).【F:src/web/extensions.py†L1-L73】
4. **API Schema Contracts**: Freeze response formats (success/error envelope) and publish OpenAPI/JSON Schema definitions for front-end integration.
5. **Automated Tests**: Add endpoint tests to ensure behavior parity before and after the split (use pytest + Flask test client), including WebSocket event smoke tests.

### Phase 2 – Front-end Repo Creation
1. **Scaffold `trading-ai-frontend`** with a modern build tool (e.g., Vite + React) or a lightweight static site generator if React is overkill. Import existing CSS/JS assets as interim modules.
2. **Port Templates to Components/Pages**:
   - Translate Jinja templates (`src/web/templates/*.html`) into front-end views.
   - Reimplement navbar/layout currently handled by `base.html` and `navbar.html`.
3. **API Client Layer**:
   - Build a wrapper for calling backend endpoints with a configurable base URL and shared error handling consistent with `create_api_response`.
   - Implement WebSocket client(s) for progress updates using `socket.io-client`.
4. **State Management**: Reproduce dashboard state machines currently embedded in vanilla JS (`dashboard.js`, `opportunities.js`, `stocks.js`). Ensure event-driven flows for bulk analysis and progress bars are preserved.【F:src/web/static/js/opportunities.js†L520-L612】
5. **Environment & Build Config**: Introduce `.env` variables for `VITE_API_BASE_URL`, `VITE_SOCKET_URL`, etc. Provide separate dev/prod configurations pointing to backend deployments.
6. **Testing & Linting**: Add unit/UI tests (Jest/Cypress) focusing on API integration and WebSocket interactions.

### Phase 3 – Cross-Repo Integration
1. **CI/CD Coordination**: Establish pipelines that build and test each repo independently, then run integration smoke tests that spin up backend + front-end to ensure compatibility.
2. **Versioned API Releases**: Adopt semantic versioning for backend API. Publish changelog so front-end can align.
3. **Shared Types/SDK (Optional)**: If response contracts are complex, generate a shared TypeScript/Pydantic schema package published to an internal registry to prevent drift.
4. **Infrastructure Updates**: Update deployment scripts (Docker Compose, Kubernetes, etc.) to run front-end (static hosting/CDN) separately from backend service. Ensure networking, TLS, and CORS policies are configured.
5. **Observability**: Move logging/monitoring responsibilities to the backend service. Front-end should capture client errors and send them to a new telemetry endpoint or external service.

### Phase 4 – Decommission Monolith
1. **Gradual Rollout**: Deploy backend repo first, pointing old Flask templates to ensure parity. Then switch traffic to new front-end build.
2. **Retire Template Routes**: Once front-end is live, remove template blueprints from backend and delete `templates/` & `static/` directories in backend repo.
3. **Archive Legacy Scripts**: Replace `start_app.py` with new backend service launcher; document migration for developers/operators.

## 5. Risk Mitigation & Recommendations
- **Migration Testing**: Use automated regression tests covering representative symbols, watchlist workflows, and long-running analyses to catch regressions introduced by the split.
- **Incremental Migration**: Consider serving the new front-end from within Flask during transition (via static file route) to validate API compatibility before full repo separation.
- **Documentation**: Provide comprehensive developer docs describing new repo structures, API contracts, and local dev setup (Docker Compose to run backend + front-end together).
- **Operational Playbooks**: Update runbooks for scheduler tasks, Redis/PostgreSQL maintenance, and Go optimizer deployment since these move exclusively to the backend repo.

By following this phased plan, the project can evolve into two focused repositories while minimizing service disruption and preserving the existing analytical capabilities of Trading AI.
