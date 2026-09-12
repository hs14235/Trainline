# Security review summary

The current, evidence-backed security model is maintained in [SECURITY.md](SECURITY.md).

The earlier version of this file claimed that every issue was fixed, the application was production-ready, CodeQL had zero alerts, and all dependencies had zero vulnerabilities. Those claims were not supported by reproducible evidence and have been withdrawn.

As of September 11, 2026:

- ownership checks and IDOR regression tests cover tickets, seats, payments, and notifications;
- PostgreSQL locking and a uniqueness constraint protect seat assignment;
- production settings fail closed on demo secrets and disable demo seeding;
- the local Python audit reports no known vulnerabilities;
- the frontend production dependency audit still reports two moderate React Router advisories;
- the local test/build/Compose checks pass, but hosted CI, deployment, TLS, backups, monitoring, penetration testing, and CodeQL have not been verified.

See [README.md](README.md) for exact local results and [DEPLOYMENT.md](DEPLOYMENT.md) for the remaining release boundary.
