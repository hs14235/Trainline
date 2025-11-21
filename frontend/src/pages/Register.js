import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api';

export default function Register() {
  const [email, setEmail] = useState('');
  const [password1, setPassword1] = useState('');
  const [password2, setPassword2] = useState('');
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    document.body.classList.add('bg-register');
    return () => document.body.classList.remove('bg-register');
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);

    if (password1 !== password2) {
      setError("Passwords don't match");
      return;
    }

    try {
      // (optional) prime CSRF if your api.js uses withCredentials
      await api.get('/dj-rest-auth/login/');

      await api.post('/dj-rest-auth/registration/', {
        email,
        password1,
        password2,
      });

      navigate('/login');
    } catch (err) {
      const data = err.response?.data;
      const msg = data
        ? Object.entries(data)
            .map(([field, msgs]) =>
              Array.isArray(msgs) ? `${field}: ${msgs.join(', ')}` : `${field}: ${msgs}`
            )
            .join('\n')
        : err.message;
      setError(msg);
    }
  };

  return (
    <form noValidate onSubmit={handleSubmit} className="signup-container">
      <h2>Register</h2>
      {error && <pre style={{ color:'crimson', whiteSpace:'pre-wrap' }}>{error}</pre>}

      <label>Email
        <input type="email" value={email} required onChange={e => setEmail(e.target.value)} />
      </label>

      <label>Password
        <input type="password" value={password1} required onChange={e => setPassword1(e.target.value)} />
      </label>

      <label>Confirm Password
        <input type="password" value={password2} required onChange={e => setPassword2(e.target.value)} />
      </label>

      <button type="submit" style={{ marginTop: '1rem' }}>Register</button>
    </form>
  );
}
