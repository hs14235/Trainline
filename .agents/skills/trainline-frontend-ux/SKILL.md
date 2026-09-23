---
name: trainline-frontend-ux
description: Inspect and refine the Trainline React frontend through rendered, responsive, accessibility-aware visual review and small browser-guided UX or styling changes. Use for Trainline screens, aesthetics, layout, responsive behavior, presentation accessibility, and live UI adjustment; do not use for unrelated repositories or backend-only work.
---

# Trainline Frontend UX

Operate only in the Trainline repository containing `frontend/package.json`,
`frontend/src/App.js`, `backend/manage.py`, and `docker-compose.yml`. Confirm the
repository root and inspect `git status` before making changes. Preserve unrelated
tracked and untracked work.

This skill supports iterative inspection and adjustment, not an unsolicited
full-site UX audit. Start with the screen, user journey, current state, and viewport
the user is looking at. If any is unstated, infer the smallest useful scope from the
request and rendered page; ask only when the answer would materially change the work.

Read [references/project-map.md](references/project-map.md) when locating a route,
component, selector, asset, API boundary, or runtime command. Reconfirm any fact that
may have changed since that map was written. Read
[references/visual-review-checklist.md](references/visual-review-checklist.md) when
performing visual feedback, responsive/accessibility QA, or final verification.

## Interactive loop

1. Inspect the rendered screen with browser/computer-use when available. Record the
   route, viewport, auth/data state, and visible evidence. Use source inspection to
   identify the exact route owner, component, and CSS selector; never infer ownership
   from appearance alone.
2. Classify the request as read-only feedback, presentation-only editing, or a
   behavior/API/data-contract change. Label findings as **confirmed rendered**,
   **source-confirmed**, or **unverified hypothesis**.
3. For feedback requests, return a small ranked set of concrete suggestions before
   editing. Use **Blocking**, **Important**, **Improvement**, and **Nit** priorities.
   Do not edit until the user authorizes changes. A direct request to change or fix
   the UI is authorization for the scoped local frontend edit.
4. Make the smallest coherent change in the owning frontend file. Preserve routes,
   API contracts, authentication behavior, backend field names, and the existing
   teal/green, photographic, translucent-surface design language unless the user
   explicitly requests a broader change.
5. Reinspect the affected state at representative desktop and mobile viewports. Check
   only relevant states and interactions, but include focus/keyboard behavior,
   readability/contrast, touch targets, loading/empty/error states, reduced motion,
   and overflow/layout regressions when the change could affect them.
6. Report the exact files, components/selectors, observed evidence, validation run,
   untested conditions, and remaining risks. Distinguish local implementation from
   committed, pushed, deployed, or production-verified status.

## Boundaries

- Keep purely visual work in the frontend. Do not silently turn copy, layout, or
  styling work into behavior, API, database, auth, or backend changes.
- Use the existing `trainline-testing` skill when behavior changes or the user asks
  for tests. Pure read-only visual feedback does not require broad automated suites;
  presentation-only edits still require focused rendered verification and a diff
  review.
- Do not seed or reset databases, add dependencies, modify lockfiles, run broad
  formatters, change containers or backend behavior, or alter shared contracts unless
  the user explicitly authorizes that task-specific expansion.
- Never commit, push, deploy, publish, or change external systems without explicit
  authorization for that exact action.
