# Trainline frontend

The frontend is a React 18 single-page application using React Router 6 and Axios. It provides account entry, traveler-oriented trip discovery, server-quoted booking options, demo payment state, full server-backed seat inventory, membership progress, structured account updates, and a public Engineering page. It deliberately does not claim live timetable data, live chat, or monetary processing.

## Configuration

Copy `.env.example` to the ignored `.env` file. `REACT_APP_API_BASE` must be the backend origin without a trailing `/api` because endpoint modules add `/api/...` themselves. `REACT_APP_BUILD_VERSION` is an optional public label for the Engineering page; it must never contain a secret.

~~~powershell
Copy-Item .env.example .env
npm ci
npm start
~~~

The development UI runs at <http://localhost:3000>.

## Validation

The suite covers protected navigation, form validation and submission guards, async failure states, server-authoritative quote/payment presentation, stable seat maps and conflict recovery, membership rewards, and structured-update focus/read behavior.

~~~powershell
npm run lint
$env:CI = 'true'
npm test -- --watchAll=false
npm run build
~~~

From the repository root, the same operations are available as:

~~~powershell
python scripts/tasks.py frontend-lint
python scripts/tasks.py frontend-test
python scripts/tasks.py frontend-build
~~~

## Authentication boundary

The current client stores the DRF token in `localStorage` and sends it through Axios as an `Authorization: Token ...` header. The backend remains authoritative for ownership and payment/seat state. Token storage is a documented risk; changing it requires a coordinated backend/frontend authentication migration.

## Build and serving

`npm run build` creates the static `build` directory. The Dockerfile builds with Node.js 22 and serves the result from Nginx. Nginx supplies SPA fallback and security headers. A successful build does not by itself mean the application has been deployed.

## Known toolchain limitation

Create React App 5 is aging and its development dependency tree includes known advisories. The production audit also reports two moderate React Router advisories. Navigation destinations are currently hard-coded and this application does not use server-side rendering, which limits exposure to those specific advisories, but the dependencies are not patched. A tested migration to Vite and a current router is the recommended next step.

See the repository [README](../README.md) for full setup, architecture, API, measured results, and limitations.
