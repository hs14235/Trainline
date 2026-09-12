import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import { checkServiceReadiness } from '../api';
import ServiceStatus from './ServiceStatus';

jest.mock('../api', () => ({
  checkServiceReadiness: jest.fn(),
}));

beforeEach(() => {
  jest.clearAllMocks();
});

test('reports database readiness after one successful probe', async () => {
  checkServiceReadiness.mockResolvedValueOnce(true);
  render(<ServiceStatus />);

  expect(screen.getByRole('status')).toHaveTextContent('Checking API readiness');
  expect(await screen.findByText('API and database ready')).toBeInTheDocument();
  expect(checkServiceReadiness).toHaveBeenCalledTimes(1);
});

test('shows a calm unavailable state and checks again only on request', async () => {
  checkServiceReadiness.mockRejectedValueOnce(new Error('offline')).mockResolvedValueOnce(true);
  render(<ServiceStatus />);

  expect(await screen.findByText('Service starting or unavailable')).toBeInTheDocument();
  expect(checkServiceReadiness).toHaveBeenCalledTimes(1);
  await userEvent.click(screen.getByRole('button', { name: 'Check again' }));
  expect(await screen.findByText('API and database ready')).toBeInTheDocument();
  expect(checkServiceReadiness).toHaveBeenCalledTimes(2);
});
