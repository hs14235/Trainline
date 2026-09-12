import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';

import api from '../api';
import SeatSelect from './SeatSelect';

jest.mock('../api', () => ({
  __esModule: true,
  default: {
    get: jest.fn(),
    post: jest.fn(),
  },
  describeApiError: jest.fn((error, fallback) => ({
    title: 'Trainline is unavailable',
    message: fallback,
    canRetry: true,
  })),
}));

function renderSeatSelect() {
  return render(
    <MemoryRouter
      initialEntries={['/select-seat/42']}
      future={{ v7_startTransition: true, v7_relativeSplatPath: true }}
    >
      <Routes>
        <Route path="/select-seat/:ticketId" element={<SeatSelect />} />
        <Route path="/" element={<div>Dashboard</div>} />
      </Routes>
    </MemoryRouter>
  );
}

beforeEach(() => {
  jest.clearAllMocks();
  api.get.mockReset();
  api.post.mockReset();
});

test('selects first, then reserves through the guarded endpoint', async () => {
  api.get
    .mockResolvedValueOnce({ data: { train_trip: { trip_id: 'T00001' } } })
    .mockResolvedValueOnce({ data: ['1A', '1B'] });
  api.post.mockResolvedValueOnce({ data: { status: 'seat assigned', seat_num: '1A' } });

  renderSeatSelect();
  const seat = await screen.findByRole('button', { name: 'Seat 1A, available' });
  const confirm = screen.getByRole('button', { name: 'Confirm seat' });
  expect(confirm).toBeDisabled();

  await userEvent.click(seat);
  expect(screen.getByRole('button', { name: 'Seat 1A, selected' })).toHaveAttribute(
    'aria-pressed',
    'true'
  );
  expect(api.post).not.toHaveBeenCalled();

  await userEvent.click(confirm);

  expect(api.get).toHaveBeenNthCalledWith(1, '/tickets/42/', expect.objectContaining({ signal: expect.anything() }));
  expect(api.get).toHaveBeenNthCalledWith(2, '/seats/T00001/', expect.objectContaining({ signal: expect.anything() }));
  expect(api.post).toHaveBeenCalledWith('/seats/T00001/', {
    ticket_id: '42',
    seat_num: '1A',
  });
  expect(await screen.findByRole('heading', { name: '1A' })).toBeInTheDocument();
});

test('explains a 409 conflict, refreshes availability, and keeps another choice usable', async () => {
  api.get
    .mockResolvedValueOnce({ data: { train_trip: { trip_id: 'T00001' } } })
    .mockResolvedValueOnce({ data: ['1A', '1B'] })
    .mockResolvedValueOnce({ data: ['1B'] });
  api.post.mockRejectedValueOnce({
    response: { status: 409, data: { seat_num: ['Seat already taken'] } },
  });

  renderSeatSelect();
  await userEvent.click(await screen.findByRole('button', { name: 'Seat 1A, available' }));
  await userEvent.click(screen.getByRole('button', { name: 'Confirm seat' }));

  expect(await screen.findByRole('heading', { name: 'That seat was just taken' })).toBeInTheDocument();
  expect(screen.getByText(/another booking reserved 1A/i)).toBeInTheDocument();
  await waitFor(() => {
    expect(screen.getByRole('button', { name: 'Seat 1A, unavailable' })).toBeDisabled();
  });
  expect(screen.getByRole('button', { name: 'Seat 1B, available' })).toBeEnabled();
  expect(api.get).toHaveBeenNthCalledWith(3, '/seats/T00001/');
});

test('prevents duplicate reservation submissions while the mutation is pending', async () => {
  let resolvePost;
  api.get
    .mockResolvedValueOnce({ data: { train_trip: { trip_id: 'T00001' } } })
    .mockResolvedValueOnce({ data: ['2A'] });
  api.post.mockImplementationOnce(
    () => new Promise((resolve) => {
      resolvePost = resolve;
    })
  );

  renderSeatSelect();
  await userEvent.click(await screen.findByRole('button', { name: 'Seat 2A, available' }));
  const confirm = screen.getByRole('button', { name: 'Confirm seat' });
  await userEvent.click(confirm);
  expect(screen.getByRole('button', { name: 'Reserving seat…' })).toBeDisabled();
  await userEvent.click(screen.getByRole('button', { name: 'Reserving seat…' }));
  expect(api.post).toHaveBeenCalledTimes(1);

  resolvePost({ data: { status: 'seat assigned', seat_num: '2A' } });
  expect(await screen.findByRole('heading', { name: '2A' })).toBeInTheDocument();
});

test('shows an intentional empty state when no seats remain', async () => {
  api.get
    .mockResolvedValueOnce({ data: { train_trip: { trip_id: 'T00001' } } })
    .mockResolvedValueOnce({ data: [] });

  renderSeatSelect();

  expect(await screen.findByRole('heading', { name: 'No seats are currently available' })).toBeInTheDocument();
  expect(screen.getByRole('button', { name: 'Confirm seat' })).toBeDisabled();
});
