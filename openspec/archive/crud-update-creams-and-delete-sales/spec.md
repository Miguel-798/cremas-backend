# Delta Spec: crud-update-creams-and-delete-sales

## MODIFIED Requirements

### Requirement: Update cream accepts full fields

The system SHALL accept name, price, and quantity when updating a cream.

#### Scenario: Update cream name

- GIVEN a cream "Crema A" exists
- WHEN user updates name to "Crema Nueva"
- THEN the cream name SHALL be updated in database

#### Scenario: Update cream price

- GIVEN a cream with price 5000 exists
- WHEN user updates price to 7500
- THEN the cream price SHALL be updated

#### Scenario: Update cream quantity

- GIVEN a cream with quantity 10 exists
- WHEN user updates quantity to 20
- THEN the cream quantity SHALL be updated

### Requirement: Delete sale restores inventory

The system SHALL restore cream inventory when a sale is deleted.

#### Scenario: Delete sale successfully

- GIVEN a cream has quantity 10 and a sale of 5 units exists
- WHEN user deletes the sale
- THEN the cream quantity SHALL be restored to 15
- AND the sale SHALL be removed from database

#### Scenario: Delete sale when cream deleted

- GIVEN a sale exists but the cream was deleted
- WHEN user deletes the sale
- THEN the sale SHALL be removed
- AND no inventory restoration SHALL occur

## ADDED Requirements

### Requirement: Frontend edit cream modal

The frontend SHALL provide a modal to edit cream details.

#### Scenario: Open edit modal

- GIVEN user is on creams page
- WHEN user clicks edit button on a cream
- THEN a modal SHALL appear with current cream values
- AND fields SHALL be editable

#### Scenario: Save cream changes

- GIVEN edit modal is open with cream data
- WHEN user clicks save
- THEN the API SHALL be called with updated values
- AND the list SHALL refresh with new data
- AND the modal SHALL close

### Requirement: Frontend delete sale button

The frontend SHALL provide a button to delete sales from history.

#### Scenario: Delete sale from history

- GIVEN user is on sales page
- WHEN user clicks delete button on a sale
- THEN a confirmation dialog SHALL appear
- AND if confirmed, the API SHALL delete the sale
- AND the inventory SHALL be restored
- AND the list SHALL refresh

#### Scenario: Cancel delete

- GIVEN delete confirmation dialog is shown
- WHEN user clicks cancel
- THEN the dialog SHALL close
- AND no changes SHALL be made