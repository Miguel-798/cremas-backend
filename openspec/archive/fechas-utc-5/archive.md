# Archive: fechas-utc-5

## Summary
**Change**: fechas-utc-5
**Status**: Completed ✅
**Date**: 2026-03-25

## Intent
Fix timezone handling for Colombia (UTC-5). Dates were showing 5 hours earlier due to UTC storage without timezone awareness.

## Scope (Completed)
- ✅ Backend entities use timezone-aware datetime (datetime.now(timezone.utc))
- ✅ Database models use DateTime(timezone=True)
- ✅ Pydantic DTOs serialize to ISO 8601
- ✅ Frontend has Colombia timezone helpers
- ✅ "Today" filter uses Colombia timezone

## Files Changed
### Backend
- src/domain/entities/sale.py
- src/domain/entities/cream.py
- src/domain/entities/reservation.py
- src/infrastructure/database/base.py
- src/application/dtos/__init__.py
- src/application/services/inventory_service.py

### Frontend
- frontend-new/src/app/ventas/page.tsx

## Verification
- Backend: ✅ Complete
- Frontend: ✅ Complete (Colombia timezone helpers verified)
- Build: ✅ Passes

## Notes
- Legacy naive datetimes handled gracefully
- No database migration needed
