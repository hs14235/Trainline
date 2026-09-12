# Security model

This document describes controls verified in the local repository as of September 11, 2026. It is not a penetration-test report, compliance attestation, or production-security certification.

## Trust boundaries

- The browser is untrusted. Ownership, amount, paid state, and seat conflicts are enforced by the API/database.
- Authentication tokens are bearer credentials and must not be logged or shared.
- PostgreSQL is authoritative for booking state.
- Docker development defaults are public demo values, not secrets.
- Production values must enter through the selected platform's configuration or secrets system.
- No live payment, email, AI, or other external provider is called by this revision.

## Verified controls

### Authentication and authorization

- dj-rest-auth and DRF token/session authentication protect product endpoints.
- Ticket querysets are scoped to `passenger__user=request.user`.
- Notification querysets are scoped to the current user.
- Booking derives its Passenger from the authenticated user.
- Seat assignment verifies ticket ownership and trip association.
- Payment locks and updates only an owned ticket.
- Serializer read-only fields reject direct writes to passenger, amount, paid state, and payment method.
- Tests cover anonymous access, owners, non-owners, invalid identifiers, and malformed payloads.

Scoped `404 Not Found` responses avoid confirming whether another user's object exists.

### Booking integrity

- Fare calculation is server-side.
- Seat strings are normalized and validated.
- Configured inventory is checked when Seat rows exist.
- PostgreSQL `SELECT ... FOR UPDATE` serializes assignments on the trip.
- A conditional uniqueness constraint prevents two non-empty seat assignments for one trip.
- A PostgreSQL concurrency test proves one winner and one conflict for simultaneous assignment.
- Payment uses a Ticket row lock and repeated payment returns `409 Conflict`.

### Configuration and secrets

- Local `.env` files are ignored.
- Example files contain only explicit demo values or placeholders.
- Production settings reject the documented development secret.
- Production Compose requires explicit database, origin, host, and API-base configuration.
- Demo seeding requires opt-in and is blocked in production.
- The seed command does not print the demo password and will not overwrite an existing identity.
- Logs use a standard console formatter and do not intentionally include credentials.

### Browser and transport controls

- Nginx sends `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, a referrer policy, and a Content Security Policy.
- Django enables secure cookies, HTTPS redirect, and HSTS in production mode.
- CORS and CSRF trusted origins are explicit environment values.
- The production Compose override removes PostgreSQL's host port and the backend source bind mount.

These settings assume a correctly configured TLS proxy. That boundary has not been deployed or verified.

## Dependency audit

The local Python dependency audit returned no known vulnerabilities after upgrading Django REST Framework to the resolved 3.17.2 release.

`npm audit --omit=dev --audit-level=high` exits successfully but still reports two moderate React Router advisories. The open-redirect advisory requires attacker-controlled arbitrary navigation input; current application navigation targets are hard-coded. The SSR advisory does not apply to this client-only Create React App build. This limits practical exposure but does not make the packages patched. A tested Vite/React Router migration remains required.

The complete frontend development tree reports 32 advisories (9 low, 9 moderate, and 14 high), inherited primarily through the aging Create React App toolchain. Do not use `npm audit fix --force` without reviewing the breaking Router 7/toolchain changes.

## Known risks

| Risk | Impact | Current mitigation | Recommended direction |
| --- | --- | --- | --- |
| Legacy tracked `.env.production` | A committed live credential would already be exposed to repository readers/history | File was not opened or altered; new `.env.*` ignore rule prevents future untracked variants from appearing | Privately inspect, rotate any live values, preserve a needed local copy, then remove from tracking/history through a reviewed Git operation |
| Token in `localStorage` | Same-origin XSS could steal a bearer token | CSP and no known arbitrary script injection path | Dedicated HttpOnly-cookie or short-lived-token migration |
| Aging CRA toolchain | Unpatched transitive development packages | Locked dependency tree and clean production build | Migrate to Vite and current lint/test tooling |
| Moderate router advisory | Crafted attacker-controlled destinations can redirect | Navigation destinations are hard-coded | Upgrade router with route regression tests |
| No endpoint-specific throttles | Auth/booking endpoints can consume global user limit | DRF user throttle of 2000/day | Add scoped login/booking/payment rates after workload review |
| Swagger is public | Endpoint metadata is discoverable | No credentials included | Decide whether production docs should require auth |
| Payment is state-only | No provider verification or financial guarantees | Product/docs label the limitation | Add provider adapter, idempotency, webhook verification, and ledger |
| No backup/restore automation | Database loss may be unrecoverable | None in repository | Platform backups plus measured restore exercise |
| No security monitoring | Abuse may not be detected promptly | Structured console logs only | Central logs, alerts, metrics, and retention policy |
| Seeded PII-like identifiers | Demo data could be mistaken for real data | Clearly prefixed demo values and reserved `.test` email | Keep seeding isolated and disabled in production |

## Reporting a vulnerability

Do not include credentials, tokens, personal data, or exploit traffic against a live system in a public issue. Provide:

- affected version or commit;
- endpoint/component;
- reproduction using synthetic local data;
- expected and actual behavior;
- impact and preconditions;
- suggested mitigation if known.

The repository currently has no dedicated private security-reporting address documented. Configure a private reporting channel before public deployment.

## Verification commands

~~~powershell
python scripts/tasks.py check
python scripts/tasks.py test
python scripts/tasks.py test-postgres
python scripts/tasks.py coverage
python scripts/tasks.py lint-backend
python scripts/tasks.py format-check
python scripts/tasks.py frontend-lint
python scripts/tasks.py frontend-test
python scripts/tasks.py frontend-build
.\.venv\Scripts\python.exe -m pip_audit -r backend\requirements.txt
Set-Location frontend
npm audit --omit=dev --audit-level=high
~~~

Passing these commands does not prove absence of vulnerabilities. Review authorization, data flow, dependencies, deployment configuration, and operational controls whenever behavior changes.

## Production checklist

- Replace every placeholder with platform-managed values.
- Keep debug disabled and demo seed disallowed.
- Terminate TLS correctly and review proxy headers.
- Restrict database networking.
- Rotate and revoke secrets through documented procedures.
- Add endpoint-appropriate abuse controls.
- Test backup restoration.
- Centralize logs without sensitive fields.
- Review the OpenAPI surface and disable unnecessary endpoints.
- Run dependency, static, dynamic, and manual security review in staging.
- Document incident response and responsible disclosure.
