/**
 * Centralized API client with authentication and error handling.
 */

const API_BASE = import.meta.env.VITE_API_URL ?? '/api';

export class ApiError extends Error {
  constructor(
    public status: number,
    public detail: string,
    public correlationId?: string
  ) {
    super(detail);
    this.name = 'ApiError';
  }
}

function getAuthToken(): string | null {
  return sessionStorage.getItem('access_token');
}

function setAuthToken(token: string): void {
  sessionStorage.setItem('access_token', token);
}

function clearAuthToken(): void {
  sessionStorage.removeItem('access_token');
}

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getAuthToken();
  const headers = new Headers(options.headers);
  
  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }
  
  if (options.body && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });

  const correlationId = response.headers.get('X-Correlation-ID') || undefined;

  if (response.status === 401) {
    clearAuthToken();
    // Only redirect to login if we're not already there
    if (window.location.pathname !== '/login') {
      window.location.href = '/login';
    }
    throw new ApiError(401, 'Unauthorized', correlationId);
  }

  if (!response.ok) {
    let detail = 'Request failed';
    try {
      const errorData = await response.json();
      detail = errorData.detail || detail;
    } catch {
      detail = await response.text() || detail;
    }
    throw new ApiError(response.status, detail, correlationId);
  }

  if (response.status === 204) {
    return null as T;
  }

  return response.json() as Promise<T>;
}

export const apiClient = {
  get: <T>(path: string) => request<T>(path, { method: 'GET' }),
  post: <T>(path: string, body?: unknown, headers?: HeadersInit) =>
    request<T>(path, {
      method: 'POST',
      body: body ? JSON.stringify(body) : undefined,
      headers,
    }),
  put: <T>(path: string, body?: unknown) =>
    request<T>(path, {
      method: 'PUT',
      body: body ? JSON.stringify(body) : undefined,
    }),
  patch: <T>(path: string, body?: unknown) =>
    request<T>(path, {
      method: 'PATCH',
      body: body ? JSON.stringify(body) : undefined,
    }),
  delete: <T>(path: string) => request<T>(path, { method: 'DELETE' }),
  setAuthToken,
  clearAuthToken,
};
