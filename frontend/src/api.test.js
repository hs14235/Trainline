import { resolveApiOrigin } from './api';

test('an unconfigured API uses the browser origin instead of a hardcoded local endpoint', () => {
  expect(
    resolveApiOrigin({
      configuredOrigin: '',
      browserOrigin: 'https://frontend.example.test',
    })
  ).toBe('https://frontend.example.test');
});

test('a separate deployment API origin is normalized without changing its host', () => {
  expect(
    resolveApiOrigin({
      configuredOrigin: 'https://api.example.test/',
      browserOrigin: 'https://frontend.example.test',
    })
  ).toBe('https://api.example.test');
});
