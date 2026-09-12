import { useCallback, useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import api, { describeApiError } from './api';
import StatusPanel, { LoadingState } from './components/StatusPanel';

function formatDateTime(value) {
  if (!value) return 'Time not provided';
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(value));
}

const emptyFilters = {
  origin: '',
  destination: '',
  status: '',
  ordering: 'departure_time',
};

export default function Flights() {
  const [trips, setTrips] = useState([]);
  const [filters, setFilters] = useState(emptyFilters);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const requestRef = useRef(null);
  const navigate = useNavigate();

  useEffect(() => {
    document.body.classList.add('bg-trips');
    return () => document.body.classList.remove('bg-trips');
  }, []);

  const loadTrips = useCallback(async (nextFilters) => {
    requestRef.current?.abort();
    const controller = new AbortController();
    requestRef.current = controller;
    setLoading(true);
    setError(null);

    const params = Object.fromEntries(
      Object.entries(nextFilters).filter(([, value]) => String(value).trim() !== '')
    );

    try {
      const response = await api.get('/train-trips/', { params, signal: controller.signal });
      setTrips(response.data);
    } catch (requestError) {
      if (requestError?.code !== 'ERR_CANCELED') {
        setError(describeApiError(requestError, 'Trips could not be loaded.'));
      }
    } finally {
      if (!controller.signal.aborted) setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadTrips(emptyFilters);
    return () => requestRef.current?.abort();
  }, [loadTrips]);

  const updateFilter = (event) => {
    setFilters((current) => ({ ...current, [event.target.name]: event.target.value }));
  };

  const handleSearch = (event) => {
    event.preventDefault();
    loadTrips(filters);
  };

  const clearFilters = () => {
    setFilters(emptyFilters);
    loadTrips(emptyFilters);
  };

  return (
    <div className="page-stack">
      <header className="page-heading surface surface--hero">
        <p className="eyebrow">Trip discovery</p>
        <h1>Find an available train</h1>
        <p className="lede">
          Filter the API-backed timetable by station or status. Fares are confirmed by the server
          when a booking is created.
        </p>
      </header>

      <form className="search-panel surface" onSubmit={handleSearch} aria-label="Filter train trips">
        <div className="form-field">
          <label htmlFor="origin">Origin station</label>
          <input
            id="origin"
            name="origin"
            value={filters.origin}
            onChange={updateFilter}
            placeholder="e.g. London"
          />
        </div>
        <div className="form-field">
          <label htmlFor="destination">Destination station</label>
          <input
            id="destination"
            name="destination"
            value={filters.destination}
            onChange={updateFilter}
            placeholder="e.g. Paris"
          />
        </div>
        <div className="form-field">
          <label htmlFor="trip-status">Service status</label>
          <input
            id="trip-status"
            name="status"
            value={filters.status}
            onChange={updateFilter}
            placeholder="e.g. Scheduled"
          />
        </div>
        <div className="form-field">
          <label htmlFor="ordering">Order by</label>
          <select id="ordering" name="ordering" value={filters.ordering} onChange={updateFilter}>
            <option value="departure_time">Earliest departure</option>
            <option value="-departure_time">Latest departure</option>
            <option value="arrival_time">Earliest arrival</option>
            <option value="service_number">Service number</option>
          </select>
        </div>
        <div className="search-panel__actions">
          <button className="button" type="submit" disabled={loading}>
            {loading ? 'Searching…' : 'Search trains'}
          </button>
          <button className="button button--quiet" type="button" onClick={clearFilters} disabled={loading}>
            Clear
          </button>
        </div>
      </form>

      <section aria-labelledby="results-heading">
        <div className="section-intro">
          <div>
            <p className="eyebrow">Live API result</p>
            <h2 id="results-heading">Available services</h2>
          </div>
          {!loading && !error && <span className="count-badge">{trips.length} found</span>}
        </div>

        {loading ? (
          <LoadingState label="Checking the current timetable…" />
        ) : error ? (
          <StatusPanel
            title={error.title}
            message={error.message}
            actionLabel="Retry search"
            onAction={() => loadTrips(filters)}
          />
        ) : trips.length === 0 ? (
          <div className="empty-state surface" role="status">
            <span className="empty-state__icon" aria-hidden="true">⌕</span>
            <h3>No matching trains</h3>
            <p>Try broader station names, remove the status filter, or clear all filters.</p>
            <button className="button button--secondary" onClick={clearFilters}>Clear filters</button>
          </div>
        ) : (
          <div className="trip-grid">
            {trips.map((trip) => {
              const id = trip.trip_id ?? trip.flight_id;
              const number = trip.service_number ?? trip.flight_number;
              return (
                <article className="trip-card surface" key={id}>
                  <div className="trip-card__header">
                    <div>
                      <p className="eyebrow">Service {number || '—'}</p>
                      <h3>{trip.origin_station || 'Origin unavailable'}</h3>
                      <span className="trip-card__arrow" aria-hidden="true">→</span>
                      <h3>{trip.destination_station || 'Destination unavailable'}</h3>
                    </div>
                    <span className="status-chip status-chip--neutral">
                      <span aria-hidden="true">•</span>
                      {trip.status || 'Status unavailable'}
                    </span>
                  </div>
                  <dl className="trip-facts">
                    <div>
                      <dt>Departs</dt>
                      <dd>{formatDateTime(trip.departure_time)}</dd>
                    </div>
                    <div>
                      <dt>Arrives</dt>
                      <dd>{formatDateTime(trip.arrival_time)}</dd>
                    </div>
                    <div>
                      <dt>Train</dt>
                      <dd>{trip.consist_type || 'Not provided'}</dd>
                    </div>
                    <div>
                      <dt>Platform</dt>
                      <dd>{trip.platform || 'TBA'}</dd>
                    </div>
                  </dl>
                  <div className="trip-card__footer">
                    <p>Final amount calculated by the booking service.</p>
                    <button className="button" onClick={() => navigate('/book/' + id)}>
                      Review trip
                    </button>
                  </div>
                </article>
              );
            })}
          </div>
        )}
      </section>
    </div>
  );
}
