import type { ChatRequest, ChatResponse, ApiError } from '../types';

const API_BASE = import.meta.env.VITE_API_URL ?? '/api';

/**
 * Send a chat request to the backend API.
 *
 * @param request - The chat request payload.
 * @returns The structured chat response.
 * @throws ApiError on non-2xx responses.
 */
export async function sendChatMessage(request: ChatRequest): Promise<ChatResponse> {
  const response = await fetch(`${API_BASE}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    let detail = 'An unexpected error occurred';
    try {
      const body = (await response.json()) as { detail?: string };
      detail = body.detail ?? detail;
    } catch {
      // response body is not JSON
    }
    const error: ApiError = { detail, status: response.status };
    throw error;
  }

  return (await response.json()) as ChatResponse;
}

/**
 * Check backend health.
 *
 * @returns True if the backend is reachable and healthy.
 */
export async function checkHealth(): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE}/health`);
    if (!response.ok) return false;
    const data = (await response.json()) as { status: string };
    return data.status === 'ok';
  } catch {
    return false;
  }
}
