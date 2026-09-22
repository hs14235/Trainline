# Visual review and verification

Use the relevant slices of this checklist; do not turn a focused request into a
full-product audit.

## Establish evidence

Record:

- route/screen and the journey step being evaluated;
- viewport dimensions and browser surface;
- authenticated/anonymous state and meaningful data state;
- whether the evidence is **confirmed rendered**, **source-confirmed**, or an
  **unverified hypothesis**.

Screenshots and browser inspection confirm presentation at the observed viewport and
state only. Source inspection can confirm ownership and potential concerns, but not
pixel output. If the UI cannot run, say so and keep conclusions source-confirmed or
hypothetical.

## Priority model

- **Blocking**: prevents completing the primary journey, hides essential content,
  creates an inaccessible interaction, or causes severe overlap/overflow/data-state
  confusion.
- **Important**: materially harms comprehension, responsive use, keyboard operation,
  state clarity, or visual hierarchy but leaves a workaround.
- **Improvement**: meaningful polish, consistency, readability, or efficiency gain.
- **Nit**: minor cosmetic inconsistency with little user impact.

For feedback, return the few highest-value findings first. Each finding should name
the priority, evidence class, viewport/state, exact owner, observed impact, and a
specific smallest fix. Do not inflate speculative concerns.

## Responsive and layout checks

- Inspect one representative desktop viewport (for example 1440x900) and one mobile
  viewport (for example 390x844). Add a tablet/intermediate viewport only when the
  layout or request warrants it.
- When editing breakpoint behavior, inspect both sides of the relevant current
  thresholds: 900px and 650px in `App.css`, and 700px in `index.css`.
- Check horizontal overflow, clipped content, sticky header/sidebar collisions,
  background cropping, long station/user/error text, card/grid reflow, footer and
  fixed utility-widget overlap, safe scrolling, and browser zoom where relevant.
- Confirm interactive targets remain comfortably usable on touch; use 44 CSS pixels
  as the default minimum target expectation unless the surrounding control provides
  an equivalent hit area.

## Accessibility presentation and interaction

- Traverse the changed flow by keyboard in logical order. Confirm visible focus,
  skip-link behavior when relevant, no keyboard traps, and that focus is not obscured
  by sticky/fixed UI.
- Confirm labels, headings, landmarks, link/button semantics, current/expanded/pressed
  states, and status/error announcements remain understandable.
- Check text and meaningful UI contrast against the actual rendered background,
  including photography and translucency. Do not claim WCAG conformance from visual
  judgment alone; measure when making a compliance claim.
- Check that information is not conveyed by color alone and that disabled, selected,
  error, warning, and success states remain distinguishable.
- With reduced motion enabled, confirm page entrance/spinner/transition behavior does
  not depend on motion and respects the global reduction rule.

## State and journey checks

Inspect only states affected by the work, drawing from:

- initial loading and delayed responses;
- empty results/tickets/notifications/seats;
- validation, network, timeout, authorization, not-found, conflict, and service
  errors;
- pending/disabled mutation controls and duplicate-submission prevention;
- success/completion and already-completed states;
- long or missing API values and the authenticated/anonymous navigation variants.

For the primary booking path, preserve the visible relationship between discovery,
options, server-confirmed amount, demo-payment disclosure, seat availability, and the
dashboard. Aesthetic changes must not imply that payment moves money or that the
client owns price or seat truth.

## Closeout format

Report:

1. **Changed:** exact files plus owning components/selectors and the user-visible
   effect.
2. **Observed:** route, viewport/state, and confirmed rendered evidence.
3. **Validated:** browser interactions and exact automated commands/results, if any.
4. **Not verified:** unavailable states, browsers, data, or environments.
5. **Remaining risk:** only concrete residual concerns, with their evidence class.

Review `git status --short`, the focused diff under the skill/task scope, and
`git diff --check`. Confirm no unrelated files, secrets, dependencies, lockfiles, or
backend contracts changed. Never describe local work as committed, pushed, deployed,
or production-verified unless separately authorized and actually confirmed.
