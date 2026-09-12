import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';

import api, { describeApiError } from '../api';
import StatusPanel from '../components/StatusPanel';

export default function Register() {
  const [form, setForm] = useState({
    username: '',
    email: '',
    password1: '',
    password2: '',
  });
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    document.body.classList.add('bg-register');
    return () => document.body.classList.remove('bg-register');
  }, []);

  const updateField = (event) => {
    setForm((current) => ({ ...current, [event.target.name]: event.target.value }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (submitting) return;

    if (!form.username.trim() || !form.email.trim() || !form.password1 || !form.password2) {
      setError({ title: 'Complete every field', message: 'All account fields are required.' });
      return;
    }
    if (form.password1 !== form.password2) {
      setError({ title: 'Passwords do not match', message: 'Re-enter the same password in both fields.' });
      return;
    }
    if (form.password1.length < 8) {
      setError({ title: 'Use a longer password', message: 'Passwords must contain at least 8 characters.' });
      return;
    }

    setSubmitting(true);
    setError(null);
    try {
      await api.post('/dj-rest-auth/registration/', {
        username: form.username.trim(),
        email: form.email.trim(),
        password1: form.password1,
        password2: form.password2,
      });
      navigate('/login', {
        replace: true,
        state: { message: 'Your local account is ready. Sign in to continue.' },
      });
    } catch (requestError) {
      setError(describeApiError(requestError, 'The account could not be created.'));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="auth-layout">
      <section className="auth-intro" aria-labelledby="register-heading">
        <p className="eyebrow">Local account setup</p>
        <h1 id="register-heading">Create your Trainline account</h1>
        <p>
          Registration uses the existing Django authentication contract. Never reuse a real password
          in this portfolio demo.
        </p>
      </section>

      <form className="auth-card surface" noValidate onSubmit={handleSubmit}>
        <div>
          <p className="eyebrow">Required details</p>
          <h2>Create account</h2>
          <p className="form-help">All fields stay within the locally configured application.</p>
        </div>

        {error && <StatusPanel title={error.title} message={error.message} variant="error" />}

        <div className="form-field">
          <label htmlFor="register-username">Username</label>
          <input
            id="register-username"
            name="username"
            type="text"
            autoComplete="username"
            value={form.username}
            onChange={updateField}
            disabled={submitting}
            required
          />
        </div>
        <div className="form-field">
          <label htmlFor="register-email">Email</label>
          <input
            id="register-email"
            name="email"
            type="email"
            autoComplete="email"
            value={form.email}
            onChange={updateField}
            disabled={submitting}
            required
          />
        </div>
        <div className="form-field">
          <label htmlFor="register-password">Password</label>
          <input
            id="register-password"
            name="password1"
            type="password"
            autoComplete="new-password"
            aria-describedby="password-guidance"
            value={form.password1}
            onChange={updateField}
            disabled={submitting}
            required
          />
          <p id="password-guidance" className="field-hint">
            Use at least 8 characters and avoid common or entirely numeric passwords.
          </p>
        </div>
        <div className="form-field">
          <label htmlFor="register-password-confirm">Confirm password</label>
          <input
            id="register-password-confirm"
            name="password2"
            type="password"
            autoComplete="new-password"
            value={form.password2}
            onChange={updateField}
            disabled={submitting}
            required
          />
        </div>

        <button className="button button--large button--full" type="submit" disabled={submitting}>
          {submitting ? 'Creating account…' : 'Create account'}
        </button>
        <p className="auth-switch">
          Already registered? <Link to="/login">Log in</Link>
        </p>
      </form>
    </div>
  );
}
