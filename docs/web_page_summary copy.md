# Trading AI Web Application Overview

## Page Summaries

| Page | Access Point | Purpose & Key Features |
| --- | --- | --- |
| Dashboard | `/` | Landing hub with sticky analysis controls for standard/enhanced runs, progress/status feedback, educational "How it Works" walkthrough, and a built-in debug monitor for AI sentiment runs that draws configuration values from the backend service layer.【F:src/web/routes/page_routes.py†L14-L26】【F:src/web/templates/index.html†L6-L240】 |
| Stocks | `/stocks` | Pulls the latest winners/losers from the database with fallback handling, then renders enhanced analysis summaries, refresh workflows, auto-refresh toggles, and sentiment-driven tables/modals for top movers.【F:src/web/routes/page_routes.py†L29-L97】【F:src/web/templates/stocks.html†L10-L200】 |
| Crypto | `/crypto` | Presents crypto watchlist sentiment controls, dynamic opportunity cards, market overview metrics, distribution charts, and risk guidance tailored to 24/7 trading.【F:src/web/routes/page_routes.py†L100-L106】【F:src/web/templates/crypto.html†L6-L195】 |
| Portfolio | `/portfolio` (`/portfolio_page`) | Simulated portfolio workspace with mock-data warning, add-position workflow, KPI cards, open positions/trades tables, and allocation/performance visualizations.【F:src/web/routes/page_routes.py†L109-L123】【F:src/web/templates/portfolio.html†L6-L220】 |
| Foreign Markets Overview | `/foreign_markets_overview` | Global exchange monitor featuring summary KPIs, regional/status filters, async refresh, modal drill-downs, and links back to opportunities analysis.【F:src/web/routes/page_routes.py†L126-L132】【F:src/web/templates/foreign_markets_overview.html†L6-L200】 |
| Opportunities | `/opportunities` | Real-time opportunity scanner with mode toggles (news vs. watchlist), refreshable feed, debug panel, and configuration cues tied to watchlist settings.【F:src/web/routes/page_routes.py†L138-L148】【F:src/web/templates/opportunities.html†L10-L180】 |
| Weekly Plan | `/weekly_plan` | Calendar-style planner supporting week navigation, multi-filter controls, summary metrics, detailed event tables, and watchlist highlights.【F:src/web/routes/page_routes.py†L151-L156】【F:src/web/templates/weekly_plan.html†L7-L200】 |
| Logs | `/logs` | Operational log console offering extensive filters, auto-refresh, export, modal search, and verbose toggles for deep diagnostics.【F:src/web/routes/page_routes.py†L160-L165】【F:src/web/templates/logs.html†L10-L200】 |
| Recommendations | `/recommendations` | Performance dashboard aggregating KPIs, charts, filterable recommendation tables, and performance summaries for AI strategies.【F:src/web/routes/page_routes.py†L169-L174】【F:src/web/templates/recommendations.html†L10-L200】 |
| Reporting | `/reporting` | Multi-section analytics studio with configurable reporting periods/types, loading states, and rich performance/trading/risk visualizations.【F:src/web/routes/page_routes.py†L178-L183】【F:src/web/templates/reporting.html†L6-L200】 |
| Backtest | `/backtest` | Strategy validation surface that ties into API endpoints for custom/historical runs, surfacing results via dedicated template views.【F:src/web/routes/backtest_routes.py†L29-L66】【F:src/web/templates/backtest.html†L6-L200】 |
| Scalping Signals | `/scalping_signals` | Real-time scalping hub that queries PostgreSQL history, exposes manual/auto API triggers, and renders contextualized signal cards with headlines.【F:src/web/scalping_signals.py†L30-L148】【F:src/web/templates/scalping_signals.html†L19-L200】 |
| System Status | `/system_status` | Health cockpit with refresh/auto-refresh controls, system/database/service KPIs, cache statistics, and operational summaries pulled from service aggregators.【F:src/web/routes/system_routes.py†L28-L76】【F:src/web/templates/system_status.html†L8-L200】 |

---

## Navigation Flow

![Navigation Flow Diagram](./diagram.svg)

<!-- Ensure diagram.svg is located in the same folder as this Markdown file -->

---

## Project Goals & Success Criteria

The refactor aims to improve performance, consistency, and maintainability across the Trading AI web application. Success is measured by achieving CLS < 0.1, Lighthouse scores ≥ 90, and zero UI regressions on the top 10 screens. The goal is to create a unified, responsive experience that scales across desktop and mobile platforms while maintaining the existing functionality and user workflows.

---

## Tech Stack & Run Instructions

**Backend:**
- Python 3.9+ with Flask framework
- PostgreSQL database with Redis caching
- Package manager: pip with virtual environment
- API runs on: `http://localhost:5001`

**Frontend:**
- Bootstrap 5.3+ for UI components
- Vanilla JavaScript (no framework)
- Static assets served by Flask

**Environment Setup:**
```bash
# Backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python start_app.py

# Required .env keys (sample values):
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key
FINNHUB_API_KEY=your_finnhub_key
NEWSAPI_API_KEY=your_newsapi_key
MARKETAUX_API_KEY=your_marketaux_key
OPENAI_API_KEY=your_openai_key
TELEGRAM_API_KEY=your_telegram_key
```

**Mock Data:** Portfolio page (`/portfolio`) and reporting page (`/reporting`) contain inline mock data for demo purposes

---

## Design System Guardrails

**UI Library:** Bootstrap 5.3+ with custom CSS overrides
**Typography:** System fonts (Arial, Helvetica, sans-serif)
**Color Tokens:** 
- Primary: Bootstrap blue (#0d6efd)
- Success: Green (#198754)
- Danger: Red (#dc3545)
- Warning: Yellow (#ffc107)
- Dark: #212529

**Spacing Scale:** Bootstrap's 0.25rem increments (0, 0.25, 0.5, 1, 1.5, 3rem)
**Components to Keep/Refactor:**
- Buttons: Bootstrap button classes with custom hover states
- Tables: Bootstrap table with striped rows and hover effects
- Modals: Bootstrap modal components
- Cards: Bootstrap card components with custom shadows
- Forms: Bootstrap form controls with validation states

---

## Mobile Target Matrix

**iOS:** 14.0+ (iPhone 8 and newer)
**Android:** 8.0+ (API level 26+)
**Device Classes:**
- Small: 320px-480px (phones)
- Medium: 481px-768px (large phones/small tablets)
- Large: 769px+ (tablets/desktop)

**Browsers:** Safari 14+, Chrome 90+, Firefox 88+
**Orientation:** Portrait primary, landscape support for tablets

---

## Accessibility & Performance

**A11y Level:** WCAG 2.1 AA compliance target
**Keyboard Focus:** Visible focus indicators, logical tab order, skip links
**Color Contrast:** Minimum 4.5:1 ratio for normal text, 3:1 for large text
**Performance Budgets:**
- Bundle size: < 500KB initial load
- Time to Interactive (TTI): < 3 seconds
- Largest Contentful Paint (LCP): < 2.5 seconds
- Cumulative Layout Shift (CLS): < 0.1

---

## Routing & State

**Auth Model:** None currently (public application)
**Protected Routes:** None (all routes publicly accessible)
**Global State:** Vanilla JavaScript with localStorage for user preferences
**Caching Strategy:** 
- Redis for API response caching (1 hour TTL)
- Browser localStorage for user settings
- Static asset caching via Flask

**Error/Empty/Loading Patterns:**
- Loading: Bootstrap spinners with "Loading..." text
- Empty states: "No data available" with refresh buttons
- Errors: Toast notifications with retry options
- 404: Custom error page with navigation back to dashboard
