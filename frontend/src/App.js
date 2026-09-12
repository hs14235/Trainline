import { useEffect, useRef, useState } from 'react';
import { Link, NavLink, Navigate, Route, Routes, useLocation, useNavigate } from 'react-router-dom';

import './App.css';
import ChatWidget from './components/ChatWidget';
import NotificationWidget from './components/NotificationWidget';
import ServiceStatus from './components/ServiceStatus';
import Flights from './Flights';
import Home from './Home';
import BookFlight from './pages/BookFlight';
import Engineering from './pages/Engineering';
import Login from './pages/Login';
import PaymentPage from './pages/PaymentPage';
import Register from './pages/Register';
import SeatSelect from './pages/SeatSelect';

function ProtectedRoute({ authenticated, children }) {
  return authenticated ? children : <Navigate to="/login" replace />;
}

function RouteFrame({ children }) {
  const location = useLocation();
  const mainRef = useRef(null);

  useEffect(() => {
    window.scrollTo(0, 0);
    mainRef.current?.focus({ preventScroll: true });
  }, [location.pathname]);

  return (
    <main id="main-content" className="app-main" ref={mainRef} tabIndex="-1">
      {children}
    </main>
  );
}

export default function App() {
  const [authenticated, setAuthenticated] = useState(() => Boolean(localStorage.getItem('token')));
  const navigate = useNavigate();

  const navClassName = ({ isActive }) => 'nav-link' + (isActive ? ' nav-link--active' : '');

  const handleAuthenticated = (token) => {
    localStorage.setItem('token', token);
    setAuthenticated(true);
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    setAuthenticated(false);
    navigate('/login');
  };

  const protect = (element) => (
    <ProtectedRoute authenticated={authenticated}>{element}</ProtectedRoute>
  );

  return (
    <div className="app-shell">
      <a className="skip-link" href="#main-content">
        Skip to main content
      </a>
      <header className="site-header">
        <Link className="brand" to={authenticated ? '/' : '/login'} aria-label="Trainline home">
          <span className="brand__rail" aria-hidden="true" />
          <span>Trainline</span>
        </Link>

        <nav className="primary-nav" aria-label="Primary navigation">
          {authenticated ? (
            <>
              <NavLink to="/" end className={navClassName}>
                Dashboard
              </NavLink>
              <NavLink to="/flights" className={navClassName}>
                Find trains
              </NavLink>
              <NavLink to="/engineering" className={navClassName}>
                Engineering
              </NavLink>
              <button className="nav-link nav-link--button" onClick={handleLogout}>
                Log out
              </button>
            </>
          ) : (
            <>
              <NavLink to="/engineering" className={navClassName}>
                Engineering
              </NavLink>
              <NavLink to="/register" className={navClassName}>
                Create account
              </NavLink>
              <NavLink to="/login" className={navClassName}>
                Log in
              </NavLink>
            </>
          )}
        </nav>
      </header>

      <RouteFrame>
        <Routes>
          <Route path="/engineering" element={<Engineering />} />
          <Route path="/" element={protect(<Home />)} />
          <Route
            path="/login"
            element={
              authenticated ? (
                <Navigate to="/" replace />
              ) : (
                <Login onAuthenticated={handleAuthenticated} />
              )
            }
          />
          <Route
            path="/register"
            element={authenticated ? <Navigate to="/" replace /> : <Register />}
          />
          <Route path="/trips" element={protect(<Flights />)} />
          <Route path="/flights" element={protect(<Flights />)} />
          <Route path="/book/:flightId" element={protect(<BookFlight />)} />
          <Route path="/select-seat/:ticketId" element={protect(<SeatSelect />)} />
          <Route path="/payment/:ticketId" element={protect(<PaymentPage />)} />
          <Route path="*" element={<Navigate to={authenticated ? '/' : '/login'} replace />} />
        </Routes>
      </RouteFrame>

      <footer className="site-footer">
        <div>
          <strong>Trainline engineering demo</strong>
          <span>React · Django REST · PostgreSQL</span>
        </div>
        <ServiceStatus />
      </footer>

      {authenticated && <NotificationWidget />}
      {authenticated && <ChatWidget />}
    </div>
  );
}
