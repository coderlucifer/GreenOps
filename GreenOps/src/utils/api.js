/**
 * GreenOps — API Client
 *
 * Centralized API calls to the GreenOps backend.
 */

import { getStoredToken } from "./auth";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function fetchJSON(url, options = {}) {
  const token = getStoredToken();
  const headers = {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(options.headers || {}),
  };

  const res = await fetch(`${API_BASE}${url}`, {
    ...options,
    headers,
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: "Unknown error" }));
    throw new Error(error.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

// Dashboard
export const getDashboard = (days = 30, project = null) => {
  const params = new URLSearchParams({ days });
  if (project) params.set("project", project);
  return fetchJSON(`/api/dashboard?${params}`);
};

// Recent calls
export const getCalls = (limit = 20, offset = 0, filters = {}) => {
  const params = new URLSearchParams({ limit, offset, ...filters });
  return fetchJSON(`/api/calls?${params}`);
};

// Model catalog
export const getModelCatalog = (provider = null) => {
  const params = provider ? `?provider=${provider}` : "";
  return fetchJSON(`/api/models/catalog${params}`);
};

// Model usage
export const getModelUsage = () => fetchJSON("/api/models/usage");

// Model comparison
export const compareModels = (inputTokens = 1000, outputTokens = 500, region = "global_average") =>
  fetchJSON("/api/models/compare", {
    method: "POST",
    body: JSON.stringify({
      input_tokens: inputTokens,
      output_tokens: outputTokens,
      region,
    }),
  });

// Budget
export const getBudget = (project = "default") =>
  fetchJSON(`/api/budget?project=${project}`);

export const setBudget = (project, period, co2LimitG, energyLimitWh = null) =>
  fetchJSON("/api/budget", {
    method: "POST",
    body: JSON.stringify({
      project,
      period,
      co2_limit_g: co2LimitG,
      energy_limit_wh: energyLimitWh,
    }),
  });

// Optimizer (legacy)
export const runOptimizer = (baselineEnergy, optimizations) =>
  fetchJSON("/run", {
    method: "POST",
    body: JSON.stringify({
      baseline_energy_wh: baselineEnergy,
      optimizations,
    }),
  });

// Enhanced simulator
export const runSimulator = (baselineEnergy, optimizations) =>
  fetchJSON("/api/simulate", {
    method: "POST",
    body: JSON.stringify({
      baseline_energy_wh: baselineEnergy,
      optimizations,
    }),
  });

// Regions
export const getRegions = () => fetchJSON("/api/regions");

// Hourly trends
export const getHourlyTrends = () => fetchJSON("/api/trends/hourly");

// Auth / API Keys
export const createApiKey = (label) =>
  fetchJSON(`/auth/api-keys?label=${encodeURIComponent(label)}`, { method: "POST" });

export const revokeApiKey = (keyId) =>
  fetchJSON(`/auth/api-keys/${keyId}`, { method: "DELETE" });

// Projects
export const getProjects = () => fetchJSON("/api/projects/");
export const createProject = (name) =>
  fetchJSON("/api/projects/", {
    method: "POST",
    body: JSON.stringify({ name }),
  });
export const deleteProject = (name) =>
  fetchJSON(`/api/projects/${encodeURIComponent(name)}`, { method: "DELETE" });
export const updateProjectWebhook = (name, webhookUrl) =>
  fetchJSON(`/api/projects/${encodeURIComponent(name)}/webhook`, {
    method: "PUT",
    body: JSON.stringify({ webhook_url: webhookUrl }),
  });
