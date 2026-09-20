import { act, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import api from '../api';
import SeatSelect from './SeatSelect';

jest.mock('../api', () => ({ __esModule: true, default: { get: jest.fn(), post: jest.fn() }, describeApiError: jest.fn((error, fallback) => ({ title: 'Trainline is unavailable', message: fallback, canRetry: true })) }));
const inventory = [
  { seat_number: '1A', car_number: '1', travel_class: 'first', available: true },
  { seat_number: '1B', car_number: '1', travel_class: 'first', available: false },
  { seat_number: '2A', car_number: '1', travel_class: 'standard', available: true },
];
const renderPage = () => render(<MemoryRouter initialEntries={['/select-seat/42']} future={{ v7_startTransition: true, v7_relativeSplatPath: true }}><Routes><Route path="/select-seat/:ticketId" element={<SeatSelect />} /><Route path="/" element={<div>Dashboard</div>} /></Routes></MemoryRouter>);
beforeEach(() => { jest.clearAllMocks(); window.sessionStorage.clear(); });

test('shows complete stable inventory and confirms a first-class reward', async () => {
  api.get.mockResolvedValueOnce({ data: { booking_reference: 'TL-000042', paid: true, train_trip: { trip_id: 'T00001' } } }).mockResolvedValueOnce({ data: inventory });
  api.post.mockResolvedValueOnce({ data: { status: 'seat assigned', seat_num: '1A', travel_class: 'first', first_class_bonus: true, membership_points: 2 } });
  renderPage();
  expect(await screen.findByRole('button', { name: /Seat 1B, first class, occupied/ })).toBeDisabled();
  await userEvent.click(screen.getByRole('button', { name: /Seat 1A, first class, available/ }));
  await userEvent.click(screen.getByRole('button', { name: 'Confirm seat' }));
  expect(api.post).toHaveBeenCalledWith('/seats/T00001/', { ticket_id: '42', seat_num: '1A' });
  expect(await screen.findByRole('heading', { name: 'Seat 1A' })).toBeInTheDocument();
  expect(screen.getByText('+1 first-class bonus')).toBeInTheDocument();
  expect(JSON.parse(sessionStorage.getItem('membershipReward')).total).toBe(2);
});

test('refreshes the full map after a lost race and clears selection', async () => {
  api.get.mockResolvedValueOnce({ data: { paid: true, train_trip: { trip_id: 'T00001' } } }).mockResolvedValueOnce({ data: inventory }).mockResolvedValueOnce({ data: inventory.map((seat) => seat.seat_number === '2A' ? { ...seat, available: false } : seat) });
  api.post.mockRejectedValueOnce({ response: { status: 409 } });
  renderPage();
  await userEvent.click(await screen.findByRole('button', { name: /Seat 2A, available/ }));
  await userEvent.click(screen.getByRole('button', { name: 'Confirm seat' }));
  expect(await screen.findByRole('heading', { name: 'That seat was just taken' })).toBeInTheDocument();
  await waitFor(() => expect(screen.getByRole('button', { name: /Seat 2A, occupied/ })).toBeDisabled());
  expect(screen.getByRole('button', { name: 'Confirm seat' })).toBeDisabled();
});

test('prevents duplicate seat submissions while pending', async () => {
  let resolvePost;
  api.get.mockResolvedValueOnce({ data: { paid: true, train_trip: { trip_id: 'T00001' } } }).mockResolvedValueOnce({ data: inventory });
  api.post.mockImplementationOnce(() => new Promise((resolve) => { resolvePost = resolve; }));
  renderPage(); await userEvent.click(await screen.findByRole('button', { name: /Seat 2A, available/ }));
  await userEvent.click(screen.getByRole('button', { name: 'Confirm seat' }));
  const pending = screen.getByRole('button', { name: 'Confirming…' }); expect(pending).toBeDisabled(); await userEvent.click(pending); expect(api.post).toHaveBeenCalledTimes(1);
  await act(async () => {
    resolvePost({ data: { seat_num: '2A', travel_class: 'standard', first_class_bonus: false } });
  });
  expect(await screen.findByRole('heading', { name: 'Seat 2A' })).toBeInTheDocument();
});
