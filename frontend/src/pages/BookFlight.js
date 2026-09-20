import { useCallback, useEffect, useRef, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import api, { describeApiError } from '../api';
import StatusPanel, { LoadingState } from '../components/StatusPanel';

const initialOptions = { priority_boarding: false, meal: false, accommodation: false, taxi: false };
const currency = (value) => `$${Number(value || 0).toFixed(2)}`;

export default function BookFlight() {
  const { flightId } = useParams(); const navigate = useNavigate();
  const [trip, setTrip] = useState(null); const [options, setOptions] = useState(initialOptions);
  const [quote, setQuote] = useState(null); const [loading, setLoading] = useState(true);
  const [quoting, setQuoting] = useState(false); const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null); const bookingKey = useRef(window.crypto?.randomUUID?.() || `${Date.now()}-${Math.random()}`);
  useEffect(() => { document.body.classList.add('bg-booking'); return () => document.body.classList.remove('bg-booking'); }, []);
  const load = useCallback(async (signal) => {
    setLoading(true); setError(null);
    try { const [tripResponse, quoteResponse] = await Promise.all([api.get('/train-trips/' + flightId + '/', { signal }), api.get('/train-trips/' + flightId + '/quote/', { signal })]); setTrip(tripResponse.data); setQuote(quoteResponse.data); }
    catch (requestError) { if (requestError?.code !== 'ERR_CANCELED') setError(describeApiError(requestError, 'This trip could not be loaded.')); }
    finally { if (!signal?.aborted) setLoading(false); }
  }, [flightId]);
  useEffect(() => { const controller = new AbortController(); load(controller.signal); return () => controller.abort(); }, [load]);
  useEffect(() => {
    if (!trip) return undefined;
    const controller = new AbortController(); const timer = setTimeout(async () => {
      setQuoting(true);
      try { setQuote((await api.get('/train-trips/' + flightId + '/quote/', { params: options, signal: controller.signal })).data); }
      catch (requestError) { if (requestError?.code !== 'ERR_CANCELED') setError(describeApiError(requestError, 'The updated quote could not be loaded.')); }
      finally { if (!controller.signal.aborted) setQuoting(false); }
    }, 120);
    return () => { clearTimeout(timer); controller.abort(); };
  }, [flightId, options, trip]);
  const submit = async () => {
    if (submitting || quoting) return; setSubmitting(true); setError(null);
    try { const response = await api.post('/train-trips/' + flightId + '/book/', { ...options, booking_key: bookingKey.current }); navigate('/payment/' + response.data.ticket_id); }
    catch (requestError) { setError(describeApiError(requestError, 'Your booking could not be created.')); }
    finally { setSubmitting(false); }
  };
  if (loading) return <LoadingState label="Loading trip and fare…" />;
  if (!trip) return <StatusPanel title={error?.title || 'Trip unavailable'} message={error?.message || 'Return to search and choose another train.'} actionLabel="Retry" onAction={() => load()} />;
  const route = `${trip.origin_station || 'Origin unavailable'} → ${trip.destination_station || 'Destination unavailable'}`;
  return <div className="page-stack booking-page">
    <ol className="journey-steps" aria-label="Booking progress"><li className="journey-steps__current" aria-current="step"><span>1</span>Options</li><li><span>2</span>Demo payment</li><li><span>3</span>Seat</li></ol>
    <header className="page-heading surface surface--hero compact-hero"><p className="eyebrow">Service {trip.service_number || '—'}</p><h1>{route}</h1><p className="lede">Choose any extras. The server recalculates every price before creating the booking.</p></header>
    <div className="booking-layout"><section className="surface" aria-labelledby="options-heading"><div className="section-intro section-intro--compact"><div><p className="eyebrow">Customize your journey</p><h2 id="options-heading">Trip options</h2></div></div>
      <div className="option-grid">{quote?.available_options?.map((option) => <label className={'option-card' + (options[option.key] ? ' option-card--selected' : '')} key={option.key}><input type="checkbox" checked={options[option.key]} onChange={(event) => setOptions((current) => ({ ...current, [option.key]: event.target.checked }))} /><span className="option-card__control" aria-hidden="true">✓</span><span className="option-card__copy"><strong>{option.name}</strong><small>{option.description}</small><b>+{currency(option.price)}</b></span></label>)}</div>
    </section><aside className="surface booking-review" aria-labelledby="quote-heading"><p className="eyebrow">Estimated total</p><h2 id="quote-heading">Your fare</h2>{quoting ? <p role="status">Updating quote…</p> : <dl className="fare-breakdown"><div><dt>Base fare</dt><dd>{currency(quote?.base_fare)}</dd></div>{quote?.options?.map((item) => <div key={item.key}><dt>{item.name}</dt><dd>{currency(item.price)}</dd></div>)}<div><dt>Subtotal</dt><dd>{currency(quote?.subtotal)}</dd></div><div><dt>Taxes & fees</dt><dd>{currency(quote?.taxes_and_fees)}</dd></div><div className="fare-breakdown__total"><dt>Estimated total</dt><dd>{currency(quote?.total)}</dd></div></dl>}<p className="server-price-note">{quote?.tax_rule}</p>{error && <StatusPanel title={error.title} message={error.message} variant="error" />}<button className="button button--accent button--large button--full" type="button" onClick={submit} disabled={submitting || quoting}>{submitting ? 'Creating booking…' : 'Continue to demo payment'}</button><Link className="text-link" to="/flights">Back to search</Link></aside></div>
  </div>;
}
