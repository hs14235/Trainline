import React, { useEffect, useState } from "react";
import api from "../api";

export default function NotificationWidget() {
  const [notes, setNotes] = useState([]);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    api.get("notifications/")
       .then(res => setNotes(res.data))
       .catch(console.error);
  }, []);

  return (
    <div style={{
      position: "fixed",
      bottom: 20,
      left: 20,
      width: open ? 300 : 60,
      height: open ? 400 : 60,
      background: "rgba(255, 255, 255, 0.95)",
      boxShadow: "0 0 8px rgba(0, 0, 0, 0.2)",
      color: "#333",
      borderRadius: 8,
      overflow: "hidden",
      fontFamily: "sans-serif",
      transition: "all .2s ease"
    }}>
      <div
        onClick={() => setOpen(o => !o)}
        style={{
          background: "linear-gradient(135deg, #0fb77a, #0b4a6f)",
          color: "white",
          height: 60,
          cursor: "pointer",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: 24,
          transition: "filter .15s ease"
        }}
        onMouseEnter={(e) => e.currentTarget.style.filter = "brightness(1.1)"}
        onMouseLeave={(e) => e.currentTarget.style.filter = "brightness(1)"}
      >
        🔔
      </div>
      {open && (
        <div style={{
          padding: 12,
          height: "calc(100% - 60px)",
          overflowY: "auto"
        }}>
          <h4 style={{ margin: "0 0 12px 0" }}>Notifications</h4>
          {notes.length === 0
            ? <p style={{ color: "#666" }}>No new notifications</p>
            : notes.map(n => (
                <div key={n.notification_id} style={{
                  marginBottom: 12,
                  padding: 8,
                  background: "#f5f5f5",
                  borderRadius: 6
                }}>
                  <small style={{ color: "#888" }}>
                    {new Date(n.sent_date).toLocaleString()}
                  </small>
                  <p style={{ margin: "4px 0 0 0" }}>{n.message}</p>
                </div>
              ))
          }
        </div>
      )}
    </div>
  );
}
