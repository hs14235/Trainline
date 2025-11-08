import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../api'
import { useEffect } from 'react';

export default function Login() {
  const [email,    setEmail]    = useState('')
  const [password, setPassword] = useState('')
  const [error,    setError]    = useState(null)
  const navigate = useNavigate()

  const handleSubmit = async e => {
    e.preventDefault()
    setError(null)

    try {
      const res = await api.post('auth/login/', { email, password });
      localStorage.setItem('token', res.data.key || res.data.token);
      console.log('login response:', res.data)
      localStorage.setItem('token', res.data.key)
      window.location.href = '/'
    } catch (err) {
      console.error('login error', err.response || err)
      const data = err.response?.data
      const msg = data
        ? Object.entries(data)
            .map(([k, v]) => `${k}: ${v}`)
            .join('\n')
        : err.message
      setError(msg)
    }
  }
  useEffect(() => {
  document.body.classList.add('bg-login');
  return () => document.body.classList.remove('bg-login');
  }, []);


  return (
   <div className="login-container"> 
        <h2>Log In</h2>
      {error && (
        <pre style={{ color: 'crimson', whiteSpace: 'pre-wrap' }}>
          {error}
        </pre>
      )}

      <form noValidate onSubmit={handleSubmit}>
        <div style={{ marginBottom: '1rem' }}>
          <label>Email</label><br/>
          <input
            type="email"
            value={email}
            onChange={e => setEmail(e.target.value)}
            required
            style={{ width: '100%' }}
          />
        </div>

        <div style={{ marginBottom: '1rem' }}>
          <label>Password</label><br/>
          <input
            type="password"
            value={password}
            onChange={e => setPassword(e.target.value)}
            required
            style={{ width: '100%' }}
          />
        </div>

        <button
          type="submit"
          style={{
            padding: '0.5rem 1rem',
            background: '#074c6aff',
            color: 'white',
            border: 'none',
            borderRadius: 4,
          }}
        >
          Log In
        </button>
      </form>
    </div>
  )
}
