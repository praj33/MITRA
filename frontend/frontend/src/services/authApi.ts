const getBaseUrl = () => {
    const url = process.env.REACT_APP_API_URL || process.env.REACT_APP_AUTH_API_URL || 'http://localhost:8000';
    if (url.startsWith('http')) return url;
    return `https://${url}`;
};

const AUTH_BASE_URL = getBaseUrl();

interface AuthUser {
    id: string;
    name: string;
    email: string;
}

interface AuthResponse {
    token: string;
    user: AuthUser;
}

interface MeResponse {
    user: AuthUser;
}

const getToken = (): string | null => localStorage.getItem('authToken');

const authHeaders = (): HeadersInit => ({
    'Content-Type': 'application/json',
    ...(getToken() ? { Authorization: `Bearer ${getToken()}` } : {}),
});

const handleResponse = async <T>(res: Response): Promise<T> => {
    const json = await res.json().catch(() => ({ error: `HTTP ${res.status}` }));
    if (!res.ok) {
        throw new Error(json.error || json.detail || `Request failed (${res.status})`);
    }
    return json as T;
};

export const authApi = {
    /** Create a new account and return token + user */
    async signup(name: string, email: string, password: string): Promise<AuthResponse> {
        const res = await fetch(`${AUTH_BASE_URL}/api/auth/signup`, {
            method: 'POST',
            headers: authHeaders(),
            body: JSON.stringify({ name, email, password }),
        });
        return handleResponse<AuthResponse>(res);
    },

    /** Log in and return token + user */
    async login(email: string, password: string): Promise<AuthResponse> {
        const res = await fetch(`${AUTH_BASE_URL}/api/auth/login`, {
            method: 'POST',
            headers: authHeaders(),
            body: JSON.stringify({ email, password }),
        });
        return handleResponse<AuthResponse>(res);
    },

    /** Fetch current user from the token stored in localStorage */
    async getMe(): Promise<AuthUser | null> {
        const token = getToken();
        if (!token) return null;
        try {
            const res = await fetch(`${AUTH_BASE_URL}/api/auth/me`, {
                method: 'GET',
                headers: authHeaders(),
            });
            const data = await handleResponse<MeResponse>(res);
            return data.user;
        } catch {
            // Token is invalid / expired
            localStorage.removeItem('authToken');
            localStorage.removeItem('user');
            return null;
        }
    },

    /** Inform backend (no-op for stateless JWT), then clear local storage */
    async logout(): Promise<void> {
        const token = getToken();
        if (token) {
            fetch(`${AUTH_BASE_URL}/api/auth/logout`, {
                method: 'POST',
                headers: authHeaders(),
            }).catch(() => { }); // fire-and-forget
        }
        localStorage.removeItem('authToken');
        localStorage.removeItem('user');
    },

    /** Initiate Google OAuth PKCE authorization flow */
    async startOAuth(provider: string = 'google', purpose: string = 'connect'): Promise<{ url: string; state: string }> {
        const res = await fetch(`${AUTH_BASE_URL}/api/oauth/${provider}/start?purpose=${encodeURIComponent(purpose)}`, {
            method: 'GET',
            headers: authHeaders(),
        });
        return handleResponse<{ url: string; state: string }>(res);
    },

    /** Get user's connected accounts metadata (no secrets) */
    async getConnections(): Promise<{ user_id: string; connections: Array<{ provider: string; email: string; status: string; scopes?: string[] }> }> {
        const res = await fetch(`${AUTH_BASE_URL}/api/connections`, {
            method: 'GET',
            headers: authHeaders(),
        });
        return handleResponse<{ user_id: string; connections: Array<{ provider: string; email: string; status: string; scopes?: string[] }> }>(res);
    },

    /** Disconnect a provider account */
    async disconnectAccount(provider: string = 'google'): Promise<{ status: string; message: string }> {
        const res = await fetch(`${AUTH_BASE_URL}/api/connections/${provider}`, {
            method: 'DELETE',
            headers: authHeaders(),
        });
        return handleResponse<{ status: string; message: string }>(res);
    },
};
