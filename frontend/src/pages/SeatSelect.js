import { useCallback, useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';

import api, { describeApiError } from '../api';
import StatusPanel, { LoadingState } from '../components/StatusPanel';

function sortSeats(seats) {
  return [...seats].sort((left, right) =>
    left.localeCompare(right, undefined, { numeric: true, sensitivity: 'base' })
  );
}

export default function SeatSelect() {
  const { ticketId } = useParams();
  const [ticket, setTicket] = useState(null);
  const [tripId, setTripId] = useState(null);
  const [seats, setSeats] = useState([]);
  const [selectedSeat, setSelectedSeat] = useState(null);
  const [unavailableSeats, setUnavailableSeats] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const [confirmedSeat, setConfirmedSeat] = useState(null);

  useEffect(() => {
    document.body.classList.add('bg-seatselect');
    return () => document.body.classList.remove('bg-seatselect');
  }, []);

  const refreshAvailability = useCallback(async (currentTripId, keepMessage = false) => {
    if (!currentTripId) return;
    setRefreshing(true);
    if (!keepMessage) setError(null);
    try {
      const response = await api.get('/seats/' + currentTripId + '/');
      setSeats(sortSeats(response.data));
    } catch (requestError) {
      setError(describeApiError(requestError, 'Seat availability could not be refreshed.'));
    } finally {
      setRefreshing(false);
    }
  }, []);

  const loadSeatContext = useCallback(async (signal) => {
    setLoading(true);
    setError(null);
    try {
      const ticketResponse = await api.get('/tickets/' + ticketId + '/', { signal });
      const loadedTicket = ticketResponse.data;
      const currentTripId = loadedTicket.train_trip?.trip_id;
      if (!currentTripId) {
        setError({
          title: 'Trip details are missing',
          message: 'This ticket is not associated with a train service.',
        });
        return;
      }

      setTicket(loadedTicket);
      setTripId(currentTripId);
      if (loadedTicket.seat_num) {
        setConfirmedSeat(loadedTicket.seat_num);
        return;
      }

      const seatsResponse = await api.get('/seats/' + currentTripId + '/', { signal });
      setSeats(sortSeats(seatsResponse.data));
    } catch (requestError) {
      if (requestError?.code !== 'ERR_CANCELED') {
        setError(describeApiError(requestError, 'Seat selection could not be loaded.'));
      }
    } finally {
      if (!signal?.aborted) setLoading(false);
    }
  }, [ticketId]);

  useEffect(() => {
    const controller = new AbortController();
    loadSeatContext(controller.signal);
    return () => controller.abort();
  }, [loadSeatContext]);

  const confirmSelection = async () => {
    if (!selectedSeat || submitting) return;
    setSubmitting(true);
    setError(null);

    try {
      await api.post('/seats/' + tripId + '/', {
        ticket_id: ticketId,
        seat_num: selectedSeat,
      });
      setConfirmedSeat(selectedSeat);
    } catch (requestError) {
      if (requestError.response?.status === 409) {
        const conflictedSeat = selectedSeat;
        setUnavailableSeats((current) =>
          current.includes(conflictedSeat) ? current : [...current, conflictedSeat]
        );
        setSeats((current) => current.filter((seat) => seat !== conflictedSeat));
        setSelectedSeat(null);
        setError({
          kind: 'conflict',
          title: 'That seat was just taken',
          message:
            'Another booking reserved ' +
            conflictedSeat +
            '. Availability has been refreshed; choose another seat.',
        });
        await refreshAvailability(tripId, true);
      } else {
        setError(describeApiError(requestError, 'The seat could not be reserved.'));
      }
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) return <LoadingState label="Loading guarded seat availability…" />;
  if (!ticket && error) {
    return (
      <StatusPanel
        title={error.title}
        message={error.message}
        actionLabel="Retry seat selection"
        onAction={() => loadSeatContext()}
      />
    );
  }

  if (confirmedSeat) {
    return (
      <div className="page-stack seat-page">
        <ol className="journey-steps" aria-label="Booking progress">
          <li className="journey-steps__complete"><span>✓</span>Options</li>
          <li className="journey-steps__complete"><span>✓</span>Demo payment</li>
          <li className="journey-steps__current" aria-current="step"><span>3</span>Seat</li>
        </ol>
        <section className="surface completion-card">
          <span className="completion-card__mark" aria-hidden="true">✓</span>
          <p className="eyebrow">Seat confirmed</p>
          <h1>{confirmedSeat}</h1>
          <p>
            This seat is assigned to ticket #{ticketId} through the guarded backend workflow.
          </p>
          <Link className="button button--accent" to="/">Return to dashboard</Link>
        </section>
      </div>
    );
  }

  return (
    <div className="page-stack seat-page">
      <ol className="journey-steps" aria-label="Booking progress">
        <li className="journey-steps__complete"><span>✓</span>Options</li>
        <li className="journey-steps__complete"><span>✓</span>Demo payment</li>
        <li className="journey-steps__current" aria-current="step"><span>3</span>Seat</li>
      </ol>

      <header className="page-heading surface surface--hero">
        <p className="eyebrow">Ticket #{ticketId}</p>
        <h1>Select an available seat</h1>
        <p className="lede">
          Availability comes from the API. Your final choice is assigned transactionally and may
          conflict if another booking wins the seat first.
        </p>
      </header>

      <div className="seat-layout">
        <section className="surface seat-map" aria-labelledby="seat-map-heading">
          <div className="section-intro section-intro--compact">
            <div>
              <p className="eyebrow">Live inventory</p>
              <h2 id="seat-map-heading">Coach 1</h2>
            </div>
            <button
              className="button button--quiet button--small"
              onClick={() => refreshAvailability(tripId)}
              disabled={refreshing || submitting}
            >
              {refreshing ? 'Refreshing…' : 'Refresh seats'}
            </button>
          </div>

          <ul className="seat-legend" aria-label="Seat map legend">
            <li><span className="seat-sample">1A</span>Available</li>
            <li><span className="seat-sample seat-sample--selected">1A ✓</span>Selected</li>
            <li><span className="seat-sample seat-sample--unavailable">1A ×</span>Unavailable</li>
            <li><span className="seat-sample seat-sample--focus">1A</span>Keyboard focus</li>
          </ul>

          {error && <StatusPanel title={error.title} message={error.message} variant="warning" />}

          {seats.length === 0 && unavailableSeats.length === 0 ? (
            <div className="empty-state">
              <h3>No seats are currently available</h3>
              <p>Return to your dashboard or refresh once before trying again.</p>
            </div>
          ) : (
            <div className="seat-grid" role="group" aria-label="Available seats">
              {sortSeats([...seats, ...unavailableSeats]).map((seatNumber) => {
                const unavailable = unavailableSeats.includes(seatNumber);
                const selected = selectedSeat === seatNumber;
                return (
                  <button
                    key={seatNumber}
                    className={
                      'seat-button' +
                      (selected ? ' seat-button--selected' : '') +
                      (unavailable ? ' seat-button--unavailable' : '')
                    }
                    onClick={() => !unavailable && setSelectedSeat(seatNumber)}
                    disabled={unavailable || submitting}
                    aria-pressed={selected}
                    aria-label={
                      unavailable
                        ? 'Seat ' + seatNumber + ', unavailable'
                        : 'Seat ' + seatNumber + (selected ? ', selected' : ', available')
                    }
                  >
                    <span>{seatNumber}</span>
                    <small>{unavailable ? 'Taken' : selected ? 'Selected ✓' : 'Available'}</small>
                  </button>
                );
              })}
            </div>
          )}
        </section>

        <aside className="surface seat-review" aria-labelledby="seat-review-heading">
          <p className="eyebrow">Selection</p>
          <h2 id="seat-review-heading">{selectedSeat ? 'Seat ' + selectedSeat : 'Choose a seat'}</h2>
          <p>
            {selectedSeat
              ? 'Confirm once. The app will never retry this reservation mutation automatically.'
              : 'Select one available seat from the keyboard-operable grid.'}
          </p>
          <button
            className="button button--accent button--large button--full"
            onClick={confirmSelection}
            disabled={!selectedSeat || submitting}
          >
            {submitting ? 'Reserving seat…' : 'Confirm seat'}
          </button>
          <Link className="text-link" to="/">Return to dashboard</Link>
        </aside>
      </div>
    </div>
  );
}
