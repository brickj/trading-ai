# Phase 0 Discovery Report - Trading AI Frontend/Backend Split

## Executive Summary
**Discovery completed on:** 2025-10-16  
**Total API Endpoints:** 81  
**Templates:** 21  
**Socket.IO Events:** 3 main events  
**Static Assets:** 7 CSS files, 6 JS files  

## 1. API Endpoint Inventory (81 Total)

### Analysis Routes (7 endpoints)
- `POST /api/analyze_stock` - Single stock analysis
- `POST /api/analyze_bulk` - Bulk stock analysis  
- `GET /api/stock/<symbol>/analysis` - Get cached analysis
- `GET /api/sp500_analysis` - S&P 500 analysis
- `GET /api/crypto_analysis` - Cryptocurrency analysis
- `POST /api/enhanced_analysis` - Enhanced analysis with AI
- `POST /api/comprehensive_analysis` - Comprehensive analysis

### System Routes (12 endpoints)
- `GET /system_status` - System status page
- `GET /api/system_status` - System status API
- `GET /api/system_metrics` - System performance metrics
- `GET /api/news_services/status` - News service status
- `GET /api/logs` - System logs
- `GET/POST /api/logging/verbosity` - Logging configuration
- `POST /api/news_services/toggle` - Toggle news services
- `POST /api/news_services/test` - Test news services
- `GET /api/news_services/config` - News service configuration
- `GET /api/test_foreign_markets` - Foreign markets test
- `GET /api/performance_status` - Performance status

### Opportunity Routes (2 endpoints)
- `GET /api/news_opportunities` - News-driven opportunities
- `GET /api/watchlist_opportunities` - Watchlist opportunities

### Recommendation Routes (4 endpoints)
- `GET /api/recommendations` - Trading recommendations
- `GET /api/recommendations/stats` - Recommendation statistics
- `GET /api/recommendations/metrics` - Recommendation metrics
- `GET /api/test_db` - Database test

### Telegram Routes (7 endpoints)
- `GET /api/telegram/test` - Telegram test
- `POST /api/telegram/toggle` - Toggle Telegram
- `POST /api/telegram/send_test` - Send test message
- `GET /api/telegram/chat_ids` - Get chat IDs
- `POST /api/telegram/add_chat_id` - Add chat ID
- `POST /api/telegram/remove_chat_id` - Remove chat ID
- `POST /api/telegram/send_raw_message` - Send raw message

### Redis Routes (4 endpoints)
- `GET /api/redis/health` - Redis health check
- `GET /api/redis/stats` - Redis statistics
- `POST /api/redis/clear` - Clear Redis cache
- `POST /api/redis/clear/<pattern>` - Clear Redis by pattern

### Portfolio Routes (2 endpoints)
- `POST /api/execute_trade` - Execute trade
- `GET /api/portfolio` - Portfolio data

### Page Routes (10 endpoints)
- `GET /` - Dashboard home
- `GET /stocks` - Stocks page
- `GET /crypto` - Crypto page
- `GET /portfolio` - Portfolio page
- `GET /portfolio_page` - Portfolio page alt
- `GET /foreign_markets_overview` - Foreign markets
- `GET /opportunities` - Opportunities page
- `GET /weekly_plan` - Weekly plan page
- `GET /logs` - Logs page
- `GET /recommendations` - Recommendations page
- `GET /reporting` - Reporting page

### Market Routes (6 endpoints)
- `GET /api/foreign_markets/overview` - Foreign markets data
- `GET /api/weekly_events` - Weekly market events
- `POST /api/weekly_plan/populate` - Populate weekly plan
- `GET /api/weekly_plan/available_weeks` - Available weeks
- `GET /api/market_calendar/<date_str>` - Market calendar
- `GET /api/earnings_calendar` - Earnings calendar

### Logging Routes (2 endpoints)
- `POST /api/log_client_error` - Client error logging
- `POST /api/frontend_logs` - Frontend logs

### Go Services Routes (7 endpoints)
- `GET /api/go_services/status` - Go services status
- `GET /api/go_services/performance` - Go services performance
- `POST /api/go_services/restart` - Restart Go services
- `POST /api/go_services/cache/clear` - Clear Go cache
- `POST /api/go_services/jobs/submit` - Submit Go job
- `GET /api/go_services/jobs/stats` - Go jobs statistics
- `GET /api/go_services/cache/stats` - Go cache statistics

### Dashboard Routes (4 endpoints)
- `GET /api/dashboard/data` - Dashboard data
- `GET /api/market_movers` - Market movers
- `POST /api/refresh_market_movers` - Refresh market movers
- `GET /api/preloaded_data` - Preloaded data

### Backtest Routes (5 endpoints)
- `GET /backtest` - Backtest page
- `POST /api/backtest` - Run backtest
- `POST /api/backtest/historical` - Historical backtest
- `GET /api/backtest/recommendations` - Backtest recommendations
- `GET /api/backtest/stats` - Backtest statistics

### Admin Routes (7 endpoints)
- `GET /api/go_services/health` - Go services health
- `POST /api/preload_stock_data` - Preload stock data
- `POST /api/historical_data/update` - Update historical data
- `GET/POST /api/watchlist/config` - Watchlist configuration
- `GET /api/job_schedules` - Job schedules
- `POST /api/job_schedules` - Create job schedule
- `POST /api/job_schedules/<id>/enable` - Enable job schedule
- `DELETE /api/job_schedules/<id>` - Delete job schedule

### Report Routes (1 endpoint)
- `POST /api/reporting/generate` - Generate report

## 2. Socket.IO Events Documentation

### Event Types
1. **`watchlist_progress`** - Real-time watchlist analysis progress
   - **Payload:** `{symbol, completed, total, status}`
   - **Trigger:** Batch processing in `opportunity_routes.py`
   - **Usage:** Progress bars for watchlist analysis

2. **`sp500_progress`** - S&P 500 analysis progress
   - **Payload:** `{current, total, symbol, status}`
   - **Trigger:** S&P 500 bulk analysis
   - **Usage:** Progress updates in stocks page

3. **`progress`** - General progress updates
   - **Payload:** `{current, total, symbol, status}`
   - **Trigger:** Various analysis operations
   - **Usage:** Generic progress tracking

### WebSocket Configuration
- **CORS Origins:** `*` (configurable via `SOCKETIO_CORS_ALLOWED_ORIGINS`)
- **Ping Timeout:** 60 seconds
- **Ping Interval:** 25 seconds
- **Client Library:** Socket.IO 4.7.2

## 3. UI Feature Catalog

### Templates and Their API Dependencies

#### Core Pages
- **`index.html`** (Dashboard)
  - APIs: `/api/dashboard/data`, `/api/analyze_stock`, `/api/analyze_bulk`
  - Features: Real-time analysis, progress tracking

- **`stocks.html`** (S&P 500 Analysis)
  - APIs: `/api/sp500_analysis`, `/api/market_movers`
  - Socket Events: `sp500_progress`
  - Features: Bulk analysis, progress bars

- **`opportunities.html`** (Trading Opportunities)
  - APIs: `/api/news_opportunities`, `/api/watchlist_opportunities`
  - Socket Events: `watchlist_progress`, `progress`
  - Features: Real-time opportunity analysis

- **`crypto.html`** (Cryptocurrency)
  - APIs: `/api/crypto_analysis`
  - Features: Crypto sentiment analysis

- **`portfolio.html`** (Portfolio Management)
  - APIs: `/api/portfolio`, `/api/execute_trade`
  - Features: Trade execution, portfolio tracking

#### Analysis Pages
- **`backtest.html`** (Backtesting)
  - APIs: `/api/backtest`, `/api/backtest/historical`, `/api/backtest/recommendations`
  - Features: Strategy backtesting, historical analysis

- **`recommendations.html`** (Recommendations)
  - APIs: `/api/recommendations`, `/api/recommendations/stats`
  - Features: AI-generated trading recommendations

#### System Pages
- **`system_status.html`** (System Monitoring)
  - APIs: `/api/system_status`, `/api/system_metrics`, `/api/go_services/status`
  - Features: System health monitoring

- **`logs.html`** (Logging)
  - APIs: `/api/logs`, `/api/logging/verbosity`
  - Features: Log viewing and configuration

- **`reporting.html`** (Reporting)
  - APIs: `/api/reporting/generate`
  - Features: Report generation

#### Market Pages
- **`foreign_markets_overview.html`** (Foreign Markets)
  - APIs: `/api/foreign_markets/overview`, `/api/test_foreign_markets`
  - Features: International market analysis

- **`weekly_plan.html`** (Weekly Planning)
  - APIs: `/api/weekly_events`, `/api/weekly_plan/populate`
  - Features: Weekly market planning

#### Specialized Pages
- **`scalping_signals.html`** (Scalping)
  - Features: High-frequency trading signals

### Navigation Structure
- **Primary Trading:** Dashboard, Opportunities, Weekly Plan, Foreign Markets, Recommendations, Portfolio
- **Analysis & Research:** S&P 500, Crypto, Backtest, Scalping
- **System & Monitoring:** Reporting, System Status, Logs

## 4. Static Assets Audit

### CSS Files (7 files)
- **`styles.css`** - Main application styles
- **`unified_theme.css`** - Unified theme system
- **`scalping_signals.css`** - Scalping-specific styles
- **`weekly_plan.css`** - Weekly plan styles
- **Backup files:** `styles.css.backup`, `styles.css.current_backup`, `unified_theme.css.backup`

### JavaScript Files (6 files)
- **`base.js`** - Core functionality, Socket.IO connection, logging
- **`dashboard.js`** - Dashboard-specific logic
- **`stocks.js`** - S&P 500 analysis, WebSocket handlers
- **`opportunities.js`** - Opportunity analysis, progress tracking
- **`crypto.js`** - Cryptocurrency analysis
- **`logger.js`** - Frontend logging system

### Asset Reusability Assessment
- **✅ Reusable:** CSS files (with minor modifications), logger.js
- **⚠️ Needs Refactoring:** JavaScript files (Socket.IO integration, API calls)
- **❌ Backend-Specific:** Template inheritance, Jinja macros

## 5. Configuration Review

### Environment Variables
**Backend-Only Variables:**
- `SECRET_KEY` - Flask secret key
- `DATABASE_URL` - PostgreSQL connection
- `REDIS_URL` - Redis connection
- `ALPHA_VANTAGE_API_KEY` - Financial data API
- `FINNHUB_API_KEY` - Market data API
- `NEWSAPI_API_KEY` - News API
- `OPENAI_API_KEY` - AI analysis
- `TELEGRAM_API_KEY` - Notifications
- `POLYGON_API_KEY` - Market data

**Frontend-Build Variables (New):**
- `VITE_API_BASE_URL` - Backend API URL
- `VITE_SOCKET_URL` - WebSocket server URL
- `VITE_ENVIRONMENT` - Build environment (dev/prod)

### Configuration Files
- **`config/secrets.yaml`** - API keys and secrets (backend only)
- **`src/core/config.py`** - Application configuration (backend only)
- **`requirements.txt`** - Python dependencies (backend only)

### CORS Configuration
- **Current:** `CORS_ORIGINS = "*"`
- **Socket.IO:** `SOCKETIO_CORS_ALLOWED_ORIGINS = "*"`
- **Methods:** GET, POST, PUT, DELETE, OPTIONS
- **Headers:** Content-Type, Authorization

## 6. Key Dependencies

### Backend Dependencies
- **Flask** - Web framework
- **Flask-SocketIO** - WebSocket support
- **Flask-CORS** - Cross-origin requests
- **PostgreSQL** - Primary database
- **Redis** - Caching layer
- **APScheduler** - Background jobs
- **Go Services** - Microservices integration

### Frontend Dependencies
- **Bootstrap 5.3.0** - UI framework
- **Font Awesome 6.4.0** - Icons
- **Chart.js** - Data visualization
- **jQuery 3.7.1** - DOM manipulation
- **Moment.js 2.29.4** - Date handling
- **Socket.IO 4.7.2** - Real-time communication

## 7. Critical Integration Points

### Real-time Features
- **Progress Tracking:** Socket.IO events for long-running analyses
- **Live Updates:** Market data, opportunities, system status
- **Error Handling:** Client-side error reporting to backend

### State Management
- **Analysis State:** Current analysis progress, results caching
- **UI State:** Loading states, progress bars, form data
- **Session State:** User preferences, watchlist configurations

### Data Flow
- **API Calls:** RESTful endpoints with JSON responses
- **WebSocket:** Real-time progress and status updates
- **Caching:** Redis for performance optimization
- **Batch Processing:** Go services for heavy computations

## 8. Migration Complexity Assessment

### High Complexity Areas
1. **Socket.IO Integration** - Real-time features across separate deployments
2. **Template-to-Component Migration** - 21 templates to modern frontend
3. **State Management** - Complex JavaScript state machines
4. **API Contract Preservation** - 81 endpoints must maintain exact behavior

### Medium Complexity Areas
1. **Static Asset Migration** - CSS/JS refactoring for new build system
2. **CORS Configuration** - Cross-origin setup for separate deployments
3. **Environment Configuration** - Split config between backend/frontend

### Low Complexity Areas
1. **API Endpoint Extraction** - Well-defined REST endpoints
2. **Database Layer** - Already separated in `src/core`
3. **Background Jobs** - Clear separation in `src/core`

## 9. Recommendations for Phase 1

### Immediate Actions
1. **Create Backend Repository** - Extract API-only Flask app
2. **Freeze API Contracts** - Document all 81 endpoints with OpenAPI
3. **Setup CORS Testing** - Validate cross-origin functionality
4. **Socket.IO Testing** - Ensure WebSocket events work across domains

### Risk Mitigation
1. **Automated Testing** - Endpoint regression tests
2. **Incremental Migration** - Serve frontend from Flask during transition
3. **Monitoring** - Track API performance and WebSocket connectivity
4. **Rollback Plan** - Maintain monolith until frontend is validated

This discovery phase provides the foundation for a successful frontend/backend split with minimal service disruption.
