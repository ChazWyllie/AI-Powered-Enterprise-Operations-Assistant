import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { sendChatMessage, checkHealth } from '../api/client';

describe('API Client', () => {
  const originalFetch = globalThis.fetch;

  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn());
  });

  afterEach(() => {
    globalThis.fetch = originalFetch;
  });

  describe('sendChatMessage', () => {
    it('sends POST request with correct payload', async () => {
      const mockResponse = {
        answer: 'test',
        plan: [],
        actions_taken: [],
        script: null,
        audit: { trace_id: 't1', mode: 'plan_only' },
      };
      vi.mocked(fetch).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      } as Response);

      const result = await sendChatMessage({ message: 'hello', mode: 'plan_only' });

      expect(fetch).toHaveBeenCalledWith('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: 'hello', mode: 'plan_only' }),
      });
      expect(result).toEqual(mockResponse);
    });

    it('sends execute_safe mode in payload when selected', async () => {
      vi.mocked(fetch).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          answer: 'done',
          plan: [],
          actions_taken: [],
          script: null,
          audit: { trace_id: 't2', mode: 'execute_safe' },
        }),
      } as Response);

      await sendChatMessage({ message: 'run it', mode: 'execute_safe' });

      const call = vi.mocked(fetch).mock.calls[0];
      expect(call).toBeDefined();
      const body = JSON.parse(call![1]!.body as string) as { mode: string };
      expect(body.mode).toBe('execute_safe');
    });

    it('throws ApiError on non-2xx response', async () => {
      vi.mocked(fetch).mockResolvedValueOnce({
        ok: false,
        status: 400,
        json: async () => ({ detail: 'Invalid mode' }),
      } as unknown as Response);

      await expect(
        sendChatMessage({ message: 'bad', mode: 'plan_only' }),
      ).rejects.toEqual({ detail: 'Invalid mode', status: 400 });
    });

    it('handles non-JSON error response', async () => {
      vi.mocked(fetch).mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: async () => { throw new Error('not json'); },
      } as unknown as Response);

      await expect(
        sendChatMessage({ message: 'fail', mode: 'plan_only' }),
      ).rejects.toEqual({ detail: 'An unexpected error occurred', status: 500 });
    });
  });

  describe('checkHealth', () => {
    it('returns true when backend is healthy', async () => {
      vi.mocked(fetch).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ status: 'ok' }),
      } as Response);

      expect(await checkHealth()).toBe(true);
    });

    it('returns false on non-ok response', async () => {
      vi.mocked(fetch).mockResolvedValueOnce({
        ok: false,
      } as Response);

      expect(await checkHealth()).toBe(false);
    });

    it('returns false on network error', async () => {
      vi.mocked(fetch).mockRejectedValueOnce(new Error('Network error'));

      expect(await checkHealth()).toBe(false);
    });

    it('returns false when status is not ok', async () => {
      vi.mocked(fetch).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ status: 'degraded' }),
      } as Response);

      expect(await checkHealth()).toBe(false);
    });
  });
});
