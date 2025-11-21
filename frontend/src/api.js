// src/api.js
import axios from "axios";

function getCookie(name) {
  const value = document.cookie
    .split("; ")
    .find(row => row.startsWith(name + "="));
  return value ? decodeURIComponent(value.split("=")[1]) : null;
}

const api = axios.create({
  baseURL: process.env.REACT_APP_API_BASE || "http://127.0.0.1:8000",
  timeout: 15000,
 });

api.interceptors.request.use((config) => {
  // Auth token (from dj-rest-auth login)
  const token = localStorage.getItem("token");
  if (token) {
    config.headers.Authorization = `Token ${token}`;
  } else {
    delete config.headers.Authorization;
  }

  // CSRF token (for POST/PUT/PATCH/DELETE)
  const csrftoken = getCookie("csrftoken");
  if (csrftoken) {
    config.headers["X-CSRFToken"] = csrftoken;
  }

  return config;
});

export default api;

// optional helper used elsewhere
export async function getWithFallback(paths, config) {
  let lastError;
  for (const p of paths) {
    try { return await api.get(p, config); } catch (e) {
      lastError = e; const s = e?.response?.status;
      if (s && s >= 400 && s < 500 && s !== 404) break;
    }
  }
  throw lastError;
}
