import { useEffect, useRef, useState } from 'react';

const guideTopics = [
  {
    label: 'Tickets',
    answer: 'Open the dashboard to review only your own tickets, payment state, options, and seat.',
  },
  {
    label: 'Seats',
    answer: 'Seat availability comes from the API. A conflict refreshes the choices without retrying the reservation.',
  },
  {
    label: 'Payments',
    answer: 'Payment is a demo-only state transition. The app never collects card details or moves money.',
  },
];

export default function ChatWidget() {
  const [open, setOpen] = useState(false);
  const [topic, setTopic] = useState(null);
  const panelRef = useRef(null);

  useEffect(() => {
    if (open) panelRef.current?.focus();
  }, [open]);

  return (
    <div className="utility-widget utility-widget--guide">
      {open && (
        <section
          id="guide-panel"
          className="utility-panel"
          aria-labelledby="guide-title"
          ref={panelRef}
          tabIndex="-1"
        >
          <div className="utility-panel__header">
            <div>
              <p className="eyebrow">Client-only demo</p>
              <h2 id="guide-title">Booking guide</h2>
            </div>
            <button className="icon-button" onClick={() => setOpen(false)} aria-label="Close booking guide">
              ×
            </button>
          </div>
          <p className="demo-disclosure">
            This is a local FAQ guide, not live chat or authenticated support.
          </p>
          <div className="guide-topics" aria-label="Guide topics">
            {guideTopics.map((item) => (
              <button
                key={item.label}
                className={'button button--quiet button--small' + (topic === item.label ? ' is-active' : '')}
                onClick={() => setTopic(item.label)}
                aria-pressed={topic === item.label}
              >
                {item.label}
              </button>
            ))}
          </div>
          <div className="guide-answer" role="status" aria-live="polite">
            {topic
              ? guideTopics.find((item) => item.label === topic)?.answer
              : 'Choose a topic for a short explanation.'}
          </div>
        </section>
      )}
      <button
        className="utility-trigger"
        onClick={() => setOpen((current) => !current)}
        aria-expanded={open}
        aria-controls="guide-panel"
        aria-label="Demo guide"
      >
        <span aria-hidden="true">?</span>
        <span>Demo guide</span>
      </button>
    </div>
  );
}
