# Archive: crud-update-creams-and-delete-sales

## Summary
**Change**: crud-update-creams-and-delete-sales
**Status**: Completed ✅
**Date**: 2026-03-25

## Intent
Add ability to UPDATE existing creams (name, price) and DELETE sales from history with inventory restoration.

## Scope (Completed)
- ✅ CreamPatch/CreamUpdate DTO for partial updates
- ✅ update_cream method in service
- ✅ delete_sale method with inventory restoration
- ✅ PUT /creams/{id} extended for full updates
- ✅ DELETE /creams/sales/{id} endpoint added
- ✅ Edit cream modal in frontend
- ✅ Delete sale button with confirmation dialog

## Files Changed
### Backend
- src/application/dtos/__init__.py - CreamPatch DTO
- src/application/services/inventory_service.py - update_cream, delete_sale
- src/api/routes/inventory.py - Extended PUT, new DELETE
- src/infrastructure/database/postgres_repo.py - Repository delete methods
- src/domain/repositories.py - Repository interface

### Frontend
- frontend-new/src/lib/api.ts - updateCream, deleteSale methods
- frontend-new/src/app/cremas/page.tsx - Edit modal
- frontend-new/src/app/ventas/page.tsx - Delete button + confirmation

## Notes
- Inventory is restored when sale is deleted
- Confirmation dialog before delete
- Partial cream updates supported (only changed fields)