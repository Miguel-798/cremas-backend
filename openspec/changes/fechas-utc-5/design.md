# Design: fechas-utc-5

## Technical Approach

Use timezone-aware datetime throughout the application:
1. Backend stores UTC with timezone info
2. Pydantic serializes to ISO 8601
3. Frontend parses ISO 8601 and displays in local timezone
4. "Today" filter uses Colombia timezone

## Architecture Decisions

### Decision: Use UTC as storage standard

**Choice**: Store all timestamps in UTC with timezone awareness
**Rationale**: UTC is the standard for storage, frontend converts to local

### Decision: Use pydantic-extra-types for datetime serialization

**Choice**: Let Pydantic handle ISO 8601 serialization automatically
**Rationale**: No manual formatting needed, standard-compliant

## Data Flow

```
Backend: datetime.now(timezone.utc) → UTC timestamp → DB → Pydantic → ISO 8601 JSON
Frontend: ISO 8601 → new Date() → Browser local timezone → Display
Filter: Now in Colombia → Start/end of day Colombia → Compare with UTC storage
```

## File Changes

### Backend - Modified Files

| File | Change |
|------|--------|
| `src/domain/entities/sale.py` | Import timezone, use `datetime.now(timezone.utc)` |
| `src/domain/entities/cream.py` | Import timezone, use aware datetime |
| `src/infrastructure/database/base.py` | Ensure DateTime columns accept timezone |
| `src/application/dtos/__init__.py` | Configure datetime serialization |
| `src/application/services/inventory_service.py` | Use timezone-aware datetime |

### Frontend - Modified Files

| File | Change |
|------|--------|
| `src/app/ventas/page.tsx` | Fix date parsing, "today" filter uses Colombia timezone |

## Code Changes

### Backend: Sale entity
```python
from datetime import datetime, timezone

class Sale:
    sold_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
```

### Backend: DTO config
```python
from pydantic import ConfigDict

class SaleResponse(BaseModel):
    model_config = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()}
    )
```

### Frontend: Date filtering
```typescript
// Get start and end of today in Colombia (UTC-5)
const now = new Date();
const startOfDayColombia = new Date(now.getFullYear(), now.getMonth(), now.getDate(), 0, 0, 0);
const endOfDayColombia = new Date(now.getFullYear(), now.getMonth(), now.getDate(), 23, 59, 59);

// Filter sales
const todaySales = sales.filter(sale => {
  const saleDate = new Date(sale.sold_at);
  return saleDate >= startOfDayColombia && saleDate <= endOfDayColombia;
});
```

## Testing Strategy

| Layer | What | How |
|-------|------|-----|
| Unit | datetime.now(timezone.utc) works | Verify timestamp has timezone |
| Integration | API returns ISO 8601 | Call endpoint, check response |
| E2E | Frontend shows correct date | Browser in Colombia, check display |

## Migration

No database migration required - existing naive datetimes will be handled gracefully by checking `tzinfo` attribute.

## Open Questions

None