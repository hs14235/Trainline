import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';

import api from '../api';
import Login from './Login';
import Register from './Register';

jest.mock('../api', () => ({
  __esModule: true,
  default: { post: jest.fn() },
  describeApiError: jest.fn(() => ({
    title: 'Request unsuccessful',
    message: 'The account request failed.',
  })),
}));

beforeEach(() => {
  jest.clearAllMocks();
  api.post.mockReset();
});

test('login labels fields and validates before sending credentials', async () => {
  render(
    <MemoryRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
      <Login onAuthenticated={jest.fn()} />
    </MemoryRouter>
  );

  expect(screen.getByLabelText('Username')).toHaveAttribute('autocomplete', 'username');
  expect(screen.getByLabelText('Password')).toHaveAttribute('autocomplete', 'current-password');
  await userEvent.click(screen.getByRole('button', { name: 'Log in' }));

  expect(screen.getByRole('heading', { name: 'Complete both fields' })).toBeInTheDocument();
  expect(api.post).not.toHaveBeenCalled();
});

test('login disables duplicate submission while authentication is pending', async () => {
  let resolveLogin;
  const onAuthenticated = jest.fn();
  api.post.mockImplementationOnce(
    () => new Promise((resolve) => {
      resolveLogin = resolve;
    })
  );
  render(
    <MemoryRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
      <Login onAuthenticated={onAuthenticated} />
    </MemoryRouter>
  );

  await userEvent.type(screen.getByLabelText('Username'), 'demo');
  await userEvent.type(screen.getByLabelText('Password'), 'safe-demo-password');
  await userEvent.click(screen.getByRole('button', { name: 'Log in' }));

  const pendingButton = screen.getByRole('button', { name: 'Signing in…' });
  expect(pendingButton).toBeDisabled();
  await userEvent.click(pendingButton);
  expect(api.post).toHaveBeenCalledTimes(1);

  resolveLogin({ data: { key: 'test-token' } });
  expect(await screen.findByRole('button', { name: 'Log in' })).toBeEnabled();
  expect(onAuthenticated).toHaveBeenCalledWith('test-token');
});

test('registration provides password guidance and catches a mismatch locally', async () => {
  render(
    <MemoryRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
      <Register />
    </MemoryRouter>
  );

  const password = screen.getByLabelText('Password');
  expect(password).toHaveAccessibleDescription(/at least 8 characters/i);

  await userEvent.type(screen.getByLabelText('Username'), 'traveller');
  await userEvent.type(screen.getByLabelText('Email'), 'traveller@example.test');
  await userEvent.type(password, 'first-password');
  await userEvent.type(screen.getByLabelText('Confirm password'), 'different-password');
  await userEvent.click(screen.getByRole('button', { name: 'Create account' }));

  expect(screen.getByRole('heading', { name: 'Passwords do not match' })).toBeInTheDocument();
  expect(api.post).not.toHaveBeenCalled();
});
