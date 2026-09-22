import {
  getApiBase,
  getAuthHeaders,
  getAuthToken,
  setAuthToken,
  clearAuthToken,
} from './apiConfig';

interface AuthUser {
  id: string;
  name: string;
  email: string;
  is_guest?: boolean;
}

interface AuthResponse {
  token: string;
  user: AuthUser;
}

interface MeResponse {
  user: AuthUser;
}

const handleResponse = async <T>(res: Response): Promise<T> => {
  const json = await res.json().catch(() => ({ error: `HTTP ${res.status}` }));
  if (!res.ok) {
    throw new Error(json.error || json.detail || json.message || `Request failed (${res.status})`);
  }
  return json as T;
};

export const authApi = {
  /** Create a new account and return token + user */
  async signup(name: string, email: string, password: string): Promise<AuthResponse> {
    const res = await fetch(`${getApiBase()}/api/auth/signup`, {
      method: 'POST',
      headers: getAuthHeaders({ includeAuth: false }),
      body: JSON.stringify({ name, email, password }),
    });
    const data = await handleResponse<AuthResponse>(res);
    if (data.token) {
      setAuthToken(data.token);
    }
    return data;
  },

  /** Log in and return token + user */
  async login(email: string, password: string): Promise<AuthResponse> {
    const res = await fetch(`${getApiBase()}/api/auth/login`, {
      method: 'POST',
      headers: getAuthHeaders({ includeAuth: false }),
      body: JSON.stringify({ email, password }),
    });
    const data = await handleResponse<AuthResponse>(res);
    if (data.token) {
      setAuthToken(data.token);
    }
    return data;
  },

  /** Initiate temporary guest session and return guest token + user */
  async guestLogin(): Promise<AuthResponse> {
    const res = await fetch(`${getApiBase()}/api/auth/guest`, {
      method: 'POST',
      headers: getAuthHeaders({ includeAuth: false }),
    });
    const data = await handleResponse<AuthResponse & { access_token?: string }>(res);
    const token = data.token || data.access_token || '';
    if (token) {
      setAuthToken(token);
    }
    return {
      token,
      user: data.user,
    };
  },

  /** Fetch current user from the token stored in localStorage */
  async getMe(): Promise<AuthUser | null> {
    const token = getAuthToken();
    if (!token) return null;
    try {
      const res = await fetch(`${getApiBase()}/api/auth/me`, {
        method: 'GET',
        headers: getAuthHeaders(),
      });
      if (res.status === 401 || res.status === 403) {
        clearAuthToken();
        localStorage.removeItem('user');
        return null;
      }
      const data = await handleResponse<MeResponse>(res);
      return data.user;
    } catch {
      // Token is invalid / expired or network issue
      clearAuthToken();
      localStorage.removeItem('user');
      return null;
    }
  },

  /** Inform backend (stateless JWT revocation / audit log), then clear local storage */
  async logout(): Promise<void> {
    const token = getAuthToken();
    if (token) {
      fetch(`${getApiBase()}/api/auth/logout`, {
        method: 'POST',
        headers: getAuthHeaders(),
      }).catch(() => {}); // fire-and-forget
    }
    clearAuthToken();
    localStorage.removeItem('user');
  },

  /** Initiate OAuth PKCE authorization flow */
  async startOAuth(provider: string = 'google', purpose: string = 'connect'): Promise<{ url: string; auth_url?: string; state: string }> {
    const res = await fetch(`${getApiBase()}/api/oauth/${provider}/start?purpose=${encodeURIComponent(purpose)}`, {
      method: 'GET',
      headers: getAuthHeaders(),
    });
    return handleResponse<{ url: string; auth_url?: string; state: string }>(res);
  },

  /** Get user's connected accounts metadata (no secrets) */
  async getConnections(): Promise<{ user_id: string; connections: Array<{ provider: string; email: string; status: string; scopes?: string[] }> }> {
    const res = await fetch(`${getApiBase()}/api/connections`, {
      method: 'GET',
      headers: getAuthHeaders(),
    });
    return handleResponse<{ user_id: string; connections: Array<{ provider: string; email: string; status: string; scopes?: string[] }> }>(res);
  },

  /** Disconnect a provider account */
  async disconnectAccount(provider: string = 'google'): Promise<{ status: string; message: string }> {
    const res = await fetch(`${getApiBase()}/api/connections/${provider}`, {
      method: 'DELETE',
      headers: getAuthHeaders(),
    });
    return handleResponse<{ status: string; message: string }>(res);
  },
};
export type { AuthUser, AuthResponse, MeResponse };
