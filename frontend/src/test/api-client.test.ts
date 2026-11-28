import { afterEach, describe, expect, it, vi } from 'vitest';
import { ApiError, API_BASE, get, onUnauthorized, post, setAccessToken } from '../lib/api-client';
import { jsonResponse } from './render';

afterEach(() => vi.restoreAllMocks());

describe('api-client', () => {
  it('uses the /api/v1 base with relative paths, bearer token and correlation id', async () => {
    const spy = vi.spyOn(globalThis, 'fetch').mockResolvedValue(jsonResponse({ items: [] }));
    setAccessToken('tok');
    await get('/accounts', { limit: 5, offset: undefined });
    const [url, init] = spy.mock.calls[0];
    expect(API_BASE).toBe('/api/v1');
    expect(url).toBe('/api/v1/accounts?limit=5');
    const headers = (init as RequestInit).headers as Record<string, string>;
    expect(headers.Authorization).toBe('Bearer tok');
    expect(headers['X-Correlation-ID']).toBeTruthy();
  });

  it('posts JSON and returns undefined for 204', async () => {
    const spy = vi.spyOn(globalThis, 'fetch').mockResolvedValue(jsonResponse(null, 204));
    await expect(post('/auth/logout')).resolves.toBeUndefined();
    expect((spy.mock.calls[0][1] as RequestInit).method).toBe('POST');
  });

  it('throws ApiError with detail and Retry-After', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      jsonResponse({ detail: 'Too many sign-in attempts' }, 429, { 'Retry-After': '30' }),
    );
    const error = await post('/auth/login', {}).catch((e: unknown) => e);
    expect(error).toBeInstanceOf(ApiError);
    expect((error as ApiError).status).toBe(429);
    expect((error as ApiError).detail).toBe('Too many sign-in attempts');
    expect((error as ApiError).retryAfter).toBe(30);
  });

  it('calls onUnauthorized for a 401 on an authenticated request only', async () => {
    const handler = vi.fn();
    onUnauthorized(handler);
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(jsonResponse({ detail: 'Authentication required' }, 401));
    await post('/auth/login', {}).catch(() => undefined);
    expect(handler).not.toHaveBeenCalled();
    setAccessToken('tok');
    await get('/auth/session').catch(() => undefined);
    expect(handler).toHaveBeenCalledTimes(1);
  });
});
