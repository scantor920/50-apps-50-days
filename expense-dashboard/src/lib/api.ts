import { useAuth } from './auth';

const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:3001';

export interface ApiErrorContext {
  url: string;
  method: string;
  status: number;
  statusText: string;
  requestId: string | null;
  responseBody?: unknown;
}

export class ApiError extends Error {
  context: ApiErrorContext;

  constructor(message: string, context: ApiErrorContext) {
    super(message);
    this.name = 'ApiError';
    this.context = context;
  }
}

function joinUrl(path: string): string {
  const base = API_BASE.endsWith('/') ? API_BASE.slice(0, -1) : API_BASE;
  return `${base}${path.startsWith('/') ? path : `/${path}`}`;
}

async function parseResponseBody(response: Response): Promise<unknown> {
  const contentType = response.headers.get('content-type') ?? '';
  if (contentType.includes('application/json')) {
    return response.json();
  }
  return response.text();
}

export async function apiGet<T>(path: string, token: string | null): Promise<T> {
  const url = joinUrl(path);
  const headers = new Headers({ Accept: 'application/json' });

  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  const response = await fetch(url, { method: 'GET', headers });
  const requestId = response.headers.get('x-request-id');

  if (!response.ok) {
    const responseBody = await parseResponseBody(response);
    throw new ApiError('Request failed', {
      url,
      method: 'GET',
      status: response.status,
      statusText: response.statusText,
      requestId,
      responseBody,
    });
  }

  return (await response.json()) as T;
}

export function useApiGet() {
  const { token } = useAuth();
  return async function get<T>(path: string): Promise<T> {
    return apiGet<T>(path, token);
  };
}
