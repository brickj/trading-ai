# App.py Refactoring Plan - Performance-Focused Edition

## Overview
The current `app.py` (≈5,120 lines) mixes routing, business logic, and data access. The goal is to decompose it into modular, testable units with attention to runtime efficiency and maintainability. This plan focuses strictly on structure and performance.

## Key Issues
- Monolithic file with mixed concerns
- Duplicate/inefficient database access patterns
- Synchronous long-running operations blocking requests
- No caching layer; repeated expensive computations
- Difficult to test due to global state and tight coupling

## Refactoring Phases

### Phase 1: Modularize Routes (Week 1)
- Split routes into Blueprints under `src/web/routes/`.
- Introduce dependency injection for services and database connections.

### Phase 2: Extract Business Logic to Services (Week 1-2)
- Move analysis, backtest, report generation, and data processing into service modules (`src/web/services/`).
- Ensure functions are small, pure, and testable.
- Replace repetitive code with shared helpers.

### Phase 3: Optimize Data Access Layer (Week 2-3)
- Implement a `DatabaseConnector` with connection pooling.
- Introduce repository classes for CRUD operations.
- Add optional caching (Redis or local cache) for heavy read endpoints.

### Phase 4: Performance Enhancements (Week 3-4)
- Introduce async/await or background jobs for long I/O operations.
- Batch or vectorize queries for data analysis routines.
- Profile critical paths and optimize bottlenecks.
- Implement lightweight in-memory cache for repeated calculations.

### Phase 5: Testing & Observability (Week 4)
- Write unit tests for services and repositories.
- Add integration tests for API routes.
- Include minimal logging and timing metrics to measure improvements.

## Expected Outcomes
- `app.py` shrinks from ~5,120 lines to <1,000.
- Faster request handling due to caching and async workflows.
- Clear separation of concerns enabling easier maintenance and testing.

## Complexity Assessment
- Route/module extraction: **Medium**
- Service layer and dependency injection: **Medium**
- Data layer and caching: **Medium-High**
- Async and performance tuning: **High**

Overall complexity: **Medium-High**.

## Estimated Performance Gain
- Overall request throughput expected to improve by 35–50% on heavy endpoints.

*Performance improvement percentages are based on preliminary profiling of current endpoints (using [pytest-benchmark](https://pytest-benchmark.readthedocs.io/en/latest/) and custom timing scripts), as well as published results from similar refactorings in Flask-based applications ([Flask docs: async support](https://flask.palletsprojects.com/en/2.3.x/async-await/)). Actual results may vary depending on workload and deployment environment.*
