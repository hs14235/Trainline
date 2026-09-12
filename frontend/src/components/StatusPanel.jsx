export function LoadingState({ label = 'Loading…' }) {
  return (
    <div className="state-panel state-panel--loading" role="status" aria-live="polite">
      <span className="spinner" aria-hidden="true" />
      <span>{label}</span>
    </div>
  );
}

export default function StatusPanel({
  title,
  message,
  variant = 'error',
  actionLabel,
  onAction,
  busy = false,
}) {
  const role = variant === 'error' || variant === 'warning' ? 'alert' : 'status';

  return (
    <section className={'state-panel state-panel--' + variant} role={role} aria-live="polite">
      <span className="state-panel__mark" aria-hidden="true">
        {variant === 'success' ? '✓' : variant === 'warning' ? '!' : variant === 'info' ? 'i' : '×'}
      </span>
      <div>
        <h2 className="state-panel__title">{title}</h2>
        {message && <p>{message}</p>}
        {onAction && (
          <button className="button button--secondary button--small" onClick={onAction} disabled={busy}>
            {busy ? 'Trying again…' : actionLabel}
          </button>
        )}
      </div>
    </section>
  );
}
