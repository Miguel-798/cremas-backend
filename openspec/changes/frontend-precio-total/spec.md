# Delta Spec: frontend-precio-total

## ADDED Requirements

### Requirement: SaleResponse includes price
The SaleResponse DTO MUST include a `price: float` field representing the cream's price at time of sale.

### Requirement: SaleResponse includes total
The SaleResponse DTO MUST include a `total: float` field calculated as `price × quantity`.

### Requirement: Price captured at sale time
The inventory service MUST capture the cream's price when a sale is registered and store it with the sale.

### Requirement: Frontend displays price on cream selection
When a user selects a cream in the sales form, the system SHALL display the cream's price next to the cream name.

### Requirement: Frontend calculates and displays total
When quantity is entered, the system SHALL calculate and display `total = price × quantity`.

### Requirement: Daily sales summary shows revenue
The sales stats section SHALL display total daily revenue in addition to unit count.

## Scenarios

### Scenario: New sale captures cream price
- GIVEN a cream with price 5000 exists
- WHEN a sale is registered for quantity 3
- THEN the sale SHALL have price=5000 and total=15000

### Scenario: Legacy sale without price
- GIVEN a sale created before this feature
- WHEN the sale is retrieved
- THEN price SHALL be 0 and total SHALL be 0

### Scenario: Price shown on cream selection
- GIVEN user is on /ventas page
- WHEN user selects "Crema de Coco" (price 5000)
- THEN the page SHALL display the price next to cream name

### Scenario: Total updates with quantity
- GIVEN price is 5000 and quantity input shows 2
- WHEN user enters or changes quantity
- THEN total SHALL update to show 10000

### Scenario: Daily revenue in stats
- GIVEN 3 sales today totaling 15000 pesos
- WHEN user views /ventas page
- THEN stats SHALL show "Ingresos del día: $15000"