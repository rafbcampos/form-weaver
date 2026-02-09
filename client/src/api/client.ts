import type { InterviewSchema } from "../types/schema";
import type { StartResponse, SubmitResponse, StatusResponse } from "../types/api";

const BASE_URL = "/api/interview";

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });

  if (!res.ok) {
    const body = await res.text();
    throw new Error(`API error ${res.status}: ${body}`);
  }

  return res.json() as Promise<T>;
}

export async function startInterview(
  schema: InterviewSchema,
  initialData: Record<string, unknown> = {},
): Promise<StartResponse> {
  return request<StartResponse>(`${BASE_URL}/start`, {
    method: "POST",
    body: JSON.stringify({ schema: schema, initial_data: initialData }),
  });
}

export async function submitForm(
  sessionId: string,
  data: Record<string, unknown>,
): Promise<SubmitResponse> {
  return request<SubmitResponse>(`${BASE_URL}/${sessionId}/submit`, {
    method: "POST",
    body: JSON.stringify({ type: "form", data }),
  });
}

export async function sendMessage(sessionId: string, text: string): Promise<SubmitResponse> {
  return request<SubmitResponse>(`${BASE_URL}/${sessionId}/submit`, {
    method: "POST",
    body: JSON.stringify({ type: "message", text }),
  });
}

export async function getStatus(sessionId: string): Promise<StatusResponse> {
  return request<StatusResponse>(`${BASE_URL}/${sessionId}/status`);
}
