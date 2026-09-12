import axios from 'axios';

export const API_ORIGIN = (process.env.REACT_APP_API_BASE || 'http://127.0.0.1:8000').replace(
  /\/$/,
  ''
);

function getCookie(name) {
  const value = document.cookie
    .split('; ')
    .find((row) => row.startsWith(name + '='));
  return value ? decodeURIComponent(value.split('=')[1]) : null;
}

const api = axios.create({
  baseURL: API_ORIGIN + '/api',
  timeout: 15000,
});

const probeClient = axios.create({
  baseURL: API_ORIGIN,
  timeout: 5000,
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = 'Token ' + token;
  } else {
    delete config.headers.Authorization;
  }

  const csrfToken = getCookie('csrftoken');
  if (csrfToken) config.headers['X-CSRFToken'] = csrfToken;

  return config;
});

function flattenValidationMessages(data) {
  if (!data || typeof data !== 'object') return [];

  return Object.entries(data).flatMap(([field, value]) => {
    const label = field === 'non_field_errors' || field === 'detail' ? '' : field + ': ';
    const messages = Array.isArray(value) ? value : [value];
    return messages
      .filter((message) => typeof message === 'string' || typeof message === 'number')
      .map((message) => label + message);
  });
}

export function describeApiError(error, fallback = 'The request could not be completed.') {
  if (axios.isCancel(error) || error?.code === 'ERR_CANCELED') {
    return { kind: 'cancelled', title: 'Request cancelled', message: '', canRetry: false };
  }

  if (error?.code === 'ECONNABORTED') {
    return {
      kind: 'timeout',
      title: 'The service is taking longer than expected',
      message: 'Nothing was submitted again automatically. Check the service and retry when ready.',
      canRetry: true,
    };
  }

  if (!error?.response) {
    return {
      kind: 'network',
      title: 'Trainline is unavailable',
      message: 'Check your connection or wait for the local services to finish starting.',
      canRetry: true,
    };
  }

  const status = error.response.status;
  const details = flattenValidationMessages(error.response.data);
  const message = details.length ? details.join(' ') : fallback;

  if (status === 400) {
    return { kind: 'validation', title: 'Check the information provided', message, canRetry: false };
  }
  if (status === 401) {
    return {
      kind: 'authorization',
      title: 'Your session is no longer valid',
      message: 'Sign in again before continuing.',
      canRetry: false,
    };
  }
  if (status === 403) {
    return {
      kind: 'authorization',
      title: 'You do not have access to this item',
      message: 'Return to your own bookings or sign in with the correct account.',
      canRetry: false,
    };
  }
  if (status === 404) {
    return {
      kind: 'not-found',
      title: 'This item was not found',
      message: 'It may have been removed or may belong to another account.',
      canRetry: false,
    };
  }
  if (status === 409) {
    return { kind: 'conflict', title: 'The booking changed', message, canRetry: true };
  }
  if (status >= 500) {
    return {
      kind: 'service',
      title: 'The service is temporarily unavailable',
      message: 'Your request was not retried. Wait a moment, check service status, and try again.',
      canRetry: true,
    };
  }

  return { kind: 'request', title: 'Request unsuccessful', message, canRetry: false };
}

export async function checkServiceReadiness(options = {}) {
  const response = await probeClient.get('/readyz', options);
  return response.data?.status === 'ok';
}

export default api;
