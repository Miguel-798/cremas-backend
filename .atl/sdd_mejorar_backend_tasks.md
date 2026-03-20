# Tasks: Comprehensive Backend Improvements

## Phase 1: Logging — structlog, remove print(), global exception handler

- [ ] 1.1 Add `structlog>=24.1.0` to `requirements.txt`
- [ ] 1.2 Create `src/infrastructure/logging.py` with `configure_logging()` (JSON in prod, ConsoleRenderer in dev) and `get_logger()` helper
- [ ] 1.3 Import `get_logger` in `src/infrastructure/auth.py`; replace 2 `print()` calls (lines 42, 62) in `get_token_algorithm` and `verify_supabase_token` with `log.warning(...)`
- [ ] 1.4 Import `get_logger` in `src/api/routes/inventory.py`; replace 5 `print()` calls in `require_auth` (lines 100, 103, 110, 114, 121) with `log.debug/info/warning(...)`
- [ ] 1.5 Import `get_logger` in `src/application/services/notification_service.py`; replace 4 `print()` calls (lines 48, 67, 71, 89) with structlog
- [ ] 1.6 Import `get_logger` in `src/infrastructure/config/settings.py`; replace 1 `print()` (line 22) with `log.warning(...)`
- [ ] 1.7 Import and call `configure_logging()` in `src/api/main.py` lifespan startup; replace 6 `print()` calls (lines 50, 54, 56-57, 62) with structlog; add global exception handler using `@app.exception_handler(Exception)` logging full traceback
- [ ] 1.8 Run app in dev mode; verify colored console output and no `print()` in logs

## Phase 2: Database — connection pooling, indexes via Alembic

- [ ] 2.1 Run `alembic init alembic` in project root to scaffold `alembic/` directory
- [ ] 2.2 Configure `alembic.ini` with async `sqlalchemy.url` from `settings.database_url`; update `env.py` to load async engine from `src/infrastructure.database.base`
- [ ] 2.3 Add `__table_args__` to `SaleModel` in `src/infrastructure/database/base.py`: `Index("ix_sales_cream_id", "cream_id")`
- [ ] 2.4 Add `__table_args__` to `ReservationModel`: `Index("ix_reservations_cream_id", "cream_id")` and `Index("ix_reservations_reserved_for", "reserved_for")`
- [ ] 2.5 Add `__table_args__` to `CreamModel`: `Index("ix_creams_flavor_name", "flavor_name")`
- [ ] 2.6 Run `alembic revision --autogenerate -m "add performance indexes"` to generate migration
- [ ] 2.7 Review generated SQL in `alembic/versions/`; verify `CREATE INDEX CONCURRENTLY` is used
- [ ] 2.8 Run `alembic upgrade head` to apply indexes; verify no table locks

## Phase 3: Auth — remove fallback, JWKS cache with TTL

- [ ] 3.1 Add `cachetools>=5.3.0` to `requirements.txt`
- [ ] 3.2 Import `TTLCache` in `src/infrastructure/auth.py`; add module-level `_jwks_cache: TTLCache = TTLCache(maxsize=1, ttl=3600)`
- [ ] 3.3 Replace the JWKS fetch loop in `verify_supabase_token` (lines 76-89) with cache-first: check `_jwks_cache["jwks"]`, fetch only on miss, store result
- [ ] 3.4 Remove the fallback decode-without-verification block entirely (lines 91-108 in current auth.py); raise `RuntimeError("JWKS: All endpoints failed")` instead
- [ ] 3.5 Import `get_logger` in auth.py; replace remaining `print()` in `verify_supabase_token` with `log.info/debug/warning` for JWKS fetch events
- [ ] 3.6 Add startup JWKS pre-fetch to `src/api/main.py` lifespan: call `_get_jwks()` and log result or raise on failure
- [ ] 3.7 Write `tests/infrastructure/test_auth.py`: test cache hit (returns cached JWKS), cache miss (fetches JWKS), all-endpoints-fail raises RuntimeError, valid/invalid/expired token handling

## Phase 4: Caching — memory/Redis cache abstraction

- [x] 4.1 Create `src/infrastructure/cache.py` with `CacheProtocol` (async `get`, `set`, `delete`) and `MemoryCache` implementation using `cachetools.TTLCache`
- [x] 4.2 Add `CACHE_ENABLED` env var to `settings.py` (default `False`)
- [x] 4.3 In `src/application/services/inventory_service.py`, instrument `get_all_creams()` and `get_cream_by_id()` with cache on reads if `CACHE_ENABLED`
- [x] 4.4 Add cache invalidation in `create_cream()`, `update_cream_quantity()`, `add_stock()`, `delete_cream()`, `register_sale()` on writes
- [ ] 4.5 Write `tests/infrastructure/test_cache.py`: test MemoryCache get/set/eviction, TTL expiration, cache invalidation on writes

## Phase 5: Testing — pytest structure, fixtures

- [ ] 5.1 Add `mock_verify_token` fixture to `tests/conftest.py`: async fn returning `AuthUser(id="test-user-1", email="test@example.com", role="authenticated")`
- [ ] 5.2 Add `mock_auth_user` fixture to `tests/conftest.py`: returns `AuthUser(...)` instance
- [ ] 5.3 Create `tests/infrastructure/test_auth.py` with `pytest.mark.asyncio`: test cache hit, cache miss, expired token returns None, invalid token raises, JWKS endpoint failures
- [ ] 5.4 Create `tests/infrastructure/test_postgres_repo.py` with `pytest-asyncio`: test `PostgresCreamRepository` CRUD using sqlite `:memory:` async engine fixture
- [ ] 5.5 Create `tests/services/test_notification_service.py`: mock Gmail API, test `send_low_stock_alert`, disabled-notification path, daily-throttle
- [ ] 5.6 Create `tests/services/test_reservation_service.py` using mock repos from conftest: test expiry logic, active reservation filtering
- [ ] 5.7 Run `pytest tests/infrastructure/ tests/services/`; fix all failures before proceeding
