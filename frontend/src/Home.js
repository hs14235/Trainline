import { useCallback, useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';

import api, { describeApiError } from './api';
import StatusPanel, { LoadingState } from './components/StatusPanel';

function TicketCard({ ticket, busyAction, onAddOption, onCancel, cancelPending, setCancelPending }) {
  const trip = ticket.train_trip || ticket.flight || {};
  const serviceNumber = trip.service_number ?? trip.flight_number ?? 'Not assigned';
  const route = [trip.origin_station, trip.destination_station].filter(Boolean).join(' → ');

  return (
    <article className="ticket-card">
      <div className="ticket-card__topline">
        <div>
          <p className="eyebrow">Ticket #{ticket.ticket_id}</p>
          <h3>Service {serviceNumber}</h3>
          <p className="ticket-card__route">{route || 'Trip details unavailable'}</p>
        </div>
        <span className={'status-chip ' + (ticket.paid ? 'status-chip--success' : 'status-chip--pending')}>
          <span aria-hidden="true">{ticket.paid ? '✓' : '•'}</span>
          {ticket.paid ? 'Paid' : 'Payment pending'}
        </span>
      </div>

      <dl className="ticket-facts">
        <div>
          <dt>Seat</dt>
          <dd>{ticket.seat_num || 'Not selected'}</dd>
        </div>
        <div>
          <dt>Amount</dt>
          <dd>{'$'}{Number(ticket.amount || 0).toFixed(2)}</dd>
        </div>
        <div>
          <dt>Booked</dt>
          <dd>{ticket.booked_at ? new Date(ticket.booked_at).toLocaleDateString() : '—'}</dd>
        </div>
        <div>
          <dt>Method</dt>
          <dd>{ticket.payment_method ? ticket.payment_method.replace('_', ' ') : '—'}</dd>
        </div>
      </dl>

      <ul className="option-tags" aria-label="Trip options">
        {ticket.priority_boarding && <li>Sleeping coach</li>}
        {ticket.meal && <li>Onboard meal</li>}
        {ticket.accommodation && <li>Accessible coach</li>}
        {ticket.taxi && <li>Taxi on arrival</li>}
        {!ticket.priority_boarding &&
          !ticket.meal &&
          !ticket.accommodation &&
          !ticket.taxi && <li className="option-tags__empty">No extras selected</li>}
      </ul>

      <div className="ticket-actions">
        {!ticket.paid && (
          <Link className="button" to={'/payment/' + ticket.ticket_id}>
            Review demo payment
          </Link>
        )}
        {!ticket.seat_num && (
          <Link className="button button--secondary" to={'/select-seat/' + ticket.ticket_id}>
            Choose seat
          </Link>
        )}
        {!ticket.paid && !ticket.meal && (
          <button
            className="button button--quiet"
            onClick={() => onAddOption(ticket.ticket_id, 'meal')}
            disabled={Boolean(busyAction)}
          >
            {busyAction === 'meal' ? 'Adding meal…' : 'Add meal'}
          </button>
        )}
        <button
          className="button button--danger-quiet"
          onClick={() => setCancelPending(ticket.ticket_id)}
          disabled={Boolean(busyAction)}
          aria-expanded={cancelPending === ticket.ticket_id}
        >
          Cancel ticket
        </button>
      </div>

      {cancelPending === ticket.ticket_id && (
        <div className="confirm-panel" role="alert">
          <div>
            <strong>Cancel this ticket?</strong>
            <p>This removes the booking and releases its selected seat. This cannot be undone here.</p>
          </div>
          <div className="confirm-panel__actions">
            <button
              className="button button--danger"
              onClick={() => onCancel(ticket.ticket_id)}
              disabled={busyAction === 'cancel'}
            >
              {busyAction === 'cancel' ? 'Cancelling…' : 'Yes, cancel ticket'}
            </button>
            <button
              className="button button--quiet"
              onClick={() => setCancelPending(null)}
              disabled={busyAction === 'cancel'}
            >
              Keep ticket
            </button>
          </div>
        </div>
      )}
    </article>
  );
}

export default function Home() {
  const [user, setUser] = useState(null);
  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [profileError, setProfileError] = useState(null);
  const [ticketsError, setTicketsError] = useState(null);
  const [actionError, setActionError] = useState(null);
  const [busyByTicket, setBusyByTicket] = useState({});
  const [cancelPending, setCancelPending] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    document.body.classList.add('bg-home');
    return () => document.body.classList.remove('bg-home');
  }, []);

  const loadDashboard = useCallback(async (signal) => {
    setLoading(true);
    setProfileError(null);
    setTicketsError(null);

    const [profileResult, ticketsResult] = await Promise.allSettled([
      api.get('/me/', { signal }),
      api.get('/tickets/', { signal }),
    ]);

    if (profileResult.status === 'fulfilled') {
      setUser(profileResult.value.data);
    } else if (profileResult.reason?.code !== 'ERR_CANCELED') {
      setProfileError(describeApiError(profileResult.reason, 'Profile details could not be loaded.'));
    }

    if (ticketsResult.status === 'fulfilled') {
      setTickets(ticketsResult.value.data);
    } else if (ticketsResult.reason?.code !== 'ERR_CANCELED') {
      setTicketsError(describeApiError(ticketsResult.reason, 'Tickets could not be loaded.'));
    }

    setLoading(false);
  }, []);

  useEffect(() => {
    if (!localStorage.getItem('token')) {
      navigate('/login');
      return undefined;
    }

    const controller = new AbortController();
    loadDashboard(controller.signal);
    return () => controller.abort();
  }, [loadDashboard, navigate]);

  const setBusyAction = (ticketId, action) => {
    setBusyByTicket((current) => ({ ...current, [ticketId]: action }));
  };

  const clearBusyAction = (ticketId) => {
    setBusyByTicket((current) => {
      const next = { ...current };
      delete next[ticketId];
      return next;
    });
  };

  const addOption = async (ticketId, field) => {
    if (busyByTicket[ticketId]) return;
    setActionError(null);
    setBusyAction(ticketId, field);
    try {
      const response = await api.patch('/tickets/' + ticketId + '/', { [field]: true });
      setTickets((current) =>
        current.map((ticket) => (ticket.ticket_id === ticketId ? response.data : ticket))
      );
    } catch (error) {
      setActionError(describeApiError(error, 'The ticket option could not be added.'));
    } finally {
      clearBusyAction(ticketId);
    }
  };

  const cancelTicket = async (ticketId) => {
    if (busyByTicket[ticketId]) return;
    setActionError(null);
    setBusyAction(ticketId, 'cancel');
    try {
      await api.delete('/tickets/' + ticketId + '/');
      setTickets((current) => current.filter((ticket) => ticket.ticket_id !== ticketId));
      setCancelPending(null);
    } catch (error) {
      setActionError(describeApiError(error, 'The ticket could not be cancelled.'));
    } finally {
      clearBusyAction(ticketId);
    }
  };

  const displayName = user?.first_name || user?.username || user?.email?.split('@')[0] || 'traveller';

  return (
    <div className="page-stack">
      <header className="dashboard-hero surface surface--hero">
        <div>
          <p className="eyebrow">Your rail dashboard</p>
          <h1>Welcome back, {displayName}</h1>
          <p className="lede">
            Find a service, review server-calculated booking details, and manage only the tickets
            connected to your account.
          </p>
        </div>
        <Link className="button button--accent button--large" to="/flights">
          Find your next train
          <span aria-hidden="true">→</span>
        </Link>
      </header>

      {profileError ? (
        <StatusPanel
          title={profileError.title}
          message="Your tickets may still be available below. Retry to restore membership details."
          actionLabel="Retry dashboard"
          onAction={() => loadDashboard()}
        />
      ) : (
        <section className="membership-strip surface" aria-label="Membership summary">
          <div>
            <span className="membership-strip__label">Membership</span>
            <strong>{user?.membership_level || 'Bronze'}</strong>
          </div>
          <div>
            <span className="membership-strip__label">Points</span>
            <strong>{user?.membership_points ?? 0}</strong>
          </div>
          <p>Membership changes are calculated by the backend after eligible paid trips.</p>
        </section>
      )}

      <section aria-labelledby="tickets-heading">
        <div className="section-intro">
          <div>
            <p className="eyebrow">Account-scoped data</p>
            <h2 id="tickets-heading">Your tickets</h2>
          </div>
          <span className="count-badge">{tickets.length} total</span>
        </div>

        {actionError && (
          <StatusPanel title={actionError.title} message={actionError.message} variant="error" />
        )}

        {loading && !tickets.length ? (
          <LoadingState label="Loading your dashboard…" />
        ) : ticketsError ? (
          <StatusPanel
            title={ticketsError.title}
            message={ticketsError.message}
            actionLabel="Retry tickets"
            onAction={() => loadDashboard()}
          />
        ) : tickets.length === 0 ? (
          <div className="empty-state surface">
            <span className="empty-state__icon" aria-hidden="true">↗</span>
            <h3>No tickets yet</h3>
            <p>Search the current timetable to create your first booking.</p>
            <Link className="button" to="/flights">Browse trains</Link>
          </div>
        ) : (
          <div className="ticket-list">
            {tickets.map((ticket) => (
              <TicketCard
                key={ticket.ticket_id}
                ticket={ticket}
                busyAction={busyByTicket[ticket.ticket_id]}
                onAddOption={addOption}
                onCancel={cancelTicket}
                cancelPending={cancelPending}
                setCancelPending={setCancelPending}
              />
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
