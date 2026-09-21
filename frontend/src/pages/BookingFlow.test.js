import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import api from '../api';
import BookFlight from './BookFlight';
import PaymentPage from './PaymentPage';

jest.mock('../api', () => ({ __esModule: true, default: { get: jest.fn(), post: jest.fn() }, describeApiError: jest.fn((error, fallback) => ({ title: 'Request unsuccessful', message: fallback, canRetry: true })) }));
const quote = { base_fare: '100.00', subtotal: '100.00', taxes_and_fees: '0.00', total: '100.00', tax_rule: 'No taxes or additional fees are applied in this deterministic portfolio demo.', options: [], available_options: [{ key: 'meal', name: 'Onboard meal', description: 'Add a meal for your journey.', price: '30.00' }] };
beforeEach(() => { jest.clearAllMocks(); });

test('renders server options and prevents duplicate booking submission', async () => {
  let resolveBooking;
  api.get.mockImplementation((path, config = {}) => path.includes('/quote/') ? Promise.resolve({ data: config.params?.meal ? { ...quote, subtotal: '130.00', total: '130.00', options: [{ key: 'meal', name: 'Onboard meal', price: '30.00' }] } : quote }) : Promise.resolve({ data: { trip_id: 'DEMO001', service_number: 7001, origin_station: 'London St Pancras', destination_station: 'Paris Gare du Nord' } }));
  api.post.mockImplementationOnce(() => new Promise((resolve) => { resolveBooking = resolve; }));
  render(<MemoryRouter initialEntries={['/book/DEMO001']} future={{ v7_startTransition: true, v7_relativeSplatPath: true }}><Routes><Route path="/book/:flightId" element={<BookFlight />} /><Route path="/payment/:ticketId" element={<div>Payment next</div>} /></Routes></MemoryRouter>);
  expect(await screen.findByRole('heading', { name: /London St Pancras.*Paris Gare du Nord/ })).toBeInTheDocument();
  await userEvent.click(screen.getByText('Onboard meal'));
  await waitFor(() => expect(screen.getAllByText('$130.00')).toHaveLength(2));
  await userEvent.click(screen.getByRole('button', { name: 'Continue to demo payment' }));
  const pending = screen.getByRole('button', { name: 'Creating booking…' }); expect(pending).toBeDisabled();
  await userEvent.click(pending); expect(api.post).toHaveBeenCalledTimes(1);
  expect(api.post.mock.calls[0][1]).toEqual(expect.objectContaining({ meal: true, booking_key: expect.any(String) }));
  resolveBooking({ data: { ticket_id: 91 } });
  expect(await screen.findByText('Payment next')).toBeInTheDocument();
});

test('payment discloses demo status and requires a selected method', async () => {
  api.get.mockResolvedValueOnce({ data: { ticket_id: 91, booking_reference: 'TL-000091', paid: false, amount: '130.00', train_trip: { origin_station: 'London', destination_station: 'Paris' }, quote: { ...quote, total: '130.00' } } });
  api.post.mockResolvedValueOnce({ data: { status: 'paid', ticket: { ticket_id: 91, quote } } });
  render(<MemoryRouter initialEntries={['/payment/91']} future={{ v7_startTransition: true, v7_relativeSplatPath: true }}><Routes><Route path="/payment/:ticketId" element={<PaymentPage />} /></Routes></MemoryRouter>);
  expect(await screen.findByText(/no real money or financial details/i)).toBeInTheDocument();
  expect(screen.getByRole('button', { name: 'Confirm demo payment' })).toBeDisabled();
  await userEvent.click(screen.getByLabelText(/Credit card/i));
  await userEvent.click(screen.getByRole('button', { name: 'Confirm demo payment' }));
  expect(api.post).toHaveBeenCalledWith('/tickets/91/pay/', { payment_method: 'credit_card' });
  expect(await screen.findByRole('heading', { name: 'Demo payment complete' })).toBeInTheDocument();
});

test('already-paid booking has no second mutation control', async () => {
  api.get.mockResolvedValueOnce({ data: { ticket_id: 7, booking_reference: 'TL-000007', amount: '100.00', paid: true, train_trip: {}, quote } });
  render(<MemoryRouter initialEntries={['/payment/7']} future={{ v7_startTransition: true, v7_relativeSplatPath: true }}><Routes><Route path="/payment/:ticketId" element={<PaymentPage />} /></Routes></MemoryRouter>);
  expect(await screen.findByRole('heading', { name: 'Demo payment complete' })).toBeInTheDocument();
  expect(screen.queryByRole('button', { name: 'Confirm demo payment' })).not.toBeInTheDocument();
  expect(api.post).not.toHaveBeenCalled();
});
