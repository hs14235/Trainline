# Deployment-oriented configuration

Trainline is not deployed from this revision. The repository contains a production-oriented Docker Compose override that provides safer process and container defaults, but an actual production release still requires a target platform, TLS termination, managed secrets, backups, monitoring, and staging validation.

## What the production override changes

Combining `docker-compose.yml` and `docker-compose.prod.yml`:

- requires explicit PostgreSQL identity and password values;
- requires a non-demo Django secret;
- selects `booking.settings_production` and disables debug mode;
- fails startup if production debug is enabled or if any payment mode other than the implemented simulated demo mode is requested;
- runs Gunicorn instead of Django's development server;
- removes the backend source bind mount;
- removes the PostgreSQL host port;
- runs migrations and collects static files at startup;
- enables HTTPS redirect, secure cookies, and HSTS;
- requires explicit hosts, CORS origins, CSRF origins, and frontend API base.

It does not configure a public reverse proxy, certificates, DNS, cloud resources, backups, log aggregation, metrics, or alerts.

## Runtime and persistence model

Trainline cannot run on static hosting alone. The compiled React bundle is static, but authenticated requests, authorization, fare calculation, booking transactions, and readiness checks require a continuously executable Django service. Users, trips, tickets, seat assignments, payments, and notifications require durable PostgreSQL storage.

A provider-neutral deployment therefore needs three responsibilities:

1. **Web edge:** serve the React build through Nginx, a static host, or a CDN and route browser traffic to the API origin.
2. **Application compute:** run the Django/Gunicorn container with private database connectivity and enough lifecycle support to run migrations deliberately.
3. **Persistent data:** run PostgreSQL on durable storage with automated backups, restore testing, and credentials supplied outside the image.

The frontend and Django images should be replaceable and stateless. User uploads are not part of the current product; if they are added later, they must use durable object storage rather than a container filesystem. PostgreSQL is the stateful recovery boundary.

## Required configuration names

Supply values through the selected platform's secret or configuration system. The authoritative placeholder list is `.env.production.example`; required deployment concerns include `DJANGO_SECRET_KEY`, database connection variables, `ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`, `CSRF_TRUSTED_ORIGINS`, and `REACT_APP_API_BASE`. `REACT_APP_BUILD_VERSION` is optional, public build metadata and must never contain a secret.

Do not copy a development `.env` file into an image. Build-time React variables are visible to every browser user and are configuration, not secret storage.

## Validate configuration locally

Never put real credentials in a command, committed file, screenshot, or support log. Copy the placeholder file to an ignored local file and replace every placeholder with environment-specific values:

~~~powershell
Copy-Item .env.production.example .env
~~~

Validate the merged configuration before starting anything:

~~~powershell
docker compose -f docker-compose.yml -f docker-compose.prod.yml config --quiet
~~~

Start only in a disposable local/staging environment:

~~~powershell
docker compose -f docker-compose.yml -f docker-compose.prod.yml up --build --detach --wait
docker compose -f docker-compose.yml -f docker-compose.prod.yml ps
~~~

Stop without deleting volumes:

~~~powershell
docker compose -f docker-compose.yml -f docker-compose.prod.yml down
~~~

Do not add `--volumes` unless deleting the exact environment's database is intentional and a verified backup exists.

## Pre-release acceptance criteria

- `python scripts/tasks.py verify` passes on the intended Python and Node baselines.
- `python scripts/tasks.py test-postgres` passes against an isolated PostgreSQL database.
- `python manage.py check --deploy --settings booking.settings_production` is reviewed with the real proxy/TLS boundary.
- `python manage.py makemigrations --check --dry-run` reports no drift.
- The production Compose merge contains no source bind mount or database host port.
- The secret key, database password, allowed hosts, CORS origins, and CSRF origins come from the target platform's secret/config system.
- TLS terminates at a trusted reverse proxy/load balancer and forwards the original scheme correctly.
- Backup creation and restore are tested, not merely configured.
- Health endpoints are wired into platform probes.
- Logs omit tokens, passwords, payment data, and environment secrets.
- Database migrations have been rehearsed against a copy of representative data.
- Rollback ownership and incident-response contacts are defined.
- Frontend `REACT_APP_API_BASE` is the exact deployed API origin.
- Demo seeding remains disabled.

## Temporary deployment demo data

The seed command may be used for a short-lived portfolio deployment only when its PostgreSQL database is brand new, disposable, and contains no copied local, customer, or other real data. Do not point it at a shared, staging, or production database. The command is additive and idempotent; it has no reset or delete path.

Keep `ALLOW_DEMO_SEED=False` and `ALLOW_DEPLOYMENT_DEMO_SEED=False` during normal runtime. For the one-time seed, temporarily provide both flags as `True` through the hosting platform, provide a unique synthetic username, an email ending in `.example.test`, and a separate demo-login password stored as a secret. Then run:

~~~text
python manage.py seed_demo --temporary-deployment-demo
~~~

The command checks the database before writing and aborts if it finds application records outside its deterministic demo scope. It also refuses the public local-development password. After a successful seed, restore both flags to `False`; the demo account remains usable without leaving seed access enabled. Never place the actual demo password in a repository file, command transcript, screenshot, or log.

`PAYMENT_MODE=demo` is mandatory for this application revision. A successful payment request changes only simulated application state; there is no payment-provider integration and no financial information should be entered. The application rejects any unimplemented live payment mode during startup.

## Platform mapping

A straightforward managed architecture could map the static frontend to object storage/CDN, the Django image to a managed container runtime, and PostgreSQL to a managed database. Exact AWS, Azure, or other services should be selected only after cost, networking, operational ownership, and deployment requirements are known.

Free and trial tiers commonly impose sleeping services, cold starts, CPU or memory quotas, limited build minutes, database expiry or storage caps, ephemeral local filesystems, and network-egress limits. These are evaluation criteria rather than claims about a particular provider; confirm the current official limits before selecting one. A sleeping API can legitimately cause the frontend's calm service-starting/unavailable state until readiness returns.

## Release, networking, and operations checklist

- Run database migrations as a controlled release step before directing traffic to incompatible application code; do not let multiple replicas race to migrate.
- Build immutable frontend and backend images. Collect Django static assets during the image or release process, not into an ephemeral runtime directory that must survive restarts.
- Terminate TLS at a trusted ingress or load balancer, preserve the original scheme, and validate secure-cookie and redirect behavior through that exact proxy chain.
- Set CORS and CSRF allowlists to the exact deployed origins. Do not use wildcard origins with credentials.
- Configure `/healthz` for process liveness and `/readyz` for database-aware readiness with conservative probe intervals and timeouts.
- Send structured application and proxy logs to durable aggregation while excluding credentials, tokens, personal data, and payment payloads.
- Define PostgreSQL backup frequency, retention, encryption, and a tested restore procedure before treating data as durable.
- Retain the previous application image and document whether each migration permits rollback or requires forward repair.
- Rehearse a failed release in staging: stop routing traffic, restore the prior image, and verify schema/application compatibility.

## Local-only demonstration path

Docker Compose remains the zero-provider demonstration path. It builds all three services, keeps PostgreSQL in a named local volume, orders startup through health/readiness checks, and exposes only localhost ports. Use the Docker quick-start commands in `README.md`; do not expose those ports through a tunnel or public firewall rule.

Kubernetes is intentionally deferred. It may become a later learning and capstone integration after the application behavior is stable, but it is not required for a credible first deployment and no Kubernetes support is claimed in this revision.

## Database migration safety

Migration `0003_ticket_unique_trip_seat` scans for duplicate non-empty seat assignments before adding the constraint. If duplicates exist, it aborts and prints limited identifying examples. Resolve those records through an approved data-remediation plan; do not delete or rewrite production bookings automatically.

## Health endpoints

- `GET /healthz` confirms the Django process can respond.
- `GET /readyz` confirms the process can query its database.
- The frontend container probes its own Nginx root.

These checks are necessary but do not replace transaction-level synthetic monitoring.

## Rollback and recovery

No automated deployment or rollback pipeline is included. Before the first release, define:

1. how the previous application image is retained and restored;
2. which migrations are reversible and which require forward repair;
3. where database backups live and how restore is tested;
4. who can rotate secrets and revoke credentials;
5. how user-visible incidents are detected and communicated.

## Current verification boundary

The development stack and its health checks passed locally on September 11, 2026. The production override has not been deployed or proven behind a real TLS proxy. No production-readiness or uptime claim should be made from the local result alone.
