import { useCallback, useEffect, useState } from 'react';

import { checkServiceReadiness } from '../api';

export default function ServiceStatus() {
  const [status, setStatus] = useState('checking');

  const check = useCallback(async (signal) => {
    setStatus('checking');
    try {
      const ready = await checkServiceReadiness({ signal });
      setStatus(ready ? 'ready' : 'unavailable');
    } catch (error) {
      if (error?.code !== 'ERR_CANCELED') setStatus('unavailable');
    }
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    check(controller.signal);
    return () => controller.abort();
  }, [check]);

  const labels = {
    checking: 'Checking API readiness',
    ready: 'API and database ready',
    unavailable: 'Service starting or unavailable',
  };

  return (
    <div className={'service-status service-status--' + status} role="status" aria-live="polite">
      <span className="service-status__dot" aria-hidden="true" />
      <span>{labels[status]}</span>
      {status === 'unavailable' && (
        <button className="service-status__retry" onClick={() => check()}>
          Check again
        </button>
      )}
    </div>
  );
}
