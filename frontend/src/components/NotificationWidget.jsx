import React, { useEffect, useState } from "react";
import api from "../api";

export default function NotificationWidget() {
  const [notes, setNotes] = useState([]);

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
      width: 100,
      height: 400,
      maxHeight: 400,
      overflowY: "auto",
      background: "transparent",
      boxShadow: "0 0 8px rgba(9, 196, 2, 0.48)",
      color: "rgba(255, 250, 250, 1)",
      borderRadius: 8,
      padding: 8,
      fontFamily: "sans-serif"
    }}>
      <h4>Notifications</h4>
      {notes.length === 0
        ? <p>No new notifications</p>
        : notes.map(n => (
            <div key={n.notification_id} style={{ marginBottom: 6 }}>
              <small style={{ color: "#888" }}>
                {new Date(n.sent_date).toLocaleString()}
              </small>
              <p>{n.message}</p>
            </div>
          ))
      }
    </div>
  );
}
