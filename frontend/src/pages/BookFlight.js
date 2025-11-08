import React, { useState, useEffect } from "react";
import { useParams, useNavigate }       from "react-router-dom";
import api                              from "../api";

export default function BookFlight() {
  const { flightId } = useParams();
  const navigate    = useNavigate();

  const [loading, setLoading]           = useState(true);
  const [error,   setError]             = useState(null);
  const [baseFare, setBaseFare]         = useState(0);

  const [priorityBoarding, setPb]       = useState(false);
  const [meal, setMeal]                 = useState(false);
  const [accommodation, setAccommodation] = useState(false);
  const [taxi, setTaxi]                 = useState(false);

  const PB_FEE      = 20;
  const MEAL_FEE    = 10;
  const ACCOM_FEE   = 50;
  const TAXI_FEE    = 30;

  useEffect(() => {
    const body = document.body;
    body.classList.add('bg-booking');
    return () => body.classList.remove('bg-booking');
  }, []);

  useEffect(() => {
    api.get(`flights/${flightId}/`)
      .then(res => {
        setBaseFare(res.data.fare ?? 100);
      })
      .catch(() => setError("Couldn’t load flight info"))
      .finally(() => setLoading(false));
  }, [flightId]);

  const totalFare =
    baseFare +
    (priorityBoarding ? PB_FEE : 0) +
    (meal             ? MEAL_FEE : 0) +
    (accommodation    ? ACCOM_FEE : 0) +
    (taxi             ? TAXI_FEE : 0);

  const handleBook = async () => {
    try {
      const payload = {
        priority_boarding: priorityBoarding,
        meal:              meal,
        accommodation:     accommodation,
        taxi:              taxi,
      };
      const res = await api.post(
        `flights/${flightId}/book/`,
        payload
      );
      navigate(`/payment/${res.data.ticket_id}`);
    } catch (err) {
      console.error(err);
      setError("Booking failed—please try again.");
    }
  };

  if (loading)  return <p>Loading Trainline info…</p>;
  if (error)    return <p style={{ color: "crimson" }}>{error}</p>;
  

  return (
    <div style={{ padding: "1rem" }}>
      <h2>Book a train line #{flightId}</h2>
      <p>Base fare: <strong>${baseFare.toFixed(2)}</strong></p>

      <label style={{ display: "block", margin: "0.5rem 0" }}>
        <input
          type="checkbox"
          checked={priorityBoarding}
          onChange={() => setPb(!priorityBoarding)}
        />{" "}
        Sleeping coaches (+${PB_FEE})
      </label>

      <label style={{ display: "block", margin: "0.5rem 0" }}>
        <input
          type="checkbox"
          checked={meal}
          onChange={() => setMeal(!meal)}
        />{" "}
        Onboard meal (+${MEAL_FEE})
      </label>

      <label style={{ display: "block", margin: "0.5rem 0" }}>
        <input
          type="checkbox"
          checked={accommodation}
          onChange={() => setAccommodation(!accommodation)}
        />{" "}
        Accessible coaches (+${ACCOM_FEE})
      </label>

      <label style={{ display: "block", margin: "0.5rem 0" }}>
        <input
          type="checkbox"
          checked={taxi}
          onChange={() => setTaxi(!taxi)}
        />{" "}
        Taxi on arrival (+${TAXI_FEE})
      </label>

      <h3>Total: ${totalFare.toFixed(2)}</h3>

      <button onClick={handleBook}>
        Confirm &amp; Proceed to Payment
      </button>
    </div>
  );
}
