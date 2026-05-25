/**
 * GreenOps — Auth API Client
 *
 * Handles login, register, demo login, refresh, and token storage.
 */

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

const TOKEN_KEY = "greenops_token";
const REFRESH_KEY = "greenops_refresh";
const USER_KEY = "greenops_user";

// ============================================================
// TOKEN STORAGE
// ============================================================

export function getStoredToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function getStoredUser() {
  const raw = localStorage.getItem(USER_KEY);
  return raw ? JSON.parse(raw) : null;
}

export function storeAuth(accessToken, refreshToken, user) {
  localStorage.setItem(TOKEN_KEY, accessToken);
  localStorage.setItem(REFRESH_KEY, refreshToken);
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function clearAuth() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(REFRESH_KEY);
  localStorage.removeItem(USER_KEY);
}

// ============================================================
// AUTH API CALLS
// ============================================================

async function authFetch(url, body) {
  const res = await fetch(`${API_BASE}${url}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  const data = await res.json();

  if (!res.ok) {
    throw new Error(data.detail || `HTTP ${res.status}`);
  }

  // Store tokens on successful auth
  storeAuth(data.access_token, data.refresh_token, data.user);
  return data;
}

export const loginUser = (email, password) =>
  authFetch("/auth/login", { email, password });

export const registerUser = (name, email, password) =>
  authFetch("/auth/register", { name, email, password });

export const loginDemo = () =>
  authFetch("/auth/demo", {});

export const refreshToken = async () => {
  const refresh = localStorage.getItem(REFRESH_KEY);
  if (!refresh) return null;
  try {
    return await authFetch("/auth/refresh", { refresh_token: refresh });
  } catch {
    clearAuth();
    return null;
  }
};

export const getProfile = async () => {
  const token = getStoredToken();
  if (!token) return null;

  const res = await fetch(`${API_BASE}/auth/me`, {
    headers: { Authorization: `Bearer ${token}` },
  });

  if (!res.ok) return null;
  return res.json();
};
