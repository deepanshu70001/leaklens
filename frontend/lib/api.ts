/**
 * LeakLens API client — fetch wrapper with auth and error handling.
 */
import {
  AuthResponse,
  DashboardSummary,
  GrowthSummary,
  IngestResponse,
  NegotiateResponse,
  Subscription,
  SubscriptionListResponse,
  ActionResponse,
} from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// ── Token Management ────────────────────────────────────────────────
let authToken: string | null = null;

export function setToken(token: string) {
  authToken = token;
  if (typeof window !== "undefined") {
    localStorage.setItem("leaklens_token", token);
  }
}

export function getToken(): string | null {
  if (authToken) return authToken;
  if (typeof window !== "undefined") {
    authToken = localStorage.getItem("leaklens_token");
  }
  return authToken;
}

export function clearToken() {
  authToken = null;
  if (typeof window !== "undefined") {
    localStorage.removeItem("leaklens_token");
  }
}

// ── Base Fetch ──────────────────────────────────────────────────────
async function apiFetch<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Request failed" }));
    throw new Error(error.detail || `API Error: ${response.status}`);
  }

  return response.json();
}

async function apiUpload<T>(
  path: string,
  file: File
): Promise<T> {
  const token = getToken();
  const formData = new FormData();
  formData.append("file", file);

  const headers: Record<string, string> = {};
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers,
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Upload failed" }));
    throw new Error(error.detail || `API Error: ${response.status}`);
  }

  return response.json();
}

// ── Auth Endpoints ──────────────────────────────────────────────────
export async function signup(email: string, password: string): Promise<AuthResponse> {
  const data = await apiFetch<AuthResponse>("/api/auth/signup", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
  setToken(data.access_token);
  return data;
}

export async function login(email: string, password: string): Promise<AuthResponse> {
  const data = await apiFetch<AuthResponse>("/api/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
  setToken(data.access_token);
  return data;
}

// ── Ingest Endpoints ────────────────────────────────────────────────
export async function ingestSMS(rawText: string): Promise<IngestResponse> {
  return apiFetch<IngestResponse>("/api/ingest/sms", {
    method: "POST",
    body: JSON.stringify({ raw_text: rawText }),
  });
}

export async function ingestStatement(file: File): Promise<IngestResponse> {
  return apiUpload<IngestResponse>("/api/ingest/statement", file);
}

export async function ingestDemo(datasetId: string = "sample_sms_1"): Promise<IngestResponse> {
  return apiFetch<IngestResponse>("/api/ingest/demo", {
    method: "POST",
    body: JSON.stringify({ dataset_id: datasetId }),
  });
}

// ── Subscription Endpoints ──────────────────────────────────────────
export async function getSubscriptions(): Promise<SubscriptionListResponse> {
  return apiFetch<SubscriptionListResponse>("/api/subscriptions");
}

export async function getSubscriptionDetail(id: string): Promise<Subscription> {
  return apiFetch<Subscription>(`/api/subscriptions/${id}`);
}

// ── Action Endpoints ────────────────────────────────────────────────
export async function takeAction(
  subscriptionId: string,
  action: string,
  redirectedToGrowth: boolean = true
): Promise<ActionResponse> {
  return apiFetch<ActionResponse>(`/api/subscriptions/${subscriptionId}/action`, {
    method: "POST",
    body: JSON.stringify({
      action,
      redirected_to_growth: redirectedToGrowth,
    }),
  });
}

export async function ghostCancelSubscription(subscriptionId: string): Promise<{status: string, message: string, draft: string}> {
  return apiFetch<{status: string, message: string, draft: string}>(`/api/subscriptions/${subscriptionId}/ghost-cancel`, {
    method: "POST",
  });
}

// ── Dashboard Endpoint ──────────────────────────────────────────────
export async function getDashboardSummary(): Promise<DashboardSummary> {
  return apiFetch<DashboardSummary>("/api/dashboard/summary");
}

// ── Growth Endpoint ─────────────────────────────────────────────────
export async function getGrowthSummary(): Promise<GrowthSummary> {
  return apiFetch<GrowthSummary>("/api/growth/summary");
}

// ── Negotiate Endpoint ──────────────────────────────────────────────
export async function generateNegotiationScript(subscriptionId: string): Promise<NegotiateResponse> {
  return apiFetch<NegotiateResponse>(`/api/negotiate/${subscriptionId}`, {
    method: "POST",
  });
}
