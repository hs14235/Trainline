# Trainline architecture

## Scope

Trainline is a modular monolith deployed as three cooperating services:

1. An Nginx container serves the compiled React single-page application.
2. A Django REST Framework process exposes authentication and domain APIs.
3. PostgreSQL stores relational application state and provides the locking semantics used by seat assignment.

The development container runs Django's reload-capable server. The production-oriented override replaces it with Gunicorn, removes the backend bind mount, closes the PostgreSQL host port, enables static collection, and selects `booking.settings_production`. It does not provide TLS termination, a cloud runtime, backups, or monitoring and is therefore not a complete deployment architecture.

## Service boundaries

~~~mermaid
flowchart TB
    subgraph Client
        React[React components]
        Axios[Axios API client]
        Store[Browser localStorage token]
        React --> Axios
        Store --> Axios
    end

    subgraph API[Django modular monolith]
        URLs[URL router]
        Auth[dj-rest-auth and DRF auth]
        Views[ViewSets and APIViews]
        Serializers[Serializers]
        Services[Domain services]
        Models[Django models and signals]
        URLs --> Auth
        Auth --> Views
        Views --> Serializers
        Views --> Services
        Serializers --> Models
        Services --> Models
    end

    Axios -->|JSON and Token header| URLs
    Models -->|ORM| PostgreSQL[(PostgreSQL)]
~~~

### React/Nginx

React owns browser interaction, client-side routes, loading/error state, and calls to the API base supplied at build time. Nginx serves static assets and falls back to `index.html` for client-side routes. It does not proxy the API in the current configuration; the browser calls Django directly on the configured origin.

### Django REST API

The API owns authentication, authorization, validation, pricing, booking state, and database transaction boundaries. Views remain intentionally thin around `core/services.py` for fare calculation and seat assignment.

### PostgreSQL

PostgreSQL is the authoritative production-oriented datastore. SQLite is retained only as the low-friction native and fast-test default. The PostgreSQL test tier exists because SQLite cannot demonstrate row-level locking or all production field constraints.

## Request flows

### Authentication

~~~mermaid
sequenceDiagram
    participant Browser
    participant Auth as dj-rest-auth
    participant DB as PostgreSQL
    Browser->>Auth: POST registration or login
    Auth->>DB: validate/create user
    DB-->>Auth: user state
    Auth-->>Browser: DRF token
    Browser->>Browser: store token locally
    Browser->>Auth: Authorization: Token ...
    Auth-->>Browser: authenticated API response
~~~

Token storage in `localStorage` is a known limitation: a successful same-origin XSS could read it. Replacing it with an HttpOnly cookie or access/refresh design changes the authentication contract and should be performed as a dedicated migration.

### Booking and fare calculation

1. The authenticated client posts booking options to `/api/train-trips/{trip_id}/book/`.
2. The API resolves or creates the caller's one-to-one Passenger record.
3. The server normalizes option booleans and calculates `base fare + selected fees`.
4. Django creates the Ticket in an atomic transaction.
5. The response returns only the new ticket identifier and calculated amount.

The client never supplies passenger ownership or the authoritative amount.

### Seat assignment

~~~mermaid
sequenceDiagram
    participant Client
    participant API
    participant Trip as Locked TrainTrip row
    participant DB as PostgreSQL
    Client->>API: POST trip, ticket_id, seat_num
    API->>DB: confirm ticket belongs to caller and trip
    API->>Trip: SELECT ... FOR UPDATE
    API->>DB: lock ticket and validate inventory
    API->>DB: check conflicting reservation
    alt seat is free
        API->>DB: update ticket seat
        API-->>Client: 200 seat assigned
    else seat is already held
        API-->>Client: 409 Conflict
    end
~~~

All application writes use the shared service, which locks the trip row so competing requests for the same trip are serialized. A partial PostgreSQL uniqueness constraint on `(train_trip, seat_num)` is the final integrity boundary for non-null, non-empty seat values. Migration `0003_ticket_unique_trip_seat` first refuses to apply if duplicates already exist; it does not silently rewrite historical data.

### Payment transition

1. The caller posts one of `cash`, `check`, or `credit_card` to an owned ticket.
2. The API locks the Ticket row without joining the nullable membership relation.
3. An already-paid ticket returns `409 Conflict`.
4. The paid flag and method are persisted atomically.
5. The Ticket signal recalculates the Passenger's membership state.

This is local state validation, not external payment processing. No live payment, email, or AI service is called.

## Persistence model

~~~mermaid
erDiagram
    USER ||--o| PASSENGER : has
    MEMBERSHIP_LEVEL ||--o{ USER : categorizes
    MEMBERSHIP_LEVEL ||--o{ PASSENGER : categorizes
    PASSENGER ||--o{ TICKET : owns
    TRAIN_TRIP ||--o{ TICKET : booked_for
    TRAIN_TRIP ||--o{ SEAT : provides
    USER ||--o{ NOTIFICATION : receives
    TRAIN_TRIP ||--o{ NOTIFICATION : concerns
    TICKET ||--o{ PAYMENT : records
    USER ||--o{ CHAT_MESSAGE : authors
    TICKET ||--o{ CHAT_MESSAGE : concerns
    TRAIN_TRIP ||--o{ CHAT_MESSAGE : concerns
~~~

The existing schema retains legacy database names such as `flight` and `flight_id` through Django's `db_table` and `db_column` mappings. These names are intentionally preserved to avoid an unnecessary data/API migration while the product language uses train trips.

## Authorization boundaries

- TrainTrip discovery is read-only and authenticated.
- Ticket querysets are filtered through `passenger__user=request.user`.
- Booking derives Passenger from the authenticated user.
- Seat assignment validates both ticket ownership and trip association.
- Payment locks and updates only an owned ticket.
- Notification querysets are filtered by the authenticated user; mark-read uses that queryset.
- Serializer read-only fields prevent callers from directly writing ownership, amount, paid state, or payment method.

The tests cover anonymous, authenticated, owner, and non-owner requests, including invalid identifiers and malformed input.

## Configuration and health

- `booking.settings` provides environment-aware defaults and uses SQLite when no database URL is supplied.
- `booking.settings_test` isolates deterministic test behavior.
- `booking.settings_production` forces production validation.
- `/healthz` reports process liveness without touching the database.
- `/readyz` runs a database query and fails if persistence is unavailable.
- Compose starts Django only after PostgreSQL is healthy and starts the frontend only after Django readiness passes.

## Important decisions

### Needed now

- Modular monolith: domain size does not justify distributed services.
- PostgreSQL locking and constraint: duplicate seats are a core integrity risk.
- Separate fast and PostgreSQL test tiers: speed without losing database-specific evidence.
- Environment-specific safety: demo secrets and seed operations must fail closed in production.

### Needed later

- Pagination and query budgets when trip/ticket volumes grow.
- A provider boundary, idempotency key, ledger, and webhook verification for real payments.
- An authenticated chat API with explicit participant authorization.
- Metrics, tracing, backup/restore exercises, and operational alerting before deployment.

### Optional

- A task queue only when email, payment webhooks, or other background work exists.
- Managed platform services only after a deployment target is selected.

Microservices, Kubernetes, Kafka, and distributed caching are not justified by the current scale or behavior.

## Known failure modes

| Failure | Current behavior |
| --- | --- |
| Database unavailable at startup | Readiness fails; dependent frontend startup does not report healthy |
| Invalid or nonexistent seat | `400 Bad Request` |
| Seat already assigned on the trip | `409 Conflict` plus database uniqueness fallback |
| Ticket belongs to another user | `404 Not Found` through scoped lookup |
| Ticket already paid | `409 Conflict` |
| Unsupported/missing payment method | `400 Bad Request` |
| Demo seed in production | Command refuses to run |
| Demo identity collision | Command aborts without changing the existing user |
| Duplicate data before uniqueness migration | Migration aborts with example conflicts |

## Verification boundaries

Local automated tests and HTTP smoke checks validate application behavior. They do not establish production availability, penetration-test results, hosted CI status, backup recovery, TLS correctness, performance, or scale. Those require a selected deployment target and separately measured evidence.
