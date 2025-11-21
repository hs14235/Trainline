import { useState } from "react";
import api from "../api";

export default function Register() {
  const [email, setEmail] = useState("");
  const [password1, setPassword1] = useState("");
  const [password2, setPassword2] = useState("");
  const [msg, setMsg] = useState("");

  const handleRegister = async (e) => {
    e.preventDefault();
    setMsg("");

    try {
      // 1) prime CSRF cookie
      await api.get("/dj-rest-auth/login/");

      // 2) register user
      await api.post("/dj-rest-auth/registration/", {
        email,
        password1,
        password2,
      });

      // 3) login to get token; store for future API calls
      const login = await api.post("/dj-rest-auth/login/", {
        email,
        password,
      });
      localStorage.setItem("token", login.data.key);

      setMsg("Registered and logged in. ✅");
    } catch (err) {
      const detail =
        err?.response?.data ??
        err?.message ??
        "Registration failed";
      setMsg(typeof detail === "string" ? detail : JSON.stringify(detail));
      console.error(err);
    }
  };

  return (
    <form onSubmit={handleRegister} style={{ maxWidth: 420 }}>
      <h2>Register</h2>
      <label>Email</label>
      <input value={email} onChange={(e) => setEmail(e.target.value)} />

      <label>Password</label>
      <input type="password" value={password1} onChange={(e) => setPassword1(e.target.value)} />

      <label>Confirm Password</label>
      <input type="password" value={password2} onChange={(e) => setPassword2(e.target.value)} />

      <button type="submit">Register</button>

      {msg && <p style={{ marginTop: 12, color: msg.includes("✅") ? "green" : "crimson" }}>{msg}</p>}
    </form>
  );
}
