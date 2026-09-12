const buildLabel = process.env.REACT_APP_BUILD_VERSION || 'local / unknown';

export default function Engineering() {
  return (
    <div className="page-stack engineering-page">
      <header className="page-heading surface surface--hero">
        <p className="eyebrow">Engineering notes</p>
        <h1>Built as a complete booking system</h1>
        <p className="lede">
          This project connects a responsive React client to a Django REST API and PostgreSQL,
          with container health checks and database-backed booking safeguards.
        </p>
      </header>

      <section className="architecture-grid" aria-labelledby="system-boundaries">
        <h2 id="system-boundaries" className="section-heading">
          System boundaries
        </h2>
        <article className="surface engineering-card">
          <span className="engineering-card__number">01</span>
          <h3>React + Nginx</h3>
          <p>The browser owns interaction and presentation. Nginx serves the production build.</p>
        </article>
        <article className="surface engineering-card">
          <span className="engineering-card__number">02</span>
          <h3>Django REST Framework</h3>
          <p>The API owns identity, validation, fares, authorization, and booking transitions.</p>
        </article>
        <article className="surface engineering-card">
          <span className="engineering-card__number">03</span>
          <h3>PostgreSQL</h3>
          <p>
            Persistent relational state, uniqueness constraints, transactions, and row locks protect
            seat assignment.
          </p>
        </article>
      </section>

      <div className="engineering-split">
        <section className="surface" aria-labelledby="verification-heading">
          <p className="eyebrow">Locally verified · September 11, 2026</p>
          <h2 id="verification-heading">Verification baseline</h2>
          <ul className="check-list">
            <li>52 fast backend tests and 2 PostgreSQL integration tests</li>
            <li>94.57% measured backend branch coverage with a 90% gate</li>
            <li>Frontend lint, tests, production build, and three-service Compose health checks</li>
            <li>Liveness and database-readiness probes with dependency ordering</li>
          </ul>
          <p className="fine-print">
            Local verification is not a production availability, hosted CI, or security guarantee.
          </p>
        </section>

        <section className="surface" aria-labelledby="limits-heading">
          <p className="eyebrow">Deliberate boundaries</p>
          <h2 id="limits-heading">What this demo does not claim</h2>
          <ul className="plain-list">
            <li>Payment is an internal state transition, not monetary processing.</li>
            <li>The help guide is client-only and is not live support.</li>
            <li>Authentication tokens currently remain in localStorage.</li>
            <li>The CI workflow exists locally but has not run remotely.</li>
            <li>No public deployment, uptime record, or Kubernetes configuration exists.</li>
          </ul>
        </section>
      </div>

      <section className="surface future-path" aria-labelledby="future-heading">
        <div>
          <p className="eyebrow">Learning path</p>
          <h2 id="future-heading">Kubernetes comes later, with evidence</h2>
          <p>
            Trainline is prepared as a containerized application capstone. Kubernetes integration is
            intentionally deferred until the separate hands-on CKA work establishes the operational
            foundation to design, test, and explain it honestly.
          </p>
        </div>
        <dl className="build-meta">
          <div>
            <dt>Client build</dt>
            <dd>{buildLabel}</dd>
          </div>
          <div>
            <dt>Architecture</dt>
            <dd>React → DRF → PostgreSQL</dd>
          </div>
        </dl>
      </section>
    </div>
  );
}
