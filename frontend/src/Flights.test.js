import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';

import api from './api';
import Flights from './Flights';

jest.mock('./api', () => {
  const actual = jest.requireActual('./api');
  return {
    __esModule: true,
    ...actual,
    default: { get: jest.fn() },
  };
});

function renderFlights() {
  return render(
    <MemoryRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
      <Flights />
    </MemoryRouter>
  );
}

beforeEach(() => {
  jest.clearAllMocks();
  api.get.mockReset();
});

test('shows a loading state and then accessible trip details', async () => {
  let resolveRequest;
  api.get.mockImplementationOnce(
    () => new Promise((resolve) => {
      resolveRequest = resolve;
    })
  );

  renderFlights();
  expect(screen.getByRole('status')).toHaveTextContent('Searching the timetable');

  resolveRequest({
    data: [
      {
        trip_id: 'T1',
        service_number: 7001,
        origin_station: 'London St Pancras',
        destination_station: 'Paris Gare du Nord',
        status: 'Scheduled',
      },
    ],
  });

  expect(await screen.findByRole('heading', { name: /London St Pancras.*Paris Gare du Nord/ })).toBeInTheDocument();
  expect(screen.getByRole('button', { name: 'View trip' })).toBeEnabled();
  expect(screen.getByText('1 found')).toBeInTheDocument();
});

test('submits only API-supported filters', async () => {
  api.get.mockResolvedValue({ data: [] });
  renderFlights();
  await screen.findByRole('heading', { name: 'No trains match this search' });

  await userEvent.type(screen.getByLabelText('From'), 'London');
  await userEvent.type(screen.getByLabelText('To'), 'Paris');
  await userEvent.click(screen.getByRole('button', { name: 'Search' }));

  expect(api.get).toHaveBeenLastCalledWith(
    '/train-trips/',
    expect.objectContaining({
      params: {
        origin: 'London',
        destination: 'Paris',
        ordering: 'departure_time',
      },
    })
  );
});

test('shows a useful empty state and clear-filter recovery', async () => {
  api.get.mockResolvedValue({ data: [] });
  renderFlights();

  expect(await screen.findByRole('heading', { name: 'No trains match this search' })).toBeInTheDocument();
  expect(screen.getByRole('button', { name: 'Show all demo services' })).toBeEnabled();
});

test('distinguishes service unavailability and offers a read-only retry', async () => {
  api.get.mockRejectedValue(new Error('network'));
  renderFlights();

  expect(await screen.findByRole('heading', { name: 'Trainline is unavailable' })).toBeInTheDocument();
  api.get.mockResolvedValue({ data: [] });
  await userEvent.click(screen.getByRole('button', { name: 'Retry search' }));
  expect(api.get).toHaveBeenCalledTimes(2);
  expect(await screen.findByRole('heading', { name: 'No trains match this search' })).toBeInTheDocument();
});
