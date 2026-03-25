# Tasks: crud-update-creams-and-delete-sales

## Phase 1: Backend - DTOs & Service

- [x] 1.1 Add CreamUpdate DTO
  - File: `src/application/dtos/__init__.py`
  - Add: CreamUpdate class with optional name, price, quantity fields

- [x] 1.2 Add update_cream method to service
  - File: `src/application/services/inventory_service.py`
  - Add: update_cream(cream_id, update_data) function

- [x] 1.3 Add delete_sale method to service
  - File: `src/application/services/inventory_service.py`
  - Add: delete_sale(sale_id) with inventory restoration logic

## Phase 2: Backend - Endpoints

- [x] 2.1 Extend PUT /creams/{id} endpoint
  - File: `src/api/routes/inventory.py`
  - Update: Accept CreamUpdate DTO, call service.update_cream

- [x] 2.2 Add DELETE /creams/sales/{id} endpoint
  - File: `src/api/routes/inventory.py`
  - Add: New endpoint that calls service.delete_sale

- [x] 2.3 Add sale delete to repository
  - File: `src/infrastructure/database/postgres_repo.py`
  - Add: delete method to SaleRepository

## Phase 3: Frontend - API

- [x] 3.1 Add updateCream to API
  - File: `frontend-new/src/lib/api.ts`
  - Add: updateCream(id, data) method with PUT

- [x] 3.2 Add deleteSale to API
  - File: `frontend-new/src/lib/api.ts`
  - Add: deleteSale(id) method with DELETE

## Phase 4: Frontend - UI

- [x] 4.1 Add edit cream modal
  - File: `frontend-new/src/app/cremas/page.tsx`
  - Add: Modal component with form fields
  - Add: Edit button on each cream row

- [x] 4.2 Add delete sale button
  - File: `frontend-new/src/app/ventas/page.tsx`
  - Add: Delete button on each sale row
  - Add: Confirmation dialog

## Phase 5: Testing & Verification

- [ ] 5.1 Test update cream
  - Action: Update cream name/price from UI

- [ ] 5.2 Test delete sale
  - Action: Delete sale, verify inventory restored

- [ ] 5.3 Verify all scenarios
  - Action: Check spec scenarios work