# Proposal: frontend-precio-total

## Intent
Add price tracking to sales and display daily revenue summary in the Cremas inventory app.

## Scope

### In Scope
- Add `price` field to SaleResponse/SaleEntity/SaleModel — captures price at time of sale
- Calculate `total = price × quantity` in SaleResponse
- Update frontend sales page to show price when cream is selected
- Add daily sales summary with total revenue on stats section

### Out of Scope
- Historical data migration for existing sales without price
- Backend aggregation endpoint for daily summary (frontend aggregates)

## Approach
1. **Backend**: Add `price` column to sales table, capture cream.price when sale is registered
2. **Frontend**: Show price in cream selection summary, calculate and display total, aggregate daily revenue client-side

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `src/application/dtos/__init__.py` | Modified | Add price and total to SaleResponse |
| `src/domain/entities/sale.py` | Modified | Add price field to Sale entity |
| `src/infrastructure/database/base.py` | Modified | Add price column to SaleModel |
| `src/application/services/inventory_service.py` | Modified | Capture cream price at sale time |
| `src/lib/api.ts` | Modified | Add price/total to Sale interface |
| `src/app/ventas/page.tsx` | Modified | Show price, display totals, daily summary |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Database migration for sales table | Low | Use Alembic, test locally first |
| Legacy sales without price | Medium | Handle null/missing gracefully in UI |

## Rollback Plan
1. Revert Alembic migration
2. Revert frontend TypeScript interfaces
3. Redeploy backend and frontend

## Success Criteria
- [ ] Price displayed when cream selected in sales form
- [ ] Total (price × quantity) calculated and shown
- [ ] Daily summary section shows total revenue
- [ ] Existing sales without price display gracefully (no crash)