/**
 * apiConfig.ts — Centralized API Base URL & Authentication Config for MITRA
 *
 * Normalizes API endpoints to avoid double `/api/api` paths,
 * manages the canonical JWT key (`mitra_auth_token`) with backward-compatible fallbacks,
 * and provides unified headers for authenticated/unauthenticated API calls.
 */

export const PRIMARY_AUTH_TOKEN_KEY = 'mitra_auth_token';
export const LEGACY_AUTH_TOKEN_KEY = 'authToken';

/**
 * Normalizes an API base URL:
 * - Strips any trailing slashes
 * - Strips any trailing `/api` (case-insensitive)
 *
 * Example:
 *   "https://mitra.blackholeinfiverse.com/api" -> "https://mitra.blackholeinfiverse.com"
 *   "https://mitra.blackholeinfiverse.com/api/" -> "https://mitra.blackholeinfiverse.com"
 *   "http://localhost:8000" -> "http://localhost:8000"
 */
export const normalizeApiBase = (rawUrl?: string): string => {
  if (!rawUrl || typeof rawUrl !== 'string') {
    if (typeof window !== 'undefined' && window.location) {
      const hostname = window.location.hostname;
      if (hostname !== 'localhost' && hostname !== '127.0.0.1') {
        return `${window.location.protocol}//${window.location.host}`;
      }
    }
    return 'http://localhost:8000';
  }

  let base = rawUrl.trim();
  // Ensure protocol if missing and not relative
  if (!base.startsWith('http://') && !base.startsWith('https://') && !base.startsWith('/')) {
    base = `https://${base}`;
  }

  // Strip trailing slashes
  base = base.replace(/\/+$/, '');

  // Strip trailing /api
  base = base.replace(/\/api$/i, '');

  // Strip trailing slashes again just in case
  base = base.replace(/\/+$/, '');

  return base;
};

/**
 * Returns the single normalized base URL for the backend API.
 */
export const getApiBase = (): string => {
  const envUrl =
    process.env.REACT_APP_API_URL ||
    process.env.REACT_APP_API_BASE_URL ||
    process.env.REACT_APP_AUTH_API_URL;

  return normalizeApiBase(envUrl);
};

/**
 * Retrieves the user's JWT token.
 * Reads canonical `mitra_auth_token` first, falling back to `authToken`.
 */
export const getAuthToken = (): string | null => {
  if (typeof window === 'undefined' || !window.localStorage) return null;
  try {
    const canonical = localStorage.getItem(PRIMARY_AUTH_TOKEN_KEY);
    if (canonical && canonical.trim()) return canonical.trim();

    const legacy = localStorage.getItem(LEGACY_AUTH_TOKEN_KEY);
    if (legacy && legacy.trim()) return legacy.trim();
  } catch (err) {
    console.warn('Failed reading auth token from storage:', err);
  }
  return null;
};

/**
 * Stores the user's JWT token under the canonical key and legacy key for interop.
 */
export const setAuthToken = (token: string): void => {
  if (typeof window === 'undefined' || !window.localStorage) return;
  try {
    if (token) {
      localStorage.setItem(PRIMARY_AUTH_TOKEN_KEY, token);
      localStorage.setItem(LEGACY_AUTH_TOKEN_KEY, token);
    } else {
      clearAuthToken();
    }
  } catch (err) {
    console.warn('Failed saving auth token to storage:', err);
  }
};

/**
 * Clears authentication tokens from storage.
 */
export const clearAuthToken = (): void => {
  if (typeof window === 'undefined' || !window.localStorage) return;
  try {
    localStorage.removeItem(PRIMARY_AUTH_TOKEN_KEY);
    localStorage.removeItem(LEGACY_AUTH_TOKEN_KEY);
  } catch (err) {
    console.warn('Failed clearing auth token from storage:', err);
  }
};

/**
 * Returns the configured application API key, if any.
 */
export const getApiKey = (): string => {
  return (process.env.REACT_APP_API_KEY || '').trim();
};

export interface AuthHeaderOptions {
  includeAuth?: boolean;
  contentType?: string | null;
  extraHeaders?: Record<string, string>;
}

/**
 * Generates unified headers for API requests.
 * Includes `Authorization: Bearer <token>` when available and `X-API-Key` if configured.
 */
export const getAuthHeaders = (options: AuthHeaderOptions = {}): Record<string, string> => {
  const {
    includeAuth = true,
    contentType = 'application/json',
    extraHeaders = {},
  } = options;

  const headers: Record<string, string> = {};

  if (contentType !== null && contentType !== undefined) {
    headers['Content-Type'] = contentType;
  }

  const apiKey = getApiKey();
  if (apiKey) {
    headers['X-API-Key'] = apiKey;
  }

  if (includeAuth) {
    const token = getAuthToken();
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
  }

  if (extraHeaders) {
    Object.assign(headers, extraHeaders);
  }

  return headers;
};

/**
 * Safe error description helper that prevents leaking internal tokens or stack traces
 * while providing actionable diagnostic information.
 */
export const formatApiError = (status: number, data?: any): string => {
  if (status === 401) {
    return 'Unauthorized: Your session may have expired. Please sign in again.';
  }
  if (status === 403) {
    return 'Forbidden: You do not have permission to access this resource.';
  }
  if (status === 404) {
    return 'Resource not found (404).';
  }
  if (status === 429) {
    return 'Too many requests. Please slow down and try again in a moment.';
  }
  if (status >= 500) {
    return 'Backend service error. Please try again later.';
  }
  if (data && typeof data === 'object') {
    return data.detail || data.error || data.message || `Request failed with status ${status}`;
  }
  return `Request failed (${status})`;
};
