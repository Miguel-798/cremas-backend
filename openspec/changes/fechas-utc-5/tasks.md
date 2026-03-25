# Tasks: fechas-utc-5

## Phase 1: Backend - Entity Changes

- [x] 1.1 Update Sale entity to use timezone-aware datetime
  - File: `src/domain/entities/sale.py`
  - Import: `from datetime import datetime, timezone`
  - Change: `sold_at` uses `datetime.now(timezone.utc)`

- [x] 1.2 Update Cream entity timestamps
  - File: `src/domain/entities/cream.py`
  - Import timezone
  - Change: `created_at`, `updated_at` use aware datetime

- [x] 1.3 Update Reservation entity if exists
  - File: `src/domain/entities/reservation.py`
  - Change timestamps to use timezone-aware datetime

## Phase 2: Backend - DTO & Service

- [x] 2.1 Configure Pydantic datetime serialization
  - File: `src/application/dtos/__init__.py`
  - Add: `json_encoders` config for datetime → ISO format

- [x] 2.2 Update inventory_service to use timezone-aware datetime
  - File: `src/application/services/inventory_service.py`
  - Change: All `datetime.utcnow()` → `datetime.now(timezone.utc)`

- [x] 2.3 Verify database model DateTime columns
  - File: `src/infrastructure/database/base.py`
  - Ensure: `DateTime(timezone=True)` is used

## Phase 3: Frontend - Date Handling

- [x] 3.1 Fix date parsing in sales page
  - File: `frontend-new/src/app/ventas/page.tsx`
  - Ensure: Dates are parsed correctly from ISO 8601

- [x] 3.2 Fix "today" filter to use Colombia timezone
  - File: `frontend-new/src/app/ventas/page.tsx`
  - Logic: Filter by Colombia local date, not UTC

- [x] 3.3 Update date display format
  - File: `frontend-new/src/app/ventas/page.tsx`
  - Show: Date in readable format for Colombia

## Phase 4: Testing & Verification

- [ ] 4.1 Test backend datetime serialization
  - Action: Create sale, check API returns ISO 8601 with timezone

- [ ] 4.2 Test frontend date display
  - Action: Make sale at 10 AM Colombia, verify shows 10 AM

- [ ] 4.3 Test "today's sales" filter
  - Action: Create sale, verify it appears in today's list

- [ ] 4.4 Verify legacy date handling
  - Action: Check existing sales still display correctly
