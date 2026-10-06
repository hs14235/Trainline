# Contributing to Trainline

Trainline is a portfolio engineering project, so a useful contribution must be understandable, testable, and honest about its verification boundary. Start with [README.md](README.md), [docs/architecture.md](docs/architecture.md), and [SECURITY.md](SECURITY.md).

## Local setup

The Docker quick start in the README is the supported full-stack path. Native development uses Python 3.12 and Node.js 22. Copy only the checked-in example environment files; never commit a populated `.env` file or paste secret values into an issue, command transcript, screenshot, or pull request.

## Change workflow

1. Confirm the branch and inspect `git status` before editing. Preserve unrelated tracked and untracked work.
2. Make the smallest coherent change. Keep fare calculation, ownership, payment state, seat assignment, and membership rules server-authoritative.
3. Add focused behavior tests for the changed contract. Do not weaken assertions or skip a valid test to obtain a green run.
4. Run the smallest relevant tier first, followed by the broader affected suite.
5. Review the final diff for secrets, local paths, generated files, personal data, and accidental artifacts.
6. State exactly what ran locally, what ran in hosted CI, and what remains unverified. Local Compose success is not production evidence.

## Test matrix

Run commands from the repository root:

| Change | Required verification |
| --- | --- |
| Backend model, serializer, service, API, auth, booking, payment, notification, or seat behavior | Focused `pytest` file, then `python scripts/tasks.py test` |
| Locking, transaction isolation, or PostgreSQL-specific behavior | `python scripts/tasks.py test-postgres` against its disposable test database |
| Frontend behavior | `python scripts/tasks.py frontend-test` and `python scripts/tasks.py frontend-lint` |
| Frontend imports, routing, environment variables, or production wiring | Frontend tests plus `python scripts/tasks.py frontend-build` |
| Repository-wide or release-candidate change | `python scripts/tasks.py verify`, followed by the PostgreSQL tier |

The PostgreSQL task rejects database names that do not contain `test`. Never point it at development, demo, staging, or production data.

## Review evidence

A reviewable change should include:

- the problem and intended observable behavior;
- the files and contracts changed;
- exact test commands and results;
- database, migration, security, deployment, or compatibility impact;
- remaining risks and unverified environments;
- screenshots only when they demonstrate rendered behavior, not as a substitute for tests.

See [docs/PUBLICATION_PLAN.md](docs/PUBLICATION_PLAN.md) for the current branch-integration boundary. Publishing, merging, deploying, and changing repository settings require separate explicit authorization.
