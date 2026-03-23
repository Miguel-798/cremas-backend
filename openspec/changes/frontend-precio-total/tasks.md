# Tasks: frontend-precio-total

## Task List

### PHASE 1: Backend Changes

- [x] **Task 1.1**: Add price field to Sale entity
  - File: `src/domain/entities/sale.py`
  - Action: Add `price: float = 0.0` field to Sale dataclass
  - Verification: Entity accepts price parameter

- [x] **Task 1.2**: Add price column to SaleModel
  - File: `src/infrastructure/database/base.py`
  - Action: Add `price: Mapped[float] = mapped_column(Numeric(10, 2), default=0.0, nullable=False)` to SaleModel class
  - Verification: Model has price column defined

- [x] **Task 1.3**: Create Alembic migration for price column
  - Command: `cd gentleman && alembic revision -m "add_price_to_sales"`
  - File: `alembic/versions/xxxx_add_price_to_sales.py`
  - Action: Add migration to add price column with default 0.0
  - Verification: `alembic upgrade head` runs successfully

- [x] **Task 1.4**: Add price and total to SaleResponse DTO
  - File: `src/application/dtos/__init__.py`
  - Action: Add `price: float` and `total: float` fields to SaleResponse class
  - Note: total will be computed in the service, not in the DTO directly
  - Verification: API response includes price and total

- [x] **Task 1.5**: Update register_sale to capture price
  - File: `src/application/services/inventory_service.py`
  - Action: In register_sale function, after getting cream, set `price = cream.price` and calculate `total = price * quantity_sold`. Pass these to Sale constructor
  - Verification: New sales have correct price and total stored

- [x] **Task 1.6**: Test backend changes
  - Action: Start server, create a test sale, verify price and total in response
  - Verification: GET /creams/sales returns price and total

### PHASE 2: Frontend Changes

- [x] **Task 2.1**: Add price to Cream interface
  - File: `frontend-new/src/lib/api.ts`
  - Action: Add `price: number` to Cream interface (required, not optional)
  - Verification: TypeScript compiles without errors

- [x] **Task 2.2**: Add price and total to Sale interface
  - File: `frontend-new/src/lib/api.ts`
  - Action: Add `price?: number` and `total?: number` to Sale interface (optional for backward compatibility)
  - Verification: TypeScript compiles without errors

- [x] **Task 2.3**: Display price when cream selected
  - File: `frontend-new/src/app/ventas/page.tsx`
  - Action: In the selected cream display section, add `selected.flavor_name` and price next to it
  - Note: The Cream interface now has price field from Task 2.1
  - Verification: Price appears next to cream name when cream is selected

- [x] **Task 2.4**: Calculate and display total
  - File: `frontend-new/src/app/ventas/page.tsx`
  - Action: Calculate `total = selected.price * quantity` and display below quantity input or in the selected cream card
  - Verification: Total updates when quantity changes

- [x] **Task 2.5**: Add daily revenue to stats section
  - File: `frontend-new/src/app/ventas/page.tsx`
  - Action: In both the "Registrar Venta" and "Historial" views, add sum of totals for today's sales to the "Hoy" card
  - Note: Use `sale.total ?? 0` to handle legacy sales without price
  - Verification: Stats show revenue in the "Hoy" section (e.g., "3 unidades / $15000")

- [x] **Task 2.6**: Handle legacy sales gracefully
  - File: `frontend-new/src/app/ventas/page.tsx`
  - Action: Use `sale.price ?? 0` and `sale.total ?? 0` when displaying sales or calculating totals
  - Verification: Old sales don't cause errors and display correctly

- [x] **Task 2.7**: Add manual price input to creams form
  - File: `frontend-new/src/app/cremas/page.tsx`
  - Action: Add price input field to the cream creation/edit form
  - Note: The Cream interface already has price field from Task 2.1
  - Verification: Can enter custom price when creating/editing a cream

- [x] **Task 2.8**: Add editable price input to sales form
  - File: `frontend-new/src/app/ventas/page.tsx`
  - Action: Add editable price input that auto-fills with selected cream's price, but allows manual override
  - Note: Calculate total = price × quantity
  - Verification: Price can be edited and total updates correctly

- [x] **Task 2.9**: Test frontend changes
  - Action: Run dev server, create creams and sales, verify price inputs work correctly
  - Verification: All UI elements work correctly

### PHASE 3: Verification

- [x] **Task 3.1**: Verify all specs are met
  - Check each requirement from spec.md
  - Ensure all scenarios work

- [x] **Task 3.2**: Push to GitHub
  - Backend: Push changes to gentleman repo
  - Frontend: Push changes to frontend-new repo