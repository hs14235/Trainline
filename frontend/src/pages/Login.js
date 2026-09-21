import { useEffect, useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';

import api, { describeApiError } from '../api';
import StatusPanel from '../components/StatusPanel';

export default function Login({ onAuthenticated }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();

  useEffect(() => {
    document.body.classList.add('bg-login');
    return () => document.body.classList.remove('bg-login');
  }, []);

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (submitting) return;

    if (!username.trim() || !password) {
      setError({
        title: 'Complete both fields',
        message: 'Enter your username and password before signing in.',
      });
      return;
    }

    setSubmitting(true);
    setError(null);
    try {
      const response = await api.post('/dj-rest-auth/login/', {
        username: username.trim(),
        password,
      });
      const token = response.data.key || response.data.token;
      if (!token) throw new Error('Authentication succeeded without a usable token.');
      onAuthenticated(token);
      navigate('/');
    } catch (requestError) {
      setError(describeApiError(requestError, 'The username or password was not accepted.'));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="auth-layout">
      <section className="auth-intro" aria-labelledby="login-heading">
        <p className="eyebrow">Continue your journey</p>
        <h1 id="login-heading">Sign in to Trainline</h1>
        <p>
          Review your journeys, choose from server-backed seat availability, and continue the
          clearly labeled demo payment workflow.
        </p>
        <ul className="auth-trust-list">
          <li>Bookings are authorized per account</li>
          <li>Fares are calculated by the API</li>
          <li>Seat conflicts are resolved by the database workflow</li>
        </ul>
      </section>

      <form className="auth-card surface" noValidate onSubmit={handleSubmit}>
        <div>
          <p className="eyebrow">Account access</p>
          <h2>Log in</h2>
          <p className="form-help">Use the local demo account only after running the documented seed command.</p>
        </div>

        {location.state?.message && (
          <StatusPanel title="Account created" message={location.state.message} variant="success" />
        )}
        {error && <StatusPanel title={error.title} message={error.message} variant="error" />}

        <div className="form-field">
          <label htmlFor="login-username">Username</label>
          <input
            id="login-username"
            type="text"
            autoComplete="username"
            value={username}
            onChange={(event) => setUsername(event.target.value)}
            disabled={submitting}
            required
          />
        </div>

        <div className="form-field">
          <label htmlFor="login-password">Password</label>
          <input
            id="login-password"
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            disabled={submitting}
            required
          />
        </div>

        <button className="button button--large button--full" type="submit" disabled={submitting}>
          {submitting ? 'Signing in…' : 'Log in'}
        </button>
        <p className="auth-switch">
          New to this demo? <Link to="/register">Create an account</Link>
        </p>
      </form>
    </div>
  );
}
