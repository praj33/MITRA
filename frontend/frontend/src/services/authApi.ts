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
};
