import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';

import App from './App';

jest.mock('./components/ServiceStatus', () => () => <div>API and database ready</div>);
jest.mock('./components/NotificationWidget', () => () => <button>Updates</button>);

jest.mock('./api', () => ({
  __esModule: true,
  default: {
    get: jest.fn(() => Promise.resolve({ data: [] })),
    post: jest.fn(),
  },
  checkServiceReadiness: jest.fn(() => Promise.resolve(true)),
  describeApiError: jest.fn(() => ({
    title: 'Request unsuccessful',
    message: 'Try again.',
  })),
}));

beforeEach(() => {
  window.localStorage.clear();
});

test('shows labeled account navigation to an anonymous visitor', () => {
  render(
    <MemoryRouter
      initialEntries={['/login']}
      future={{ v7_startTransition: true, v7_relativeSplatPath: true }}
    >
      <App />
    </MemoryRouter>
  );

  expect(screen.getByRole('heading', { name: /sign in to trainline/i })).toBeInTheDocument();
  expect(screen.getByRole('navigation', { name: 'Primary navigation' })).toBeInTheDocument();
  expect(screen.getByRole('link', { name: 'Create account' })).toBeInTheDocument();
  expect(screen.getByRole('link', { name: 'Log in' })).toHaveAttribute('aria-current', 'page');
  expect(screen.getByText('API and database ready')).toBeInTheDocument();
});

test('redirects protected routes to login without a token', async () => {
  render(
    <MemoryRouter
      initialEntries={['/flights']}
      future={{ v7_startTransition: true, v7_relativeSplatPath: true }}
    >
      <App />
    </MemoryRouter>
  );

  expect(await screen.findByRole('heading', { name: /sign in to trainline/i })).toBeInTheDocument();
});

test('keeps the honest engineering page public and exposes active navigation', async () => {
  render(
    <MemoryRouter
      initialEntries={['/engineering']}
      future={{ v7_startTransition: true, v7_relativeSplatPath: true }}
    >
      <App />
    </MemoryRouter>
  );

  expect(screen.getByRole('heading', { name: 'Built as a complete booking system' })).toBeInTheDocument();
  expect(screen.getByRole('link', { name: 'Engineering' })).toHaveAttribute('aria-current', 'page');
  expect(screen.getByText(/not monetary processing/i)).toBeInTheDocument();
  expect(screen.getByText(/no public deployment/i)).toBeInTheDocument();
});

test('authenticated navigation includes dashboard, trips, and logout', () => {
  window.localStorage.setItem('token', 'test-token');
  render(
    <MemoryRouter
      initialEntries={['/engineering']}
      future={{ v7_startTransition: true, v7_relativeSplatPath: true }}
    >
      <App />
    </MemoryRouter>
  );

  expect(screen.getByRole('link', { name: 'Dashboard' })).toBeInTheDocument();
  expect(screen.getByRole('link', { name: 'Find trains' })).toBeInTheDocument();
  expect(screen.getByRole('button', { name: 'Log out' })).toBeInTheDocument();
  expect(screen.getByRole('button', { name: /updates/i })).toBeInTheDocument();
  expect(screen.queryByRole('button', { name: /demo guide/i })).not.toBeInTheDocument();
});
