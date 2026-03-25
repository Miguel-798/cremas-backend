# Proposal: crud-update-creams-and-delete-sales

## Intent

Add ability to UPDATE existing creams (name, price) and DELETE sales from history. Currently:
- Cream PUT only updates quantity, not name or price
- No DELETE endpoint exists for sales

## Scope

### In Scope
- Extend PUT /creams/{id} to update name, price, and quantity
- Add DELETE /creams/sales/{id} endpoint to delete sales
- When deleting a sale, restore the cream's inventory (quantity_sold added back)
- Add edit modal to creams frontend page
- Add delete button to sales history frontend

### Out of Scope
- Soft delete for sales (audit trail) - use hard delete for simplicity
- Bulk delete operations

## Approach

1. **Backend - Update Cream:**
   - Extend existing PUT endpoint to accept full cream fields
   - Add CreamUpdate DTO with optional fields (name, price, quantity)
   - Update service to handle partial updates

2. **Backend - Delete Sale:**
   - Add DELETE endpoint at /creams/sales/{sale_id}
   - Service method: get sale, add quantity_sold back to cream.quantity, delete sale
   - Handle case where cream no longer exists

3. **Frontend - Edit Cream:**
   - Add edit button/icon on each cream row
   - Show modal with current values
   - Call PUT endpoint on save

4. **Frontend - Delete Sale:**
   - Add delete button on each sale in history
   - Show confirmation dialog
   - Call DELETE endpoint, refresh list

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `src/application/dtos/__init__.py` | Modified | Add CreamUpdate DTO |
| `src/api/routes/inventory.py` | Modified | Add DELETE sale endpoint |
| `src/application/services/inventory_service.py` | Modified | Add update_cream, delete_sale methods |
| `src/infrastructure/database/postgres_repo.py` | Modified | Implement sale delete in repo |
| `frontend-new/src/lib/api.ts` | Modified | Add updateCream, deleteSale API methods |
| `frontend-new/src/app/cremas/page.tsx` | Modified | Add edit modal |
| `frontend-new/src/app/ventas/page.tsx` | Modified | Add delete button |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Inventory restoration on delete | Medium | Wrap in transaction |
| Cream deleted after sale | Low | Check cream exists before restoring |

## Rollback Plan

1. Revert backend endpoint changes
2. Revert frontend changes
3. Redeploy

## Success Criteria

- [ ] Can update cream name, price from UI
- [ ] Can delete sale from history
- [ ] Inventory restored when sale deleted
- [ ] Confirmation dialog before delete