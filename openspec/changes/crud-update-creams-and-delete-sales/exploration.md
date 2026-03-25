# Exploration: crud-update-creams-and-delete-sales

## Current State

### UPDATE Cream
- **Backend Endpoint**: `PUT /creams/{cream_id}` exists (inventory.py:250-268)
- **DTO**: `CreamUpdate` only allows updating `quantity` field (dtos/__init__.py:41-43)
- **Service**: `update_cream_quantity` only updates quantity, not name or price (inventory_service.py:79-96)
- **Frontend API**: No `update` method in `creamsApi` - only create, addStock, delete (api.ts:112-122)
- **Frontend UI**: No edit modal/button for creams - only add stock via prompt

### DELETE Sale
- **Backend Endpoint**: NO existing DELETE endpoint for sales
- **Service**: No `delete_sale` method in `InventoryService`
- **Repository**: No `delete` method in `SaleRepository` interface (repositories.py:55-72)
- **Frontend API**: No `delete` method in `salesApi` (api.ts:124-130)
- **Frontend UI**: No delete button for sales in the history view (ventas/page.tsx)

## Affected Areas

### Backend
- `src/application/dtos/__init__.py` — Need to add `CreamFullUpdate` DTO or extend existing
- `src/api/routes/inventory.py` — Add DELETE /creamssales/{sale_id} endpoint
- `src/application/services/inventory_service.py` — Add `update_cream` and `delete_sale` methods
- `src/domain/repositories.py` — Add `delete` method to `SaleRepository` interface
- `src/infrastructure/database/postgres_repo.py` — Implement `delete` in `PostgresSaleRepository`

### Frontend
- `src/lib/api.ts` — Add `update` to `creamsApi` and `delete` to `salesApi`
- `src/app/cremas/page.tsx` — Add edit modal for cream (name, price, quantity)
- `src/app/ventas/page.tsx` — Add delete button to sale history items

## Approaches

### Approach A: Minimal Update for Cream + Full Delete for Sale
1. **UPDATE cream**: Extend `CreamUpdate` DTO to include all fields (flavor_name, price, quantity), create new service method `update_cream` that updates all fields
2. **DELETE sale**: Add delete endpoint that restores cream stock

**Pros**: 
- Cream update allows editing name and price (fulfills user need)
- Sale delete properly restores inventory (data consistency)
- Minimal changes to existing code

**Cons**:
- More complex service method

**Effort**: Medium

### Approach B: Separate Endpoints for Cream
1. **UPDATE cream**: Keep existing PUT for quantity, add new PATCH for full update
2. **DELETE sale**: Add delete endpoint WITHOUT restoring stock (simple deletion)

**Pros**: 
- Separation of concerns (quantity update vs full update)
- Simpler sale delete (no inventory logic)

**Cons**: 
- Two endpoints for cream update could be confusing
- Sale delete without inventory restoration could cause data inconsistency

**Effort**: Low-Medium

### Approach C: Full Update + Soft Delete for Sale
1. **UPDATE cream**: Extend PUT to accept all fields
2. **DELETE sale**: Add soft delete (mark as cancelled) instead of hard delete

**Pros**: 
- Preserves audit trail
- No inventory logic complexity

**Cons**: 
- Doesn't actually remove the sale
- More complex frontend (show cancelled sales differently)

**Effort**: High

## Recommendation

**Approach A** is recommended because:
1. It provides the functionality the user requested (edit cream name/price + delete sale)
2. Deleting a sale should restore the cream inventory to maintain data consistency
3. Single PUT endpoint for cream update is cleaner than multiple endpoints

### Implementation Details

**For UPDATE cream:**
- Create new DTO `CreamFullUpdate` with optional fields: `flavor_name`, `price`, `quantity`
- Create service method `update_cream(cream_id, data)` that updates all provided fields
- Add frontend edit modal in creams page

**For DELETE sale:**
- Add `delete(sale_id)` to SaleRepository interface
- Implement in PostgresSaleRepository
- Add service method `delete_sale(sale_id)` that:
  1. Gets the sale to find cream_id and quantity_sold
  2. Deletes the sale record
  3. Restores the stock to the cream (add_stock)
  4. Invalidates relevant caches
- Add DELETE /creamssales/{sale_id} endpoint
- Add delete button to sales history UI

## Risks

1. **Inventory consistency**: When deleting a sale, stock must be restored - failing to do this will cause inventory discrepancies
2. **Race conditions**: Concurrent sale deletes could cause stock issues - consider using database transactions
3. **Frontend UX**: Edit modal needs validation and error handling
4. **Cache invalidation**: Must properly invalidate creams and sales caches after delete

## Ready for Proposal

**Yes** - The exploration is complete. The recommended approach (Approach A) provides:
- Full cream editing (name, price, quantity)
- Sale deletion with inventory restoration
- Clear implementation path with identified files

Next step: Create proposal document with scope, approach, and affected areas.
