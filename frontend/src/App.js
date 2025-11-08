import React from 'react';
import { Routes, Route, Navigate, Link, useNavigate } from 'react-router-dom';

import Login from './pages/Login';
import Register from './pages/Register';
import Home from './Home';
import Flights from './Flights';
import BookFlight from './pages/BookFlight';
import PaymentPage from './pages/PaymentPage';
import SeatSelect from './pages/SeatSelect';
import ChatWidget from './components/ChatWidget';
import NotificationWidget from "./components/NotificationWidget";
import { Tooltip } from 'react-tooltip';
import 'react-tooltip/dist/react-tooltip.css';
import './App.css';

export default function App() {
  const token = !!localStorage.getItem('token');
  const navigate = useNavigate();

  const handleLogout = () => {
    localStorage.removeItem('token');
    navigate('/');          
  };

  return (
    <>
      <nav className="navbar">
        <div className="navbar-brand">Trainline</div>

        <div className="navbar-links">
          {token ? (
            <>
              <Link
                to="/"
                className="nav-link"
                data-tip="Go to dashboard"
                data-tooltip-id="main-tip"
              >
                Home
              </Link>

              <Link
                to="/flights"
                className="nav-link"
                data-tip="Browse and book"
                data-tooltip-id="main-tip"
              >
                Available Trains
              </Link>

              <button
                className="nav-link"
                data-tip="Log out"
                data-tooltip-id="main-tip"
                onClick={handleLogout}
              >
                Log Out
              </button>
            </>
          ) : (
            <>
              <Link
                to="/register"
                className="nav-link"
                data-tip="Create an account"
                data-tooltip-id="main-tip"
              >
                Register
              </Link>

              <Link
                to="/login"
                className="nav-link"
                data-tip="Sign in"
                data-tooltip-id="main-tip"
              >
                Log In
              </Link>
            </>
          )}
        </div>
      </nav>

      <div className="container">
        <Routes>
          <Route path="/" element={token ? <Home /> : <Navigate to="/login" replace />} />
          <Route path="/login" element={token ? <Navigate to="/" replace /> : <Login />} />
          <Route path="/register" element={token ? <Navigate to="/" replace /> : <Register />} />

          <Route path="/trips"   element={token ? <Flights /> : <Navigate to="/login" replace />} />
          <Route path="/flights" element={token ? <Flights /> : <Navigate to="/login" replace />} />

          <Route path="/book/:flightId" element={token ? <BookFlight /> : <Navigate to="/login" replace />} />
          <Route path="/select-seat/:ticketId" element={token ? <SeatSelect /> : <Navigate to="/login" replace />} />
          <Route path="/payment/:ticketId" element={token ? <PaymentPage /> : <Navigate to="/login" replace />} />

          <Route path="*" element={<Navigate to={token ? '/' : '/login'} replace />} />
        </Routes>
      </div>

      {token && <ChatWidget />}
      {token && <NotificationWidget />}

      <Tooltip id="main-tip" place="top" effect="solid" style={{ backgroundColor: "#333", color: "#fff" }} /> 
    </>
  );
}
