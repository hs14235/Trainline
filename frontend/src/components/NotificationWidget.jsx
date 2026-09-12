import { useCallback, useEffect, useRef, useState } from 'react';

import api, { describeApiError } from '../api';

export default function NotificationWidget() {
  const [notes, setNotes] = useState([]);
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const panelRef = useRef(null);

  const loadNotifications = useCallback(async (signal) => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.get('/notifications/', { signal });
      setNotes(response.data);
    } catch (requestError) {
      if (requestError?.code !== 'ERR_CANCELED') {
        setError(describeApiError(requestError, 'Notifications could not be loaded.'));
      }
    } finally {
      if (!signal?.aborted) setLoading(false);
    }
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    loadNotifications(controller.signal);
    return () => controller.abort();
  }, [loadNotifications]);

  useEffect(() => {
    if (open) panelRef.current?.focus();
  }, [open]);

  const markRead = async (notificationId) => {
    const current = notes.find((note) => note.notification_id === notificationId);
    if (!current || current.read_status === 'read') return;
    try {
      await api.post('/notifications/' + notificationId + '/mark_read/');
      setNotes((items) =>
        items.map((note) =>
          note.notification_id === notificationId ? { ...note, read_status: 'read' } : note
        )
      );
    } catch (requestError) {
      setError(describeApiError(requestError, 'The notification could not be marked as read.'));
    }
  };

  const unreadCount = notes.filter((note) => note.read_status !== 'read').length;

  return (
    <div className="utility-widget utility-widget--notifications">
      {open && (
        <section
          id="notifications-panel"
          className="utility-panel"
          aria-labelledby="notifications-title"
          ref={panelRef}
          tabIndex="-1"
        >
          <div className="utility-panel__header">
            <div>
              <p className="eyebrow">Account updates</p>
              <h2 id="notifications-title">Notifications</h2>
            </div>
            <button className="icon-button" onClick={() => setOpen(false)} aria-label="Close notifications">
              ×
            </button>
          </div>
          {loading ? (
            <p role="status">Loading notifications…</p>
          ) : error ? (
            <div className="widget-error" role="alert">
              <strong>{error.title}</strong>
              <p>{error.message}</p>
              {error.canRetry && (
                <button className="button button--small" onClick={() => loadNotifications()}>
                  Retry
                </button>
              )}
            </div>
          ) : notes.length === 0 ? (
            <p className="widget-empty">No notifications for this account.</p>
          ) : (
            <ul className="notification-list">
              {notes.map((note) => {
                const unread = note.read_status !== 'read';
                return (
                  <li className={unread ? 'notification notification--unread' : 'notification'} key={note.notification_id}>
                    <div>
                      <span className="status-chip status-chip--compact">
                        {unread ? 'Unread' : 'Read'}
                      </span>
                      <time dateTime={note.sent_date || undefined}>
                        {note.sent_date ? new Date(note.sent_date).toLocaleString() : 'Date unavailable'}
                      </time>
                    </div>
                    <p>{note.message}</p>
                    {unread && (
                      <button className="text-link" onClick={() => markRead(note.notification_id)}>
                        Mark as read
                      </button>
                    )}
                  </li>
                );
              })}
            </ul>
          )}
        </section>
      )}
      <button
        className="utility-trigger"
        onClick={() => setOpen((current) => !current)}
        aria-expanded={open}
        aria-controls="notifications-panel"
        aria-label={unreadCount > 0 ? `Updates, ${unreadCount} unread` : 'Updates'}
      >
        <span aria-hidden="true">⌁</span>
        <span>Updates</span>
        {unreadCount > 0 && <strong aria-hidden="true">{unreadCount}</strong>}
      </button>
    </div>
  );
}
