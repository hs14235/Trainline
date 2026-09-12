# Repository audit report

**Audit date:** September 11, 2026

**Scope:** Local repository only

**Remote operations:** None

**Commit/deployment status:** Changes remain local and uncommitted; nothing was pushed, published, or deployed.

## Baseline findings

The initial repository contained a React/Create React App frontend, Django REST Framework backend, PostgreSQL Compose database, and models for users, passengers, trips, seats, tickets, payments, notifications, membership levels, and chat records.

Material baseline problems included:

- Docker development defaults could not start reliably because debug/secret behavior conflicted with production validation.
- Compose did not provide complete readiness ordering and production retained a source bind mount.
- Frontend API calls duplicated the `/api` path in several workflows.
- The seat UI bypassed the guarded assignment endpoint.
- Ticket passenger identifiers remained writable, enabling ownership manipulation.
- Ticket and notification access was insufficiently user-scoped.
- Seat conflicts lacked a database uniqueness constraint and robust shared locking.
- Payment and price state trusted more client input than necessary.
- There was no meaningful automated suite, coverage gate, frontend lockfile, CI workflow, or safe demo seed command.
- Native settings claimed a SQLite fallback while requiring `DATABASE_URL`.
- Documentation contained incorrect schema descriptions and unsupported security/deployment claims.

## Implemented phases

### Reproducible infrastructure

- Environment-aware settings with development, test, and production-oriented entry points
- Docker health checks and dependency ordering
- Isolated development and test PostgreSQL volumes
- Docker ignore rules that reduced frontend build context from about 777 MB to 1.18 MB
- Cross-platform task runner
- Deterministic frontend lockfile and constrained backend dependencies
- Liveness/readiness endpoints and secret-safe console logging

### Backend correctness and tests

- User-scoped ticket/notification access
- Server-derived passenger and fare
- Transactional booking/payment paths
- Central seat service with inventory validation, row locking, conflict semantics, and database uniqueness
- Safe preflight uniqueness migration
- 52 fast tests and 2 PostgreSQL tests
- 94.57% measured fast-suite coverage with a 90% threshold

### Demo and CI

- Idempotent, opt-in, production-blocked demo command with collision protection
- Local GitHub Actions workflow for backend and frontend validation
- Repository-specific `trainline-testing` skill and validation scripts

### Documentation

- Employer-facing README grounded in verified behavior
- Architecture diagrams and transaction flow
- Honest security and deployment boundaries
- Reviewed screenshot paths and useful captions

## Bugs discovered during final integration

1. An old Docker volume used credentials that differed from current Compose defaults. The old volume was preserved; a distinct development volume was introduced.
2. The frontend Docker context included local dependencies and caches. Docker ignore rules reduced it to 1.18 MB.
3. Nginx's hidden-file rule denied the SPA's internal `/index.html` redirect, making the frontend return 403. The rule now targets actual dot-prefixed path segments.
4. Demo passenger passport text exceeded PostgreSQL's `varchar(20)` despite passing SQLite tests. The value and regression test were corrected.
5. Payment row locking joined a nullable membership relation, which PostgreSQL rejects with `FOR UPDATE`. The nullable join was removed and a PostgreSQL regression test added.

## Verification summary

- Django checks and migration drift: pass
- Fast backend: 52 passed
- PostgreSQL integration: 2 passed
- Backend coverage: 94.57%, threshold pass
- Frontend lint: pass
- Frontend tests: 4 passed
- Frontend production build: pass
- Docker Compose build/start: three services healthy
- Local HTTP smoke flow: login/profile/filter/book/seat assign/conflict/payment pass
- Demo seed: passes twice against isolated PostgreSQL
- Python dependency audit: no known vulnerabilities
- Frontend production dependency audit: exits zero at the high threshold but reports two moderate advisories
- Legacy tracked `.env.production`: not inspected or changed; requires private credential review and untracking before commit
- Hosted CI and deployment: not run

Exact final command output and any remaining failure are reported in the task handoff and README.
