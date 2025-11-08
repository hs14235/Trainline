import React, { useState, useEffect } from 'react';
import api from './api';

export default function Tickets() {
  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError]     = useState(null);

  useEffect(() => {
    api.get(`ticket/${ticketId}/`)
      .then(res => setTickets(res.data))
      .catch(err => setError(err))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p>Loading your tickets…</p>;
  if (error)   return <p style={{color:'red'}}>Error: {error.message}</p>;

  return (
    <div className="tickets">
      <h2>My Tickets</h2>
      {tickets.length === 0
        ? <p>You have no tickets yet.</p>
        : (
          <table>
            <thead>
              <tr>
                <th>ID</th><th>Flight#</th><th>Seat</th>
                <th>Booked At</th>
              </tr>
            </thead>
            <tbody>
              {tickets.map(t => (
                <tr key={t.ticket_id}>
                  <td>{t.ticket_id}</td>
                  <td>{t.flight.flight_number}</td>
                  <td>{t.seat_num || '—'}</td>
                  <td>{new Date(t.ticket_date).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )
      }
    </div>
  );
}
