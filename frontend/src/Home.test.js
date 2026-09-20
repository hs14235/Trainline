import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';

import api from './api';
import Home from './Home';

jest.mock('./api', () => {
  const actual = jest.requireActual('./api');
  return {
    __esModule: true,
    ...actual,
    default: {
      get: jest.fn(),
      delete: jest.fn(),
    },
  };
});

const ticket = {
  ticket_id: 12,
  amount: '100.00',
  paid: false,
  seat_num: null,
  payment_method: null,
  booked_at: '2026-09-11T12:00:00Z',
  priority_boarding: false,
  meal: false,
  accommodation: false,
  taxi: false,
  train_trip: {
    service_number: 7001,
    origin_station: 'London St Pancras',
    destination_station: 'Paris Gare du Nord',
  },
};

function renderHome() {
  window.localStorage.setItem('token', 'test-token');
  return render(
    <MemoryRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
      <Home />
    </MemoryRouter>
  );
}

beforeEach(() => {
  jest.clearAllMocks();
  api.get.mockReset();
  api.delete.mockReset();
  window.localStorage.clear();
});

test('keeps ticket data visible when the profile request fails independently', async () => {
  api.get.mockImplementation((path) =>
    path === '/me/' ? Promise.reject(new Error('profile unavailable')) : Promise.resolve({ data: [ticket] })
  );

  renderHome();

  expect(await screen.findByRole('heading', { name: /London St Pancras.*Paris Gare du Nord/ })).toBeInTheDocument();
  expect(screen.getByRole('heading', { name: 'Trainline is unavailable' })).toBeInTheDocument();
  expect(screen.getByText(/journeys may still be available below/i)).toBeInTheDocument();
});

test('requires explicit confirmation before cancelling a ticket', async () => {
  api.get
    .mockResolvedValueOnce({
      data: { first_name: 'Demo', membership_level: 'Bronze', membership_points: 1 },
    })
    .mockResolvedValueOnce({ data: [ticket] });
  api.delete.mockResolvedValueOnce({ status: 204 });

  renderHome();
  await screen.findByRole('heading', { name: /London St Pancras.*Paris Gare du Nord/ });
  await userEvent.click(screen.getByRole('button', { name: 'Manage booking' }));
  await userEvent.click(screen.getByRole('button', { name: 'Cancel booking' }));

  expect(api.delete).not.toHaveBeenCalled();
  expect(screen.getByText(/releases its selected seat/i)).toBeInTheDocument();
  api.get.mockResolvedValueOnce({ data: { membership_level: 'Bronze', membership_points: 0 } });
  await userEvent.click(screen.getByRole('button', { name: 'Yes, cancel booking' }));

  expect(api.delete).toHaveBeenCalledWith('/tickets/12/');
  expect(await screen.findByRole('heading', { name: 'No bookings yet' })).toBeInTheDocument();
});
