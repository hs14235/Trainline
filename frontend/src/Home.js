import React, { useState, useEffect } from "react";
import { useNavigate, Link } from "react-router-dom";
import api from "./api";

export default function Home() {
  const [user, setUser] = useState(null);
  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  
  useEffect(() => {
  document.body.classList.add('bg-home');
  return () => document.body.classList.remove('bg-home');
  }, []);

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) return navigate("/login");

    Promise.all([
      api.get("/dj-rest-auth/user/"),
      api.get("/api/tickets/"),
    ])
      .then(([uRes, tRes]) => {
        setUser(uRes.data);
        setTickets(tRes.data);
      })
      .catch(err => {
        console.error(err);
        setError("Failed to load dashboard");
      })
      .finally(() => setLoading(false));
  }, [navigate]);

  if (loading) return <p>Loading…</p>;
  if (error)   return <p style={{ color: "crimson" }}>{error}</p>;

  const points = user.membership_points || 0;
  // Use the backend-provided membership_level instead of calculating client-side
  const level = user.membership_level || "Bronze";
  

  const addFlag = async (ticketId, field) => {
    try {
      const res = await api.patch(`/api/tickets/${ticketId}/`, { [field]: true });

      // If backend returns the updated ticket + membership info, use it
      if (res.data) {
        if (res.data.membership_points !== undefined) {
          setUser(u => ({ ...u, membership_points: res.data.membership_points, membership_level: res.data.membership_level }));
        }
        if (res.data.ticket) {
          setTickets(prev => prev.map(t => (t.ticket_id === res.data.ticket.ticket_id ? res.data.ticket : t)));
          return;
        }
      }

      // fallback: refresh whole state
      const [uRes, tRes] = await Promise.allSettled([api.get('/dj-rest-auth/user/'), api.get('/api/tickets/')]);
      if (uRes.status === 'fulfilled') setUser(uRes.value.data);
      if (tRes.status === 'fulfilled') setTickets(tRes.value.data);
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div style={{ margin: "1rem 0"}}>
      <h1>Welcome back, {user.first_name || user.email.split("@")[0]}</h1>
      <p>Membership: <strong>{level}</strong> | Points: <strong>{points}</strong></p>
      <nav style={{ margin: "1rem 0" }}>
        <Link to="/trips">
        <button 
          className ="book-button"
          aria-label="Book a Trip"
          data-tooltip-id="main-tip" 
          data-tooltip-content="Book a Trip!"
        
        >
          <span className="sr-only">Book a Trip</span>
        </button>
     </Link>
     </nav>

      <h2>Your Tickets</h2>
      {tickets.length === 0 ? (
        <p>No tickets yet.</p>
      ) : (
        <table border="1" cellPadding="6">
          <thead>
            <tr>
              <th>#</th><th>Trip</th><th>Seat</th><th>Paid?</th><th>Method</th>
              <th>Priority</th><th>Meal</th><th>Accom</th><th>Taxi</th><th>Booked At</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
             {tickets.map(t => {
              const trip = t.train_trip || {};
              const serviceNo = trip.service_number;

              return (
                <tr key={t.ticket_id}>
                  <td>{t.ticket_id}</td>
                  <td>{serviceNo ?? '—'}</td>
                  <td>
                  {t.seat_num
                    ? t.seat_num
                    : <Link to={`/select-seat/${t.ticket_id}`}>Pick Seat</Link>
                  }
                </td>
                <td>
                  {t.paid
                      ? "✘"
                    : <button onClick={() => navigate(`/payment/${t.ticket_id}`)}
                     data-tooltip-id="main-tip"
                     data-tooltip-content="Pay">
                      </button>
                  }
                </td>
                <td>{t.payment_method || "—"}</td>
                  <td>{t.priority_boarding ? "✘" : "☐"}</td>
                  <td>{t.meal ? "✘" : "☐"}</td>
                  <td>{t.accommodation ? "✘" : "☐"}</td>
                  <td>{t.taxi ? "✘" : "☐"}</td>
                <td>{new Date(t.booked_at).toLocaleDateString()}</td>
                <td>
                  {!t.priority_boarding &&
                    <button onClick={() =>
                      addFlag(t.ticket_id, "priority_boarding")
                    } >Add Priority</button>
                  }
                  {!t.meal &&
                    <button onClick={() =>
                      addFlag(t.ticket_id, "meal")
                    }>Add Meal</button>
                  }
                  {!t.accommodation &&
                    <button onClick={() =>
                      addFlag(t.ticket_id, "accommodation")
                    }>Add Accom</button>
                  }
                  {!t.taxi &&
                    <button onClick={() =>
                      addFlag(t.ticket_id, "taxi")
                    }>Add Taxi</button>
                  }
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      )}
    </div>
  );
}
  
