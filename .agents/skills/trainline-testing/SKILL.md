---
name: trainline-testing
description: Select, run, and diagnose the appropriate test tier for the Trainline Django and React repository. Use for Trainline test execution, coverage, CI parity checks, flaky-test audits, and root-cause summaries; do not use for unrelated repositories.
---

# Trainline Testing

Operate only in the Trainline repository containing `backend/manage.py`,
`frontend/package.json`, `docker-compose.yml`, and `scripts/tasks.py`. Run
`python .agents/skills/trainline-testing/scripts/inspect_repo.py` first. Stop if
those sentinels do not identify one repository root.

## Select the smallest useful tier

- Model, serializer, or service change: run the relevant file under
  `backend/tests/` with `python -m pytest <path> -ra`.
- REST route, permission, authentication, booking, payment, notification, or
  seat behavior: run the relevant API test file, then `python scripts/tasks.py test`.
- Locking, transaction isolation, or PostgreSQL-specific behavior: start only
  the isolated `test-db` service from `docker-compose.test.yml`, set
  `TEST_DATABASE_URL` to that demo database, and run
  `python scripts/tasks.py test-postgres`. Stop the service afterward if this
  session started it.
- Frontend behavior: run `python scripts/tasks.py frontend-test`; add
  `frontend-build` when imports, routing, environment variables, or production
  bundling could be affected.
- Complete local verification or CI parity: run
  `python scripts/tasks.py verify`, then the PostgreSQL tier separately.

The fast suite uses an isolated in-memory SQLite test database. pytest-django
creates and migrates a separate test database for PostgreSQL; never point
`TEST_DATABASE_URL` at development, demo, staging, or production data. Do not
use `--reuse-db` unless the user asks for it and the database is confirmed to be
disposable.

## Diagnose truthfully

Capture the exact command, exit code, passed/failed/skipped counts, and coverage
when produced. Group failures by root cause rather than repeating every stack
trace. Distinguish the first causal failure from dependent failures, and
recommend the smallest safe change. Never call a suite passing when collection,
setup, migration, or a required tier failed.

After adding or materially changing tests, run
`python .agents/skills/trainline-testing/scripts/audit_tests.py`. Inspect every
reported skipped, sleep-based, network-dependent, assertion-free, or placeholder
test; the script reports candidates and does not prove test quality. Tests should
assert observable responses, permissions, database effects, or recovery—not
private implementation details.

Never delete, skip, loosen, or replace a valid test solely to obtain a green
result. Do not make live payment, email, AI, or other network calls. Mock external
boundaries. Do not commit, push, deploy, publish, alter remote state, or perform
destructive cleanup. Obtain explicit approval immediately before any external or
destructive action.
