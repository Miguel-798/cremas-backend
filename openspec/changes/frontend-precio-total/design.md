# Design: frontend-precio-total

## Technical Approach
- **Backend**: Add `price` column to sales table, capture cream.price when sale is registered
- **Frontend**: Display price when cream selected, calculate totals client-side, show daily revenue

## Architecture Decisions

### Decision: Store price at sale time
- **Choice**: Store price permanently in sale record
- **Alternative**: Fetch current price dynamically
- **Rationale**: Historical accuracy - revenue won't change if cream price changes later

## Data Flow

```
User selects cream → Frontend shows cream.price
User enters quantity → Frontend calculates total = price × quantity
User submits → API creates sale with captured price
API returns sale with price + total → Frontend displays
```

## File Changes

### Backend - New Files
- `alembic/versions/xxxx_add_price_to_sales.py` — Migration to add price column to sales

### Backend - Modified Files

| File | Change |
|------|--------|
| `src/application/dtos/__init__.py` | Add `price: float` and `total: float` to SaleResponse |
| `src/domain/entities/sale.py` | Add `price: float = 0.0` field |
| `src/infrastructure/database/base.py` | Add `price = Column(Numeric(10, 2), default=0.0)` to SaleModel |
| `src/application/services/inventory_service.py` | In register_sale, set `price=cream.price`, calculate `total=price*quantity` |

### Frontend - Modified Files

| File | Change |
|------|--------|
| `src/lib/api.ts` | Add `price?: number` and `total?: number` to Sale interface |
| `src/app/ventas/page.tsx` | Show price when cream selected, calculate and display total, add daily revenue to stats |

## Code Changes (Based on current codebase)

### SaleResponse (backend - add to existing class)
```python
class SaleResponse(BaseModel):
    """DTO para responder con datos de venta."""
    id: UUID
    cream_id: UUID
    cream_name: str
    quantity_sold: int
    price: float  # NEW
    total: float  # NEW - calculated as price * quantity_sold
    sold_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
```

### Sale Entity (backend - add fields)
```python
@dataclass
class Sale:
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    cream_id: uuid.UUID = field(default_factory=uuid.uuid4)
    cream_name: str = ""
    quantity_sold: int = 0
    price: float = 0.0  # NEW
    sold_at: datetime = field(default_factory=datetime.utcnow)
```

### SaleModel (backend - add column)
```python
class SaleModel(Base):
    __tablename__ = "sales"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    cream_id: Mapped[str] = mapped_column(String(36), ForeignKey("creams.id"), nullable=False)
    cream_name: Mapped[str] = mapped_column(String(255), nullable=False)
    quantity_sold: Mapped[int] = mapped_column(Integer, nullable=False)
    price: Mapped[float] = mapped_column(Numeric(10, 2), default=0.0, nullable=False)  # NEW
    sold_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
```

### register_sale (service change - capture price)
In the register_sale function, after getting the cream:
```python
async def register_sale(self, cream_id: UUID, quantity_sold: int) -> Sale:
    cream = await self.cream_repo.get_by_id(cream_id)
    if not cream:
        raise ValueError(f"Crema no encontrada: {cream_id}")
    
    if quantity_sold > cream.quantity:
        raise ValueError(
            f"Stock insuficiente. Disponible: {cream.quantity}, "
            f"solicitado: {quantity_sold}"
        )
    
    # Descontar stock
    cream.remove_stock(quantity_sold)
    await self.cream_repo.update(cream)
    
    # Capture price at sale time
    price = cream.price  # NEW
    total = price * quantity_sold  # NEW
    
    # Crear registro de venta
    sale = Sale(
        cream_id=cream_id,
        cream_name=cream.flavor_name,
        quantity_sold=quantity_sold,
        price=price,  # NEW
    )
    result = await self.sale_repo.create(sale)
    
    # ... rest of method
```

### Sale Interface (frontend - add to existing interface)
```typescript
interface Sale {
  id: string;
  cream_id: string;
  cream_name: string;
  quantity_sold: number;
  price?: number;    // NEW
  total?: number;    // NEW
  sold_at: string;
}
```

### Sales Page (frontend changes)
1. Add state: `selectedPrice?: number`
2. When cream selected: set `selectedPrice = cream.price`
3. Display price next to cream name
4. Calculate total: `total = selectedPrice * quantity`
5. Display total in "Resumen del día" section
6. Add "Ingresos del día" showing sum of totals

## Migration Plan
1. Create Alembic migration: `alembic revision -m "add price to sales"`
2. Add column: `price = Column(Numeric(10, 2), default=0.0)`
3. Apply migration: `alembic upgrade head`
4. No data migration needed - existing sales get price=0

## Testing Strategy
| Layer | What | How |
|-------|------|-----|
| Unit | register_sale captures price | Mock cream with price, verify sale.price |
| Integration | API returns price and total | Call /creams/sales, verify response |
| E2E | User sees price when cream selected | Playwright test |

## Open Questions
None - all technical decisions resolved.
