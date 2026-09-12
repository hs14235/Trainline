import { useCallback, useEffect, useState } from 'react';
import { Link, useLocation, useParams } from 'react-router-dom';

import api, { describeApiError } from '../api';
import StatusPanel, { LoadingState } from '../components/StatusPanel';

export default function PaymentPage() {
  const { ticketId } = useParams();
  const location = useLocation();
  const [ticket, setTicket] = useState(null);
  const [method, setMethod] = useState('');
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const [outcome, setOutcome] = useState(null);

  useEffect(() => {
    document.body.classList.add('bg-payment');
    return () => document.body.classList.remove('bg-payment');
  }, []);

  const loadTicket = useCallback(async (signal) => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.get('/tickets/' + ticketId + '/', { signal });
      setTicket(response.data);
      if (response.data.paid) setOutcome('already-paid');
    } catch (requestError) {
      if (requestError?.code !== 'ERR_CANCELED') {
        setError(describeApiError(requestError, 'Ticket details could not be loaded.'));
      }
    } finally {
      if (!signal?.aborted) setLoading(false);
    }
  }, [ticketId]);

  useEffect(() => {
    const controller = new AbortController();
    loadTicket(controller.signal);
    return () => controller.abort();
  }, [loadTicket]);

  const handlePay = async (event) => {
    event.preventDefault();
    if (submitting || ticket?.paid) return;
    if (!method) {
      setError({
        title: 'Choose a demo payment method',
        message: 'Select how this internal ticket state should be recorded.',
      });
      return;
    }

    setSubmitting(true);
    setError(null);
    try {
      await api.post('/tickets/' + ticketId + '/pay/', { payment_method: method });
      setTicket((current) => ({ ...current, paid: true, payment_method: method }));
      setOutcome('paid');
    } catch (requestError) {
      if (requestError.response?.status === 409) {
        setTicket((current) => ({ ...current, paid: true }));
        setOutcome('already-paid');
      } else {
        setError(describeApiError(requestError, 'The demo payment state could not be updated.'));
      }
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) return <LoadingState label="Loading server-confirmed ticket amount…" />;
  if (!ticket && error) {
    return (
      <StatusPanel
        title={error.title}
        message={error.message}
        actionLabel="Retry ticket"
        onAction={() => loadTicket()}
      />
    );
  }

  const amount = Number(ticket.amount || location.state?.amount || 0);

  return (
    <div className="page-stack payment-page">
      <ol className="journey-steps" aria-label="Booking progress">
        <li className="journey-steps__complete"><span>✓</span>Options</li>
        <li className="journey-steps__current" aria-current="step"><span>2</span>Demo payment</li>
        <li><span>3</span>Seat</li>
      </ol>

      <div className="payment-layout">
        <header className="surface payment-summary">
          <p className="eyebrow">Ticket #{ticketId}</p>
          <h1>{outcome ? 'Payment state recorded' : 'Review demo payment'}</h1>
          <p className="payment-amount">
            <span>Server-confirmed amount</span>
            <strong>{'$'}{Number.isFinite(amount) ? amount.toFixed(2) : '0.00'}</strong>
          </p>
          <p className="demo-disclosure">
            <strong>Portfolio demo:</strong> this updates an internal ticket state only. No money,
            card data, payment provider, or financial account is involved.
          </p>
        </header>

        <section className="surface" aria-labelledby="payment-action-heading">
          {outcome === 'paid' && (
            <StatusPanel
              title="Demo payment marked successful"
              message="The backend recorded this ticket as paid. You can now select an available seat."
              variant="success"
            />
          )}
          {outcome === 'already-paid' && (
            <StatusPanel
              title="This ticket is already paid"
              message="No second mutation was attempted. Continue to seat selection or return to your dashboard."
              variant="info"
            />
          )}

          {!outcome && (
            <form onSubmit={handlePay}>
              <p className="eyebrow">Internal validation</p>
              <h2 id="payment-action-heading">Choose a recorded method</h2>
              <fieldset className="payment-methods" disabled={submitting}>
                <legend className="sr-only">Demo payment method</legend>
                <label>
                  <input
                    type="radio"
                    name="payment-method"
                    value="cash"
                    checked={method === 'cash'}
                    onChange={(event) => setMethod(event.target.value)}
                  />
                  <span><strong>Cash</strong><small>Demo record only</small></span>
                </label>
                <label>
                  <input
                    type="radio"
                    name="payment-method"
                    value="credit_card"
                    checked={method === 'credit_card'}
                    onChange={(event) => setMethod(event.target.value)}
                  />
                  <span><strong>Credit card label</strong><small>No card details are collected</small></span>
                </label>
                <label>
                  <input
                    type="radio"
                    name="payment-method"
                    value="check"
                    checked={method === 'check'}
                    onChange={(event) => setMethod(event.target.value)}
                  />
                  <span><strong>Check</strong><small>Demo record only</small></span>
                </label>
              </fieldset>
              {error && <StatusPanel title={error.title} message={error.message} variant="error" />}
              <button className="button button--accent button--large button--full" type="submit" disabled={submitting}>
                {submitting ? 'Recording payment state…' : 'Confirm demo payment'}
              </button>
            </form>
          )}

          {outcome && (
            <div className="completion-actions">
              {!ticket.seat_num && (
                <Link className="button button--accent" to={'/select-seat/' + ticketId}>
                  Choose a seat
                </Link>
              )}
              <Link className="button button--secondary" to="/">Return to dashboard</Link>
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
