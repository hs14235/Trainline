import React, { useState, useEffect } from 'react';
import api from './api';
import { useNavigate } from 'react-router-dom';

export default function Trips() {
  const [trips, setTrips] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    const body = document.body;
    body.classList.add('bg-trips');
    return () => body.classList.remove('bg-trips');
  }, []);

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      setLoading(true);
      try {
        const r = await api.get('trips/');
        if (!cancelled) setTrips(r.data);
      } catch (err) {
        if (!cancelled) setError(err);
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    load();
    return () => { cancelled = true; };
  }, []);

  if (loading) return <p>Loading trips…</p>;
  if (error) return <p style={{ color: 'red' }}>Error loading trips</p>;

  return (
    <div>
      <h2>Available Trips</h2>
      <table className="flights-table">
        <thead>
          <tr>
            <th>Service #</th>
            <th>From (Station)</th>
            <th>To (Station)</th>
            <th>Departs</th>
            <th>Arrives</th>
            <th>Platform</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          {trips.map((t) => {
            const id = t.trip_id;
            const number = t.service_number;
            const from = t.origin_station;
            const to = t.destination_station;
            const dep = t.departure_time;
            const arr = t.arrival_time;
            const platform = t.platform || '—';

            return (
              <tr key={id}>
                <td>{number}</td>
                <td>{from}</td>
                <td>{to}</td>
                <td>{dep ? new Date(dep).toLocaleString() : '—'}</td>
                <td>{arr ? new Date(arr).toLocaleString() : '—'}</td>
                <td>{platform}</td>
                <td>
                  <button onClick={() => navigate(`/book/${id}`)}>
                    Book
                  </button>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}