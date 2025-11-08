import React, { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import api from '../api'

export default function PaymentPage() {
  const { ticketId } = useParams()
  const navigate     = useNavigate()
  const [ticket, setTicket] = useState(null)
  const [method, setMethod] = useState('')
  const [error, setError]   = useState(null)

  useEffect(() => {
    const body = document.body;
    body.classList.add('bg-payment');
    return () => body.classList.remove('bg-payment');
  }, []);


  useEffect(() => {
    api.get(`tickets/${ticketId}/`)
      .then(res => setTicket(res.data))
      .catch(() => setError('Unable to load ticket'))
  }, [ticketId])

  if (error)   return <p style={{color:'crimson'}}>{error}</p>
  if (!ticket) return <p>Loading ticket…</p>

  const rawAmt = ticket.amount
  const amt    = isNaN(Number(rawAmt)) ? 0 : Number(rawAmt)

  const handlePay = async e => {
    e.preventDefault()
    try {
      await api.post(`tickets/${ticketId}/pay/`, { payment_method: method })
      window.location.href = '/'
    } catch (err) {
      setError(
        err.response?.data?.error ||
        JSON.stringify(err.response?.data) ||
        err.message
      )
    }
  }
  
  return (
    <form onSubmit={handlePay} style={{ maxWidth:400, margin:'2rem auto' }}>
      <h2>Pay for Ticket #{ticketId}</h2>
      <p>
        Amount due:{' '}
        <strong>${amt.toFixed(2)}</strong>
      </p>

      <label>
        Payment method
        <select
          value={method}
          onChange={e => setMethod(e.target.value)}
          required
        >
          <option value="" disabled>Select one…</option>
          <option value="cash">Cash</option>
          <option value="credit_card">Credit Card</option>
          <option value="check">Check</option>
        </select>
      </label>

      <button
        type="submit"
        style={{ display:'block', marginTop:'1rem' }}
      >
        Confirm Payment
      </button>
    </form>
  )
}
