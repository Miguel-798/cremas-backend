# Design: crud-update-creams-and-delete-sales

## Technical Approach

1. **Backend - Update Cream:**
   - Extend PUT /creams/{id} to accept optional fields
   - Create CreamUpdate DTO with optional name, price, quantity
   - Update service to handle partial updates

2. **Backend - Delete Sale:**
   - Add DELETE /creams/sales/{sale_id} endpoint
   - Service: get sale → restore inventory → delete sale
   - Use transaction for atomicity

3. **Frontend - Edit Modal:**
   - Add edit button to cream rows
   - Modal with form fields (name, price, quantity)
   - PUT on save

4. **Frontend - Delete Button:**
   - Add delete button to sale rows
   - Confirmation dialog
   - DELETE on confirm, refresh list

## Data Flow

### Update Cream
```
UI Edit Modal → PUT /creams/{id} → Service.update_cream() → Repo → DB
```

### Delete Sale
```
UI Delete Button → Confirmation → DELETE /creams/sales/{id} 
→ Service.delete_sale() → Get Sale → Restore Cream Qty → Delete Sale → Repo → DB
```

## File Changes

### Backend - Modified Files

| File | Change |
|------|--------|
| `src/application/dtos/__init__.py` | Add CreamUpdate DTO |
| `src/api/routes/inventory.py` | Add DELETE /creams/sales/{id} endpoint, extend PUT |
| `src/application/services/inventory_service.py` | Add update_cream, delete_sale methods |
| `src/infrastructure/database/postgres_repo.py` | Add sale delete to repository |

### Frontend - Modified Files

| File | Change |
|------|--------|
| `frontend/src/lib/api.ts` | Add updateCream, deleteSale methods |
| `frontend/src/app/cremas/page.tsx` | Add edit modal component |
| `frontend/src/app/ventas/page.tsx` | Add delete button and confirmation |

## Code Examples

### CreamUpdate DTO (backend)
```python
class CreamUpdate(BaseModel):
    name: str | None = None
    price: float | None = None
    quantity: int | None = None
```

### Delete Sale Endpoint (backend)
```python
@sales_router.delete("/sales/{sale_id}")
async def delete_sale(
    sale_id: UUID,
    current_user: User = Depends(get_current_user)
):
    await inventory_service.delete_sale(sale_id)
    return {"message": "Sale deleted"}
```

### API Methods (frontend)
```typescript
updateCream: (id: string, data: Partial<Cream>) => 
  authFetchApi(`/creams/${id}`, { method: 'PUT', body: data }),

deleteSale: (id: string) => 
  authFetchApi(`/creams/sales/${id}`, { method: 'DELETE' }),
```

## Testing Strategy

| Layer | What | How |
|-------|------|-----|
| Unit | update_cream, delete_sale | Mock repo, verify calls |
| Integration | API endpoints | Call with curl/Postman |
| E2E | UI edit/delete | Playwright test |

## Migration

No database migration required - schema unchanged.

## Open Questions

None