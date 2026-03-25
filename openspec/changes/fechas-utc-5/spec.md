# Delta Spec: fechas-utc-5

## MODIFIED Requirements

### Requirement: Sale timestamps MUST use timezone-aware datetime

The system SHALL store sale timestamps using timezone-aware datetime (UTC with timezone info).

#### Scenario: New sale uses timezone-aware timestamp

- GIVEN a user creates a new sale at 10:00 AM Colombia time
- WHEN the sale is saved to the database
- THEN the timestamp SHALL be stored as UTC (5 hours ahead: 3:00 PM UTC)
- AND when retrieved, the API SHALL return ISO 8601 formatted datetime with timezone

#### Scenario: Legacy naive datetime

- GIVEN a sale was created before this fix (naive datetime)
- WHEN the sale is retrieved via API
- THEN the system SHALL handle both naive and aware datetimes gracefully

### Requirement: Frontend MUST display dates in local timezone

The frontend SHALL parse and display dates using the browser's local timezone.

#### Scenario: Date display in Colombia

- GIVEN a sale was created at 3:00 PM UTC
- WHEN displayed in frontend (browser in Colombia, UTC-5)
- THEN it SHALL show as 10:00 AM Colombia time

#### Scenario: Today's sales filter

- GIVEN user is in Colombia (UTC-5)
- WHEN viewing today's sales
- THEN only sales from midnight to midnight Colombia time SHALL be shown
- AND NOT sales from midnight to midnight UTC

### Requirement: API response MUST include timezone info

The API SHALL return dates in ISO 8601 format with timezone information.

#### Scenario: ISO 8601 response format

- GIVEN a sale exists in the database
- WHEN the sale is fetched via API
- THEN the sold_at field SHALL be in format: "2026-03-25T10:00:00-05:00"

## ADDED Requirements

### Requirement: Date filtering MUST use Colombia timezone

The "today's sales" filter SHALL use Colombia's local date for comparison.

#### Scenario: Today's sales at midnight

- GIVEN it's March 25, 10:00 AM in Colombia
- WHEN fetching today's sales
- THEN sales from March 25 00:00 to March 25 23:59:59 Colombia time SHALL be included
- AND sales from March 24 20:00 UTC to March 25 19:59:59 UTC SHALL be excluded