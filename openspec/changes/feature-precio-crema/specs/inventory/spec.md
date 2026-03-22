# Delta for Inventory/Cream Pricing

## ADDED Requirements

### Requirement: Cream Price Field

The system MUST include a `price` field on Cream entities with the following characteristics:
- Type: Decimal with 2 decimal places
- Default value: 0.00
- Constraint: Non-negative (MUST be >= 0)

#### Scenario: Create cream with price

- GIVEN valid authentication and CreamCreate DTO with price=9.99
- WHEN POST /creams is called
- THEN the cream is created with price=9.99 and returned in CreamResponse
- AND the price persists in database as decimal(10,2)

#### Scenario: Create cream without price (default)

- GIVEN valid authentication and CreamCreate DTO without price field
- WHEN POST /creams is called
- THEN the cream is created with price=0.00 (default)

#### Scenario: Update cream price

- GIVEN an existing cream and valid authentication
- WHEN PUT /creams/{cream_id} is called with new price
- THEN the cream's price is updated and returned in response

#### Scenario: Price with invalid negative value rejected

- GIVEN CreamCreate DTO with price=-5.00
- WHEN validation is applied
- THEN the request fails with 422 validation error (Pydantic ge=0)

#### Scenario: Price with more than 2 decimals truncated

- GIVEN CreamCreate DTO with price=9.999
- WHEN validation is applied
- THEN the value is rounded to 9.999 -> 10.00 OR rejected with 422

---

## MODIFIED Requirements

### Requirement: CreamCreate DTO

The CreamCreate DTO MUST include the `price` field.
(Previously: Only flavor_name and quantity)

### Requirement: CreamResponse DTO

The CreamResponse DTO MUST include the `price` field.
(Previously: Only id, flavor_name, quantity, created_at, updated_at)

### Requirement: CreamWithStatus DTO

The CreamWithStatus DTO MUST include the `price` field.
(Previously: Only id, flavor_name, quantity, is_low_stock, created_at, updated_at)

### Requirement: Cream Entity

The Cream entity MUST include the `price` attribute.
(Previously: id, flavor_name, quantity, created_at, updated_at)

### Requirement: CreamModel (SQLAlchemy)

The CreamModel MUST include a `price` column.
(Previously: id, flavor_name, quantity, created_at, updated_at)

---

## Data Contracts

### CreamCreate (Modified)
```python
class CreamCreate(BaseModel):
    flavor_name: str = Field(..., min_length=1, max_length=255)
    quantity: int = Field(default=0, ge=0)
    price: Decimal = Field(default=Decimal("0.00"), ge=0, decimal_places=2)  # NEW
```

### CreamResponse (Modified)
```python
class CreamResponse(BaseModel):
    id: UUID
    flavor_name: str
    quantity: int
    price: Decimal  # NEW
    created_at: datetime
    updated_at: datetime
```

### CreamWithStatus (Modified)
```python
class CreamWithStatus(BaseModel):
    id: UUID
    flavor_name: str
    quantity: int
    price: Decimal  # NEW
    is_low_stock: bool
    created_at: datetime
    updated_at: datetime
```

### Cream Entity (Domain)
```python
@dataclass
class Cream:
    id: uuid.UUID
    flavor_name: str
    quantity: int
    price: Decimal = Decimal("0.00")  # NEW
    created_at: datetime
    updated_at: datetime
```

### CreamModel (SQLAlchemy)
```python
class CreamModel(Base):
    id: Mapped[str]
    flavor_name: Mapped[str]
    quantity: Mapped[int]
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"))  # NEW
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]
```

---

## API Endpoints Affected

| Endpoint | Method | Change |
|----------|--------|--------|
| /creams | POST | CreamCreate includes price |
| /creams | GET | CreamWithStatus includes price |
| /creams/{cream_id} | GET | CreamResponse includes price |
| /creams/{cream_id} | PUT | Response includes price |
| /creams/{cream_id}/add-stock | POST | Response includes price |
| /creams/{cream_id}/sell | POST | Response includes price |
| /creams/{cream_id}/history | GET | CreamResponse includes price |
| /creams/low-stock | GET | Alerts include price |

---

## Database Migration

### Alembic Migration Required

**File**: `alembic/versions/{revision}_add_price_to_creams.py`

```python
"""Add price to creams table

Revision ID: {new_revision}
Revises: {previous_revision}
Create Date: {date}
"""
from alembic import op
import sqlalchemy as sa
from decimal import Decimal

revision = '{new_revision}'
down_revision = '{previous_revision}'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column(
        'creams',
        sa.Column('price', sa.Numeric(10, 2), nullable=False, server_default='0.00')
    )

def downgrade() -> None:
    op.drop_column('creams', 'price')
```

---

## Edge Cases

1. **Negative price rejected**: Pydantic validation with `ge=0`
2. **Excessive decimal places**: Should validate to 2 decimal places max
3. **Price > 999999.99**: Should be supported by Numeric(10,2)
4. **Migration rollback**: Must preserve data if downgrading
5. **Legacy data**: Existing creams get price=0.00 via server_default

---

## Dependencies

- **Pydantic**: Decimal field validation
- **SQLAlchemy**: Numeric(10,2) column type
- **Alembic**: Migration script
- **Domain Service**: InventoryService.create_cream() must accept price

---

## Next Step

Ready for design (sdd-design). If design already exists, ready for tasks (sdd-tasks).