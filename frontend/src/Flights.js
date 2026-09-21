import { useCallback, useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api, { describeApiError } from './api';
import StatusPanel, { LoadingState } from './components/StatusPanel';

const emptyFilters = { origin: '', destination: '', departure_date: '', status: '', ordering: 'departure_time' };
const formatDateTime = (value) => value ? new Intl.DateTimeFormat(undefined, { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value)) : 'Time not provided';
const duration = (start, end) => {
  if (!start || !end) return 'Not provided';
  const minutes = Math.max(0, Math.round((new Date(end) - new Date(start)) / 60000));
  return `${Math.floor(minutes / 60)}h ${minutes % 60}m`;
};

export default function Flights() {
  const [trips, setTrips] = useState([]); const [filters, setFilters] = useState(emptyFilters);
  const [loading, setLoading] = useState(true); const [error, setError] = useState(null);
  const requestRef = useRef(null); const navigate = useNavigate();
  useEffect(() => { document.body.classList.add('bg-trips'); return () => document.body.classList.remove('bg-trips'); }, []);
  const loadTrips = useCallback(async (nextFilters) => {
    requestRef.current?.abort(); const controller = new AbortController(); requestRef.current = controller;
    setLoading(true); setError(null);
    const params = Object.fromEntries(Object.entries(nextFilters).filter(([, value]) => String(value).trim()));
    try { setTrips((await api.get('/train-trips/', { params, signal: controller.signal })).data); }
    catch (requestError) { if (requestError?.code !== 'ERR_CANCELED') setError(describeApiError(requestError, 'Trips could not be loaded.')); }
    finally { if (!controller.signal.aborted) setLoading(false); }
  }, []);
  useEffect(() => { loadTrips(emptyFilters); return () => requestRef.current?.abort(); }, [loadTrips]);
  const updateFilter = ({ target }) => setFilters((current) => ({ ...current, [target.name]: target.value }));
  const clearFilters = () => { setFilters(emptyFilters); loadTrips(emptyFilters); };
  const swapStations = () => setFilters((current) => ({ ...current, origin: current.destination, destination: current.origin }));
  return <div className="page-stack">
    <header className="page-heading surface surface--hero compact-hero"><p className="eyebrow">Plan a journey</p><h1>Find your train</h1><p className="lede">Search the local demo timetable. Times and fares are API-backed portfolio data, not a live rail feed.</p></header>
    <form className="search-panel surface" onSubmit={(event) => { event.preventDefault(); loadTrips(filters); }} aria-label="Search train trips">
      <div className="form-field"><label htmlFor="origin">From</label><input id="origin" name="origin" value={filters.origin} onChange={updateFilter} placeholder="London" /></div>
      <button className="swap-button" type="button" onClick={swapStations} aria-label="Swap origin and destination">⇄</button>
      <div className="form-field"><label htmlFor="destination">To</label><input id="destination" name="destination" value={filters.destination} onChange={updateFilter} placeholder="Paris" /></div>
      <div className="form-field"><label htmlFor="departure-date">Departure date</label><input id="departure-date" type="date" name="departure_date" value={filters.departure_date} onChange={updateFilter} /></div>
      <details className="secondary-filters"><summary>More filters</summary><div className="secondary-filters__grid"><div className="form-field"><label htmlFor="trip-status">Service status</label><select id="trip-status" name="status" value={filters.status} onChange={updateFilter}><option value="">Any status</option><option value="Scheduled">Scheduled</option><option value="Delayed">Delayed</option><option value="Cancelled">Cancelled</option></select></div><div className="form-field"><label htmlFor="ordering">Sort by</label><select id="ordering" name="ordering" value={filters.ordering} onChange={updateFilter}><option value="departure_time">Earliest departure</option><option value="-departure_time">Latest departure</option><option value="arrival_time">Earliest arrival</option><option value="service_number">Service number</option></select></div></div></details>
      <div className="search-panel__actions"><button className="button" type="submit" disabled={loading}>{loading ? 'Searching…' : 'Search'}</button><button className="button button--quiet" type="button" onClick={clearFilters} disabled={loading}>Clear</button></div>
    </form>
    <section aria-labelledby="results-heading"><div className="section-intro"><div><p className="eyebrow">Demo timetable</p><h2 id="results-heading">Train services</h2></div>{!loading && !error && <span className="count-badge">{trips.length} found</span>}</div>
      {loading ? <LoadingState label="Searching the timetable…" /> : error ? <StatusPanel title={error.title} message={error.message} actionLabel="Retry search" onAction={() => loadTrips(filters)} /> : trips.length === 0 ? <div className="empty-state surface" role="status"><span className="empty-state__icon" aria-hidden="true">⌕</span><h3>No trains match this search</h3><p>Try nearby station wording, another date, or remove the extra filters.</p><button className="button button--secondary" onClick={clearFilters}>Show all demo services</button></div> : <div className="trip-grid">{trips.map((trip) => <article className="trip-card surface" key={trip.trip_id}><div className="trip-card__header"><div><p className="eyebrow">Service {trip.service_number || '—'}</p><h3>{trip.origin_station || 'Origin unavailable'} <span aria-hidden="true">→</span> {trip.destination_station || 'Destination unavailable'}</h3></div><span className="status-chip status-chip--neutral">{trip.status || 'Status unavailable'}</span></div><dl className="trip-facts"><div><dt>Departs</dt><dd>{formatDateTime(trip.departure_time)}</dd></div><div><dt>Arrives</dt><dd>{formatDateTime(trip.arrival_time)}</dd></div><div><dt>Duration</dt><dd>{duration(trip.departure_time, trip.arrival_time)}</dd></div><div><dt>Train</dt><dd>{trip.consist_type || 'Not provided'}</dd></div></dl><div className="trip-card__footer"><p>From <strong>${Number(trip.base_fare).toFixed(2)}</strong> · Demo fare</p><button className="button" onClick={() => navigate('/book/' + trip.trip_id)}>View trip</button></div></article>)}</div>}
    </section>
  </div>;
}
