import { useCallback, useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';

import api, { describeApiError } from '../api';
import StatusPanel, { LoadingState } from '../components/StatusPanel';

const optionDefinitions = [
  {
    key: 'priority_boarding',
    title: 'Sleeping coach',
    description: 'Request the sleeping-coach option for this booking.',
  },
  {
    key: 'meal',
    title: 'Onboard meal',
    description: 'Add the onboard meal option to the ticket.',
  },
  {
    key: 'accommodation',
    title: 'Accessible coach',
    description: 'Request the supported accessible-coach accommodation.',
  },
  {
    key: 'taxi',
    title: 'Taxi on arrival',
    description: 'Add the arrival taxi option recorded by this demo.',
  },
];

export default function BookFlight() {
  const { flightId } = useParams();
  const navigate = useNavigate();
  const [trip, setTrip] = useState(null);
  const [options, setOptions] = useState({
    priority_boarding: false,
    meal: false,
    accommodation: false,
    taxi: false,
  });
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    document.body.classList.add('bg-booking');
    return () => document.body.classList.remove('bg-booking');
  }, []);

  const loadTrip = useCallback(async (signal) => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.get('/train-trips/' + flightId + '/', { signal });
      setTrip(response.data);
    } catch (requestError) {
      if (requestError?.code !== 'ERR_CANCELED') {
        setError(describeApiError(requestError, 'Trip details could not be loaded.'));
      }
    } finally {
      if (!signal?.aborted) setLoading(false);
    }
  }, [flightId]);

  useEffect(() => {
    const controller = new AbortController();
    loadTrip(controller.signal);
    return () => controller.abort();
  }, [loadTrip]);

  const toggleOption = (key) => {
    setOptions((current) => ({ ...current, [key]: !current[key] }));
  };

  const handleBook = async (event) => {
    event.preventDefault();
    if (submitting) return;

    setSubmitting(true);
    setError(null);
    try {
      const response = await api.post('/train-trips/' + flightId + '/book/', options);
      navigate('/payment/' + response.data.ticket_id, {
        state: { amount: response.data.amount, bookingCreated: true },
      });
    } catch (requestError) {
      setError(describeApiError(requestError, 'The booking could not be created.'));
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) return <LoadingState label="Loading trip details…" />;
  if (!trip && error) {
    return (
      <StatusPanel
        title={error.title}
        message={error.message}
        actionLabel="Retry trip"
        onAction={() => loadTrip()}
      />
    );
  }

  return (
    <div className="page-stack booking-page">
      <ol className="journey-steps" aria-label="Booking progress">
        <li className="journey-steps__current" aria-current="step"><span>1</span>Options</li>
        <li><span>2</span>Demo payment</li>
        <li><span>3</span>Seat</li>
      </ol>

      <header className="page-heading surface surface--hero">
        <p className="eyebrow">Service {trip.service_number || '—'}</p>
        <h1>{trip.origin_station} <span aria-hidden="true">→</span> {trip.destination_station}</h1>
        <p className="lede">
          Choose supported options, then let the API create the ticket and calculate its
          authoritative amount.
        </p>
      </header>

      <form className="booking-layout" onSubmit={handleBook}>
        <section className="surface" aria-labelledby="options-heading">
          <div className="section-intro section-intro--compact">
            <div>
              <p className="eyebrow">Step 1</p>
              <h2 id="options-heading">Trip options</h2>
            </div>
          </div>
          <div className="option-grid">
            {optionDefinitions.map((option) => (
              <label
                className={'option-card' + (options[option.key] ? ' option-card--selected' : '')}
                key={option.key}
              >
                <input
                  type="checkbox"
                  checked={options[option.key]}
                  onChange={() => toggleOption(option.key)}
                  disabled={submitting}
                />
                <span className="option-card__control" aria-hidden="true">✓</span>
                <span>
                  <strong>{option.title}</strong>
                  <small>{option.description}</small>
                </span>
              </label>
            ))}
          </div>
        </section>

        <aside className="surface booking-review" aria-labelledby="review-heading">
          <p className="eyebrow">Review</p>
          <h2 id="review-heading">Create this booking</h2>
          <dl>
            <div><dt>Service</dt><dd>{trip.service_number || '—'}</dd></div>
            <div><dt>Status</dt><dd>{trip.status || 'Not provided'}</dd></div>
            <div><dt>Platform</dt><dd>{trip.platform || 'TBA'}</dd></div>
            <div>
              <dt>Options</dt>
              <dd>{Object.values(options).filter(Boolean).length || 'None'}</dd>
            </div>
          </dl>
          <div className="server-price-note">
            <strong>Server-calculated total</strong>
            <p>The final amount is returned after ticket creation. This page does not calculate it.</p>
          </div>
          {error && <StatusPanel title={error.title} message={error.message} variant="error" />}
          <button className="button button--accent button--large button--full" type="submit" disabled={submitting}>
            {submitting ? 'Creating booking…' : 'Create booking'}
          </button>
          <Link className="text-link" to="/flights">Back to train results</Link>
        </aside>
      </form>
    </div>
  );
}
