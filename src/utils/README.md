# Trading AI - Utilities & Documentation

This directory contains utility scripts, technical documentation, and developer resources for the Trading AI platform.

## 🛠️ Utility Scripts

### `setup_postgres.py`
**PostgreSQL Database Setup Script**

Sets up the complete PostgreSQL database infrastructure for the Trading AI platform.

**What it does:**
- ✅ Creates the `trading_db` database
- ✅ Creates the `trading_user` with proper permissions
- ✅ Creates the `app_cache` table with optimized indexes
- ✅ Tests database connection and cache functionality
- ✅ Provides detailed setup verification

**When to use:**
- 🆕 **First-time setup** on a new machine
- 🔄 **Database recovery** after corruption or issues
- 👥 **Team onboarding** - new developers setting up their environment
- 🚀 **Production deployment** on new servers
- 🧪 **CI/CD environments** requiring fresh database setup

**Usage:**
```bash
# Run from project root
python src/utils/setup_postgres.py
```

**Prerequisites:**
- PostgreSQL 14+ installed and running
- Superuser access (postgres user) with known password
- Python environment with psycopg2 installed

**Output:**
- Creates database: `trading_db`
- Creates user: `trading_user` (password: `trading_password`)
- Creates table: `app_cache` with indexes
- Runs functionality tests
- Provides performance optimization verification

---

## 📚 Technical Documentation

### `PERFORMANCE_OPTIMIZATION.md`
**Performance Enhancement Guide**

Comprehensive documentation of performance optimizations implemented in the Trading AI platform.

**Contents:**
- PostgreSQL cache implementation (2,400x performance improvement)
- Smart batching system (5-10x faster bulk analysis)
- WebSocket real-time progress updates
- Concurrent processing optimizations
- Performance benchmarks and metrics

### `NEWS_SOURCES.md`
**News Sources Configuration Guide**

Documentation for configuring and managing news data sources.

**Contents:**
- Supported news providers (Finnhub, Yahoo Finance, Alpha Vantage, Reddit)
- API configuration and rate limiting
- News source prioritization and fallback strategies
- Reddit integration with comprehensive subreddit coverage
- News data processing and sentiment analysis pipeline

### `GO_ANALYSIS.md`
**Go Microservices Analysis**

Technical analysis and implementation guide for Go microservices integration.

**Contents:**
- Performance comparison: Python vs Go
- Microservice architecture design
- API gateway and service communication
- Performance benchmarks and optimization strategies
- Implementation roadmap for Go services

---

## 🔧 Development Tools

This directory serves as the central location for:
- **Database utilities** - Setup, migration, and maintenance scripts
- **Performance tools** - Monitoring and optimization utilities
- **Documentation** - Technical guides and implementation details
- **Development aids** - Scripts for development environment setup

---

## 📋 Usage Notes

### Database Setup
```bash
# Initial PostgreSQL setup
python src/utils/setup_postgres.py
```

### Documentation Access
- Performance optimization details: `src/utils/PERFORMANCE_OPTIMIZATION.md`
- News sources configuration: `src/utils/NEWS_SOURCES.md`
- Go microservices planning: `src/utils/GO_ANALYSIS.md`

### Future Utilities
This directory is ready for additional developer tools:
- Database migration scripts
- Cache cleanup utilities
- Performance monitoring tools
- Backup and restore scripts
- Testing utilities
- Development environment helpers

---

## 🎯 Organization Benefits

**Cleaner Project Root:**
- Main directory focuses on user-facing files (README, startup scripts)
- Technical utilities organized in dedicated location
- Better separation of concerns

**Developer Experience:**
- All utility scripts in one location
- Technical documentation easily accessible
- Clear organization for team collaboration

**Maintenance:**
- Centralized location for developer tools
- Easier to add new utilities
- Consistent documentation structure 