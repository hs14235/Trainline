import axios from "axios";

const api = axios.create({
  baseURL: process.env.REACT_APP_API_BASE || "http://127.0.0.1:8000/api/",
  timeout: 15000,
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) {
    config.headers.Authorization = `Token ${token}`;
  } else {
    delete config.headers.Authorization;
  }
  return config;
});

api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err?.response?.status === 401) {
    }
    return Promise.reject(err);
  }
);

export async function getWithFallback(paths, config) {
  let lastError;
  for (const path of paths) {
    try {
      return await api.get(path, config);
    } catch (e) {
      lastError = e;
      const status = e?.response?.status;
      if (status && status >= 400 && status < 500 && status !== 404) break;
    }
  }
  throw lastError;
}

export function toTrainTrip(rec) {
  if (!rec) return null;
  return {
    id: rec.trip_id ?? rec.flight_id,
    serviceNumber: rec.service_number ?? rec.flight_number,
    from: rec.origin_station ?? rec.departure_airport,
    to: rec.destination_station ?? rec.arrival_airport,
    departsAt: rec.departure_time ?? null,
    arrivesAt: rec.arrival_time ?? null,
    platform: rec.platform ?? rec.gate ?? null,
  };
}

export default api;
