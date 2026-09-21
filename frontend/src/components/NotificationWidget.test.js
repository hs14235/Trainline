import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import api from '../api';
import NotificationWidget from './NotificationWidget';

jest.mock('../api', () => ({
  __esModule: true,
  default: { get: jest.fn(), post: jest.fn() },
  describeApiError: jest.fn((error, fallback) => ({
    title: 'Updates unavailable',
    message: fallback,
    canRetry: true,
  })),
}));

beforeEach(() => {
  jest.clearAllMocks();
});

test('shows structured event facts only when applicable and marks an event read', async () => {
  api.get.mockResolvedValueOnce({
    data: [
      {
        notification_id: 7,
        event_type: 'points_awarded',
        title: 'First-class bonus earned',
        message: 'Your confirmed first-class seat earned 1 bonus point.',
        booking_reference: 'TL-000042',
        route_snapshot: 'London → Paris',
        seat_snapshot: '1A',
        points_delta: 1,
        level_snapshot: 'Silver',
        is_level_up: false,
        read_status: 'unread',
        sent_date: '2026-09-20T12:00:00Z',
      },
    ],
  });
  api.post.mockResolvedValueOnce({ data: { status: 'ok' } });

  render(<NotificationWidget />);
  const trigger = await screen.findByRole('button', { name: 'Updates, 1 unread' });
  await userEvent.click(trigger);

  expect(screen.getByText('TL-000042')).toBeInTheDocument();
  expect(screen.getByText('London → Paris')).toBeInTheDocument();
  expect(screen.getByText('+1')).toBeInTheDocument();
  expect(screen.queryByText('Silver')).not.toBeInTheDocument();

  await userEvent.click(screen.getByRole('button', { name: 'Mark as read' }));
  expect(api.post).toHaveBeenCalledWith('/notifications/7/mark_read/');
  expect(screen.getByText('Read')).toBeInTheDocument();
});

test('closes with Escape and restores focus to the trigger', async () => {
  api.get.mockResolvedValueOnce({ data: [] });
  render(<NotificationWidget />);
  const trigger = await screen.findByRole('button', { name: 'Updates' });
  await userEvent.click(trigger);
  const panel = screen.getByRole('region', { name: 'Updates' });
  expect(panel).toHaveFocus();
  await userEvent.keyboard('{Escape}');
  expect(screen.queryByRole('region', { name: 'Updates' })).not.toBeInTheDocument();
  expect(trigger).toHaveFocus();
});
