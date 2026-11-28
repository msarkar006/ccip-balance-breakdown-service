/**
 * The single API client. Base is `VITE_API_URL ?? '/api/v1'`; call paths are relative to it
 * (`/accounts`). Only `get` and `post` exist: the prototype has no other method.
 */
export const API_BASE: string = import.meta.env.VITE_API_URL ?? '/api/v1';

export class ApiError extends Error {
  readonly status: number;
  readonly detail: string;
  readonly retryAfter?: number;

  constructor(status: number, detail: string, retryAfter?: number) {
    super(detail);
    this.name = 'ApiError';
    this.status = status;
    this.detail = detail;
    this.retryAfter = retryAfter;
  }
}

export type QueryParams = Record<string, string | number | boolean | null | undefined>;

let accessToken: string | null = null;
let unauthorizedHandler: (() => void) | null = null;

export function setAccessToken(token: string | null): void {
  accessToken = token;
}

export function getAccessToken(): string | null {
  return accessToken;
}

/** Registers the callback run on any 401 from a request that carried a token. */
export function onUnauthorized(handler: (() => void) | null): void {
  unauthorizedHandler = handler;
}

export function newCorrelationId(): string {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID();
  }
  return `web-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 10)}`;
}

export function withQuery(path: string, params?: QueryParams): string {
  if (!params) return path;
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== null && value !== undefined) search.set(key, String(value));
  }
  const text = search.toString();
  return text ? `${path}?${text}` : path;
}

function safeDetail(body: unknown, status: number): string {
  if (typeof body === 'object' && body !== null && 'detail' in body) {
    const detail = (body as { detail: unknown }).detail;
    if (typeof detail === 'string' && detail.length > 0) return detail;
  }
  return status === 422 ? 'The request was not valid' : 'Something went wrong. Try again later.';
}

async function request<T>(
  method: 'GET' | 'POST',
  path: string,
  body?: unknown,
  extraHeaders?: Record<string, string>,
): Promise<T> {
  const headers: Record<string, string> = {
    ...extraHeaders,
    Accept: 'application/json',
    'X-Correlation-ID': newCorrelationId(),
  };
  if (accessToken) headers.Authorization = `Bearer ${accessToken}`;
  if (body !== undefined) headers['Content-Type'] = 'application/json';

  let response: Response;
  try {
    response = await fetch(`${API_BASE}${path}`, {
      method,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
    });
  } catch {
    throw new ApiError(0, 'The service could not be reached. Try again later.');
  }

  if (response.ok) {
    if (response.status === 204) return undefined as T;
    return (await response.json()) as T;
  }

  let payload: unknown = null;
  try {
    payload = await response.json();
  } catch {
    payload = null;
  }
  const retryHeader = response.headers.get('Retry-After');
  const retryAfter = retryHeader !== null && retryHeader !== '' && !Number.isNaN(Number(retryHeader)) ? Number(retryHeader) : undefined;
  const error = new ApiError(response.status, safeDetail(payload, response.status), retryAfter);
  if (response.status === 401 && headers.Authorization && unauthorizedHandler) unauthorizedHandler();
  throw error;
}

export function get<T>(path: string, params?: QueryParams): Promise<T> {
  return request<T>('GET', withQuery(path, params));
}

export function post<T>(path: string, body?: unknown, headers?: Record<string, string>): Promise<T> {
  return request<T>('POST', path, body, headers);
}
