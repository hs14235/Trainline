// src/components/ChatWidget.jsx
import React, { useState } from 'react';

const canned = [
  { trigger: /ticket/i, response: "For ticket issues, please check your booking history or contact support@trainline.com." },
  { trigger: /membership/i, response: "Membership tiers update after you complete fully‑loaded the amenities for your trip. Your current membership level is: ${membershipLevel}"  },
  { trigger: /account/i, response: "You can update your email & password on your profile page (coming soon!)." },
  { trigger: /.*/, response: "Sorry, currently I can only encompass a few prompts. Try 'ticket', 'membership', or 'account'." },
];

export default function ChatWidget() {
  const [open, setOpen] = useState(false);
  const [msgs, setMsgs] = useState([
    { from: 'bot', text: "Hi! How can I help today?" }
  ]);
  const [entry, setEntry] = useState('');

  const send = () => {
    if (!entry.trim()) return;
    const you = { from: 'you', text: entry };
    const bot = canned.find(c => c.trigger.test(entry)) || canned[canned.length - 1];
    setMsgs([...msgs, you, { from:'bot', text: bot.response }]);
    setEntry('');
  };

  return (
    <div style={{
      position: 'fixed', bottom: 20, right: 20,
      width: open ? 300 : 60, height: open ? 400 : 60,
      background: '#fff', boxShadow: '0 0 8px rgba(0,0,0,0.2)',
      borderRadius: 8, overflow: 'hidden',
      fontFamily: 'sans-serif', transition: 'all .2s'
    }}>
      <div
        onClick={() => setOpen(o => !o)}
        style={{
          background: '#007b5e', color: 'white',
          height: 60, cursor: 'pointer',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: 24
        }}>
        💬
      </div>
      {open && (
        <div style={{ display:'flex', flexDirection:'column', height:'calc(100% - 60px)' }}>
          <div style={{ flex:1, padding:8, overflowY:'auto' }}>
            {msgs.map((m,i) => (
              <div key={i} style={{
                textAlign: m.from==='you' ? 'right' : 'left',
                margin: '4px 0'
              }}>
                <span style={{
                  display:'inline-block',
                  background: m.from==='you' ? '#007b5e' : '#eee',
                  color: m.from==='you' ? 'white' : 'black',
                  padding: '6px 10px',
                  borderRadius: 12,
                  maxWidth: '80%'
                }}>
                  {m.text}
                </span>
              </div>
            ))}
          </div>
          <div style={{ padding:8, borderTop:'1px solid #ddd' }}>
            <input
              value={entry}
              onChange={e => setEntry(e.target.value)}
              onKeyDown={e => e.key==='Enter' && send()}
              placeholder="Type a message…" 
              style={{
                width: '100%', padding: '8px', boxSizing: 'border-box'
              }}
            />
          </div>
        </div>
      )}
    </div>
  );
}
