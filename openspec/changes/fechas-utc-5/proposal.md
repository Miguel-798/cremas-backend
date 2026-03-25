# Proposal: fechas-utc-5

## Intent
Fix timezone handling so dates are stored and displayed in Colombia's local time (UTC-5). Currently, sales and other timestamps show 5 hours earlier than expected, and "today's sales" filtering doesn't work correctly.

## Scope

### In Scope
- Update backend to use timezone-aware datetime (datetime.now(timezone.utc))
- Configure Pydantic DTOs for proper ISO 8601 serialization
- Update frontend to correctly parse and display timezone-aware dates
- Fix "today's sales" filter to work with Colombian timezone

### Out of Scope
- Historical data migration (existing dates remain as-is)
- Timezone configuration UI (hardcoded to Colombia for now)

## Approach
Use timezone-aware datetimes throughout:
1. **Backend**: Replace `datetime.utcnow()` with `datetime.now(timezone.utc)`
2. **Database**: Store timestamps with timezone info
3. **Frontend**: Parse ISO 8601 strings correctly and display in local time
4. **Filtering**: Use proper date comparison for "today" in Colombia timezone

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `src/domain/entities/sale.py` | Modified | Use aware datetime for sold_at |
| `src/domain/entities/cream.py` | Modified | Use aware datetime for timestamps |
| `src/infrastructure/database/base.py` | Modified | Ensure DateTime columns store timezone |
| `src/application/dtos/__init__.py` | Modified | Configure DTOs for ISO serialization |
| `src/application/services/inventory_service.py` | Modified | Use timezone-aware datetime |
| `frontend-new/src/app/ventas/page.tsx` | Modified | Fix date parsing and "today" filter |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Existing naive dates in DB | Medium | Handle both naive and aware dates gracefully |
| Pydantic serialization | Low | Test JSON output format |
| Frontend date parsing | Low | Use proper ISO parsing |

## Rollback Plan
1. Revert datetime usage changes
2. Revert frontend date parsing
3. Redeploy

## Success Criteria
- [ ] New sales use timezone-aware timestamps
- [ ] Dates display correctly in frontend (not 5 hours off)
- [ ] "Today's sales" filter works correctly in Colombia
- [ ] API returns ISO 8601 formatted dates