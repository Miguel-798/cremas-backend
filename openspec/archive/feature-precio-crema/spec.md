# Spec: feature-precio-crema

## Overview

Add price tracking to cream inventory items.

## Requirements

### ADDED
- `price` field: `float`, default `0.0`, non-negative validation

### MODIFIED
- CreamCreate DTO - accepts price in creation
- CreamResponse DTO - returns price in responses
- CreamWithStatus DTO - returns price with stock status

## Scenarios

### Create with price
- GIVEN: User creates cream with price
- WHEN: POST /creams with `{flavor_name, price}`
- THEN: Cream created with specified price

### Default price
- GIVEN: User creates cream without price
- WHEN: POST /cremas with `{flavor_name}`
- THEN: Cream created with price = 0.0

### Update price (future)
- GIVEN: Cream exists with price
- WHEN: Price update endpoint called
- THEN: Price updated to new value

## Technical Design

### Domain Layer
```python
@dataclass
class Cream:
    price: float = 0.0
```

### Database Layer
```python
price: Mapped[float] = mapped_column(Numeric(10, 2), default=0.00, nullable=False)
```

### DTO Layer
```python
class CreamCreate(BaseModel):
    price: float = Field(default=0.0, ge=0)
```

### Migration
```python
op.add_column('creams', sa.Column('price', sa.Numeric(10, 2), nullable=False, server_default='0.00'))
```

## Status: COMPLETED ✅
