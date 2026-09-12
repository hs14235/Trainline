import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';

import api from '../api';
import BookFlight from './BookFlight';
import PaymentPage from './PaymentPage';

jest.mock('../api', () => ({
  __esModule: true,
  default: {
    get: jest.fn(),
    post: jest.fn(),
  },
  describeApiError: jest.fn((error, fallback) => ({
    title: 'Request unsuccessful',
    message: fallback,
    canRetry: true,
  })),
}));

beforeEach(() => {
  jest.clearAllMocks();
  api.get.mockReset();
  api.post.mockReset();
});

test('booking preserves choices and prevents duplicate ticket creation', async () => {
  let resolveBooking;
  api.get.mockResolvedValueOnce({
    data: {
      trip_id: 'DEMO001',
      service_number: 7001,
      origin_station: 'London St Pancras',
      destination_station: 'Paris Gare du Nord',
      status: 'Scheduled',
      platform: '5',
    },
  });
  api.post.mockImplementationOnce(
    () => new Promise((resolve) => {
      resolveBooking = resolve;
    })
  );

  render(
    <MemoryRouter
      initialEntries={['/book/DEMO001']}
      future={{ v7_startTransition: true, v7_relativeSplatPath: true }}
    >
      <Routes>
        <Route path="/book/:flightId" element={<BookFlight />} />
        <Route path="/payment/:ticketId" element={<div>Payment next</div>} />
      </Routes>
    </MemoryRouter>
  );

  expect(await screen.findByRole('heading', { name: /London St Pancras/i })).toBeInTheDocument();
  expect(screen.getByText(/this page does not calculate it/i)).toBeInTheDocument();
  await userEvent.click(screen.getByText('Onboard meal'));
  await userEvent.click(screen.getByRole('button', { name: 'Create booking' }));

  const pendingButton = screen.getByRole('button', { name: 'Creating booking…' });
  expect(pendingButton).toBeDisabled();
  await userEvent.click(pendingButton);
  expect(api.post).toHaveBeenCalledTimes(1);
  expect(api.post).toHaveBeenCalledWith('/train-trips/DEMO001/book/', {
    priority_boarding: false,
    meal: true,
    accommodation: false,
    taxi: false,
  });

  resolveBooking({ data: { ticket_id: 91, amount: 130 } });
  expect(await screen.findByText('Payment next')).toBeInTheDocument();
});

test('payment is explicitly demo-only and validates before mutation', async () => {
  api.get.mockResolvedValueOnce({
    data: { ticket_id: 91, amount: '130.00', paid: false, payment_method: null },
  });
  api.post.mockResolvedValueOnce({ data: { status: 'paid' } });

  render(
    <MemoryRouter
      initialEntries={['/payment/91']}
      future={{ v7_startTransition: true, v7_relativeSplatPath: true }}
    >
      <Routes>
        <Route path="/payment/:ticketId" element={<PaymentPage />} />
      </Routes>
    </MemoryRouter>
  );

  expect(await screen.findByText('$130.00')).toBeInTheDocument();
  expect(screen.getByText(/no money, card data, payment provider/i)).toBeInTheDocument();
  await userEvent.click(screen.getByRole('button', { name: 'Confirm demo payment' }));
  expect(screen.getByRole('heading', { name: 'Choose a demo payment method' })).toBeInTheDocument();
  expect(api.post).not.toHaveBeenCalled();

  await userEvent.click(screen.getByLabelText(/credit card label/i));
  await userEvent.click(screen.getByRole('button', { name: 'Confirm demo payment' }));
  expect(api.post).toHaveBeenCalledWith('/tickets/91/pay/', { payment_method: 'credit_card' });
  expect(await screen.findByRole('heading', { name: 'Demo payment marked successful' })).toBeInTheDocument();
});

test('an already-paid ticket never renders another payment mutation control', async () => {
  api.get.mockResolvedValueOnce({
    data: { ticket_id: 7, amount: '100.00', paid: true, payment_method: 'cash' },
  });

  render(
    <MemoryRouter
      initialEntries={['/payment/7']}
      future={{ v7_startTransition: true, v7_relativeSplatPath: true }}
    >
      <Routes>
        <Route path="/payment/:ticketId" element={<PaymentPage />} />
      </Routes>
    </MemoryRouter>
  );

  expect(await screen.findByRole('heading', { name: 'This ticket is already paid' })).toBeInTheDocument();
  expect(screen.queryByRole('button', { name: 'Confirm demo payment' })).not.toBeInTheDocument();
  expect(api.post).not.toHaveBeenCalled();
});
