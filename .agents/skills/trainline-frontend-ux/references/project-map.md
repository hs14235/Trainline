# Current Trainline frontend map

Verified against the `Trainline-Codex` checkout at commit `3a76498` on 2026-09-16.
Treat this as a navigation aid, not permanent truth: inspect the current checkout and
focused diff before relying on it.

## Runtime shape

- `frontend/package.json`: React 18, Create React App (`react-scripts` 5.0.1), React
  Router 6.30.6, Axios, and React Testing Library. This is not a Vite frontend.
- `frontend/src/index.js`: mounts `App` inside `BrowserRouter`.
- `docker-compose.yml`: PostgreSQL 14 (`db`) -> Django development server on port
  8000 (`backend`) -> Nginx-served React production build on port 3000 (`frontend`).
  The browser calls Django directly; Nginx does not proxy API requests.
- `frontend/src/api.js`: owns the Axios API base, token and CSRF request headers,
  readiness probe, timeouts, and user-facing API error normalization. The API client
  uses `${REACT_APP_API_BASE}/api`; the default origin is `http://127.0.0.1:8000`.
- `frontend/src/App.js`: owns authentication state from the `localStorage` token,
  protected routing, site header/navigation, route-change main-content focus, footer,
  and authenticated utility widgets. Do not change the token contract as a styling
  task.

## Active routes and owners

| Route | Owner | Purpose |
| --- | --- | --- |
| `/login` | `frontend/src/pages/Login.js` | Sign-in form and token handoff |
| `/register` | `frontend/src/pages/Register.js` | Local account registration |
| `/engineering` | `frontend/src/pages/Engineering.js` | Public verified architecture/limitations page |
| `/` | `frontend/src/Home.js` | Protected dashboard, membership summary, owned tickets |
| `/flights`, `/trips` | `frontend/src/Flights.js` | Protected trip filtering and discovery; `/trips` is an alias |
| `/book/:flightId` | `frontend/src/pages/BookFlight.js` | Step 1: ticket options and booking creation |
| `/payment/:ticketId` | `frontend/src/pages/PaymentPage.js` | Step 2: demo-only payment-state transition |
| `/select-seat/:ticketId` | `frontend/src/pages/SeatSelect.js` | Step 3: server-backed seat availability and assignment |

`frontend/src/Tickets.js`, `frontend/src/Profile.js`, and
`frontend/src/components/Register.jsx` are not mounted by the current route tree.
Confirm callers before treating any unmounted legacy component as a UI owner.

## Presentation ownership

- `frontend/src/index.css`: design tokens, type defaults, focus outline, page
  photographs/body overlays, base element behavior, the 700px background rule, and
  global reduced-motion handling.
- `frontend/src/App.css`: shell/navigation/footer, surfaces, buttons, forms, status
  panels, dashboard/trip cards, booking journey, payment and seat layouts, Engineering
  page, and utility widgets. Its main responsive breakpoints are 900px and 650px.
- `frontend/public/train-home.jpg`, `train-login.jpg`, `train-signup.jpg`,
  `trip-booking.jpg`, and `trainpayment.jpg`: current page background assets selected
  through body classes applied by route owners.
- Shared state UI: `frontend/src/components/StatusPanel.jsx` and `LoadingState`.
- Persistent authenticated utilities:
  `frontend/src/components/NotificationWidget.jsx` and `ChatWidget.jsx`; the latter is
  a client-only booking guide, not live chat.
- `frontend/src/components/ServiceStatus.jsx`: footer readiness indicator using
  `/readyz`.

The visual language currently uses teal/green tokens, photographic backgrounds,
high-opacity translucent surfaces, rounded cards, compact status chips, and a bright
mint accent. Prefer the existing variables and component classes over one-off colors
or a parallel component system.

## Journey and state boundaries

The primary authenticated path is trip discovery -> booking options -> demo payment
state -> seat selection -> dashboard. The API, not the browser, owns authoritative
fare calculation, identity/authorization, booking creation, payment validation, and
seat assignment. Visual changes must preserve loading, empty, error, conflict,
pending, disabled, and success states around those calls.

Relevant focused tests are in `frontend/src/App.test.js`, `Flights.test.js`,
`Home.test.js`, `pages/AuthFlows.test.js`, `pages/BookingFlow.test.js`,
`pages/SeatSelect.test.js`, and `components/ServiceStatus.test.js`. Use the
`trainline-testing` skill to choose test scope when behavior changes or tests are
requested.

## Start and inspect

Preferred full-stack path, when the user authorizes starting local services and the
required local configuration already exists:

```powershell
docker compose up --build --detach --wait
docker compose ps
```

Open `http://localhost:3000`. Do not seed or reset data as part of visual work. If an
authenticated state is required, use only an already available user-provided/local
session or ask the user to prepare one.

For a native frontend against an already running backend:

```powershell
Set-Location frontend
npm.cmd start
```

Repository task entry points include `python scripts/tasks.py frontend-lint`,
`frontend-test`, and `frontend-build`. Follow `trainline-testing` for behavior-related
test selection. Checked-in README screenshots are historical reference images, not
proof of the current rendered UI.
