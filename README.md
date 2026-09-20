# Trainline

Trainline is a full-stack rail-booking portfolio application built with React, Django REST Framework, PostgreSQL, and Docker. It models trip discovery, bookings, seat inventory, payment state, notifications, and support records while emphasizing authorization, database integrity, repeatable local setup, and observable failures.

This independent engineering project is not affiliated with the commercial Trainline service.

> Verification status — September 20, 2026: the fast backend suite with measured coverage, isolated PostgreSQL locking tier, frontend lint/tests/build, migration checks, and three-service Docker Compose stack were exercised locally. The GitHub Actions workflow has not been run for this uncommitted revision. This revision is not deployed.

## Engineering highlights

- User-scoped ticket and notification queries protect against cross-account object access.
- Seat assignment serializes reservations on a shared PostgreSQL trip row and has a conditional database uniqueness constraint on `(train_trip, seat_num)`.
- The server returns itemized quotes and calculates persisted fares; callers cannot set passenger ownership, payment state, payment method, or price.
- Stable booking keys prevent duplicate ticket creation; event keys prevent duplicate durable notifications.
- Membership totals are derived idempotently from paid priority service and confirmed first-class seats.
- Payment transitions use an allowlist and reject repeated payment with `409 Conflict`.
- Development, test, and production-oriented Django settings have distinct safety behavior.
- Compose startup is ordered through PostgreSQL, API-readiness, and frontend health checks.
- An opt-in, production-blocked command creates deterministic demo data without overwriting users.
- The backend suite separates fast behavior tests from PostgreSQL locking tests.
- The repository-specific `trainline-testing` Codex skill selects test tiers, audits weak tests, and refuses remote or destructive actions.

## Product capabilities

- Account registration and token-backed login
- Authenticated profile summary
- Responsive trip discovery with From/To/date controls, station swapping, secondary supported-status filtering, allowlisted ordering, and explicit loading, empty, and service-failure states
- Server-quoted booking options with an itemized base fare, option fees, `$0.00` deterministic demo taxes/fees, and total
- Keyboard-operable full coach inventory with stable occupied seats, first-class labels, ownership-checked assignment, and `409 Conflict` recovery
- Duplicate-seat prevention at service and database layers
- Owned-ticket list, update, delete/cancel, and payment transition
- Derived membership levels and points for paid priority service and confirmed first-class seats
- User-scoped structured booking, payment, seat, point, and level-up event snapshots with idempotent creation and read-state updates
- A public Engineering page describing verified architecture, test tiers, and limitations
- OpenAPI schema, Swagger UI, liveness, and database readiness

Payment remains a local demo state transition; it does not contact a processor, collect financial details, or move money. Chat records remain in the legacy data model, but no chat or fake-assistant interface is exposed.

## Architecture

~~~mermaid
flowchart LR
    Browser[Browser] -->|HTTP :3000| Web[Nginx and React SPA]
    Web -->|JSON REST :8000| API[Django REST Framework]
    API --> Auth[Token and session authentication]
    API --> Domain[Fare, booking, and seat services]
    Domain -->|ORM and transactions| DB[(PostgreSQL 14)]
    API -->|/healthz| Live[Liveness]
    API -->|/readyz query| Ready[Database readiness]
~~~

The modular monolith has three runtime containers: React/Nginx, Django, and PostgreSQL. Booking rules live in a service module so API entry points share transaction-safe behavior without adding unnecessary microservices. [Architecture details](docs/architecture.md) cover request flow, persistence, locking, and tradeoffs.

## Technology stack

| Component | Responsibility |
| --- | --- |
| React 18, React Router 6, Axios | Browser UI, routing, authentication state, and API calls |
| Django 5.2, Django REST Framework 3.17 | Models, validation, authorization, REST endpoints, and OpenAPI |
| django-allauth, dj-rest-auth | Registration, login, and token issuance |
| PostgreSQL 14 | Relational persistence, uniqueness, and row locking |
| Gunicorn, Nginx, WhiteNoise | Production-oriented process and static serving |
| Docker Compose | Builds, service startup ordering, and health checks |
| pytest, pytest-django, Factory Boy, coverage.py | Behavior tests, fixtures, PostgreSQL tests, and coverage |
| Black, isort, Flake8, ESLint | Formatting and static checks |
| GitHub Actions | Local CI definition for backend and frontend verification |

## Screenshots

These checked-in captures show the existing interface and historical sample records. The current seed uses deterministic trips dated in 2030.

| Login | Registration |
| --- | --- |
| ![Login form over a steam-train photograph](backend/docs/traindemo-login.jpg) | ![Registration form over a railway photograph](backend/docs/traindemo-signup.jpg) |
| Trip discovery | Payment selection |
| ![Rail trips with route, schedule, platform, and booking actions](backend/docs/tripdemo-booking.jpg) | ![Ticket amount and payment-method selection](backend/docs/traindemopayment.jpg) |

## Docker quick start

Prerequisites: Docker Desktop with Compose v2 and available ports `3000`, `8000`, and `5432`.

~~~powershell
git clone https://github.com/hs14235/Trainline.git
cd Trainline
Copy-Item .env.example .env
docker compose up --build --detach --wait
docker compose exec -e ALLOW_DEMO_SEED=True backend python manage.py seed_demo
~~~

Open:

- Frontend: <http://localhost:3000>
- API root: <http://localhost:8000/api/>
- Swagger UI: <http://localhost:8000/api/docs/>
- Liveness: <http://localhost:8000/healthz>
- Readiness: <http://localhost:8000/readyz>

Inspect or stop without deleting the development database:

~~~powershell
docker compose ps
docker compose logs --tail 100 backend
docker compose down
~~~

The `postgres_dev_data` volume is separate from volumes created by older Compose configurations. `docker compose down` preserves it. There is intentionally no automatic destructive reset task; use a disposable database or remove the exact development volume manually only when deletion is intended.

## Demo environment

The defaults are public, non-sensitive demo values:

~~~text
Username: demo_traveler
Password: Trainline-Demo-2026!
Email:    demo.traveler@example.test
~~~

Seed with Docker:

~~~powershell
docker compose exec -e ALLOW_DEMO_SEED=True backend python manage.py seed_demo
~~~

Seed natively after setting `ALLOW_DEMO_SEED=True` in `backend/.env`:

~~~powershell
.\.venv\Scripts\python.exe backend\manage.py seed_demo
~~~

The command is idempotent, refuses `DJANGO_ENV=production`, refuses username/email collisions, never changes an existing password, and does not print the password. It creates three trips, 48 seats, three initial tickets, three timetable notices, three derived membership/reward events, two payment records, and two chat records. For a clean exercise, use a new disposable database; never reset a database containing needed data.

## Native development

Python 3.12 and Node.js 22 are the project and CI baselines. Native backend development defaults to SQLite; concurrency-sensitive verification uses an isolated PostgreSQL tier.

~~~powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
Copy-Item backend\.env.example backend\.env
.\.venv\Scripts\python.exe backend\manage.py migrate
.\.venv\Scripts\python.exe backend\manage.py runserver
~~~

In a second terminal:

~~~powershell
Set-Location frontend
Copy-Item .env.example .env
npm ci
npm start
~~~

macOS, Linux, and WSL use the equivalent `.venv/bin/python` and `cp` commands. List cross-platform tasks with `python scripts/tasks.py --list`.

## Commands

| Purpose | Command |
| --- | --- |
| Django configuration and migration drift | `python scripts/tasks.py check` |
| Apply native migrations | `python scripts/tasks.py migrate` |
| Fast backend suite | `python scripts/tasks.py test` |
| Isolated PostgreSQL tier | `python scripts/tasks.py test-postgres` |
| Branch coverage and 90% gate | `python scripts/tasks.py coverage` |
| Backend lint | `python scripts/tasks.py lint-backend` |
| Backend format check | `python scripts/tasks.py format-check` |
| Apply backend formatting | `python scripts/tasks.py format` |
| Frontend lint | `python scripts/tasks.py frontend-lint` |
| Frontend tests | `python scripts/tasks.py frontend-test` |
| Frontend production build | `python scripts/tasks.py frontend-build` |
| Complete fast sequence | `python scripts/tasks.py verify` |

`test-postgres` starts only `docker-compose.test.yml`'s disposable database when `TEST_DATABASE_URL` is absent. It rejects a URL whose database name does not contain `test`.

## Test strategy and measured results

Measured locally on September 20, 2026:

| Tier | Observable behavior | Result |
| --- | --- | --- |
| Fast backend | Models, serializers, auth, ownership, quotes, idempotent booking/events, payment, membership, schema, seats, and seed safety | 58 passed, 2 PostgreSQL tests deselected |
| PostgreSQL | Concurrent duplicate-seat arbitration and nullable-relation-safe ticket/passenger locking | 2 passed, 58 deselected |
| Frontend | Navigation, search, quotes, mutation guards, payment disclosure, stable seat maps, rewards, structured updates, and conflict recovery | 23 passed across 8 suites |
| Coverage | Fast backend suite with branch measurement | 94.71% total; 90% gate passed |

Important module coverage:

| Module | Coverage |
| --- | ---: |
| `core/views.py` | 96% |
| `core/services.py` | 94% |
| `core/models.py` | 92% |
| `core/serializers.py` | 91% |
| `core/signals.py` | 92% |
| `seed_demo.py` | 98% |

The threshold is below the measured baseline so regressions fail without encouraging assertion-free tests.

## Representative API

Product endpoints require authentication unless stated otherwise.

| Method and path | Behavior |
| --- | --- |
| `POST /api/dj-rest-auth/registration/` | Register |
| `POST /api/dj-rest-auth/login/` | Issue a token |
| `GET /api/me/` | Current profile summary |
| `GET /api/train-trips/` | List; filters `origin`, `destination`, `departure_date`, `status`, `ordering` |
| `GET /api/train-trips/{trip_id}/quote/` | Return option catalog and authoritative itemized demo quote |
| `POST /api/train-trips/{trip_id}/book/` | Idempotently create an owned ticket with server-calculated amount |
| `GET /api/tickets/` | List only owned tickets |
| `PATCH /api/tickets/{ticket_id}/` | Update permitted booking options |
| `DELETE /api/tickets/{ticket_id}/` | Delete/cancel an owned ticket |
| `POST /api/tickets/{ticket_id}/pay/` | Validate and record payment state |
| `GET /api/seats/{trip_id}/` | Full configured coach inventory with class and availability |
| `POST /api/seats/{trip_id}/` | Assign a seat to an owned ticket |
| `GET /api/notifications/` | List only owned notifications |
| `POST /api/notifications/{notification_id}/mark_read/` | Mark an owned notification read |
| `GET /healthz` | Public process liveness |
| `GET /readyz` | Public database readiness |

The schema is at `/api/schema/` and Swagger UI at `/api/docs/`.

## Security and reliability

- Token/session authentication and authenticated product endpoints
- Queryset ownership boundaries for tickets and notifications
- Server-controlled ownership, price, paid state, and payment method
- Validated payment/seat inputs with explicit `400`, `404`, and `409` behavior
- PostgreSQL row locking plus conditional uniqueness for seat integrity
- Production validation for secret key and allowed hosts
- Production-only HTTPS redirect, secure cookies, HSTS, and Nginx headers
- Explicit CORS and CSRF origins
- Console logging that does not print passwords or environment secrets
- Process, database, and web-server health checks
- Production override removes the database host port and source bind mount

[SECURITY.md](SECURITY.md) documents verified controls, threat boundaries, and remaining risks.

## Continuous integration

`.github/workflows/ci.yml` defines least-privilege jobs with concurrency cancellation, 15-minute timeouts, Python 3.12.9, Node.js 22.14.0, dependency caching, PostgreSQL 14, Django/migration checks, formatting, linting, dependency/security scans, coverage enforcement, integration tests, frontend tests, and a production build.

The workflow is local and unpushed. There is intentionally no badge or claim that GitHub-hosted execution passes.

## Environment configuration

- `.env.example` — safe Docker development defaults
- `backend/.env.example` — native backend/SQLite defaults
- `frontend/.env.example` — native React API base and optional non-secret build label
- `.env.production.example` — required production-oriented placeholders

Local `.env` files are ignored. Production rejects the documented demo secret and demo seeding. Never reuse demo credentials outside an isolated local environment.

## Known limitations and tradeoffs

- The frontend stores its DRF token in `localStorage`; same-origin XSS could steal it. Moving to HttpOnly cookies or short-lived access/refresh tokens requires an intentional auth-contract change.
- A legacy `.env.production` file is already tracked by Git. It was not opened or changed during this work. Before committing, verify privately whether it contains any live credential, rotate any such credential, preserve any needed local copy, and remove the file from tracking; ignore rules cannot retroactively untrack it.
- Create React App and its transitive development toolchain are aging. The production dependency audit reports two moderate React Router advisories. The open-redirect risk is limited by current hard-coded navigation targets, and the SSR advisory does not apply to this client-only build, but the packages remain unpatched.
- Payment lacks a provider, provider idempotency key, webhook verification, ledger, and refunds. The current booking key only deduplicates local ticket creation.
- Chat has legacy persistence but no authenticated backend API or frontend assistant.
- Email delivery, queues, metrics, tracing, backups, TLS termination, and deployment are not implemented.
- SQLite cannot prove PostgreSQL locking; the PostgreSQL tier is mandatory for booking-integrity changes.
- Trip listing has filtering and ordering but no pagination.
- Existing screenshots show historical sample dates and do not prove current backend state.

## Credible next steps

1. Migrate Create React App to Vite and adopt a patched router release with route regression tests.
2. Design a cookie-based auth migration with CSRF tests and an explicit compatibility plan.
3. Add pagination and query-count assertions for growing collections.
4. Expose user-scoped chat only after defining participants and moderation.
5. Add a mocked provider adapter, provider-scoped idempotency key, and verified webhook flow before describing payment as external processing.
6. Run CI remotely only after review and explicit push authorization.

## Production-oriented configuration

The production override is a baseline, not a deployment. Review [DEPLOYMENT.md](DEPLOYMENT.md), supply non-demo values, add TLS termination, backups, monitoring, and platform secrets, then validate in staging before release.

## License

Licensed under the [MIT License](LICENSE).
