import React, { createContext, useContext, useState, useEffect } from 'react';
import { authApi } from '../services/authApi';
import { getAuthToken, setAuthToken, clearAuthToken } from '../services/apiConfig';
import { useCompanionStore } from '../store/companion.store';

interface User {
  id: string;
  email: string;
  name: string;
  is_guest?: boolean;
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isGuest: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  signup: (name: string, email: string, password: string) => Promise<void>;
  loginAsGuest: () => Promise<void>;
  logout: () => void;
  error: string | null;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isGuest, setIsGuest] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Helper to trigger guest login fallback
  const startGuestFallback = async () => {
    try {
      const { token: guestToken, user: guestUser } = await authApi.guestLogin();
      setUser(guestUser);
      setIsGuest(true);
      useCompanionStore.getState().setAuth(guestUser, guestToken, true);
    } catch {
      setUser(null);
      setIsGuest(false);
      clearAuthToken();
    }
  };

  // On mount: restore session from stored canonical JWT or initiate Guest session
  useEffect(() => {
    const restoreSession = async () => {
      const token = getAuthToken();
      if (!token) {
        await startGuestFallback();
        setIsLoading(false);
        return;
      }

      try {
        const me = await authApi.getMe();
        if (me) {
          setUser(me);
          const guestFlag = Boolean(me.is_guest);
          setIsGuest(guestFlag);
          // Sync with companion Zustand store
          useCompanionStore.getState().setAuth(me, token, guestFlag);
        } else {
          await startGuestFallback();
        }
      } catch {
        // Token invalid or backend unreachable – start guest session
        await startGuestFallback();
      } finally {
        setIsLoading(false);
      }
    };
    restoreSession();
  }, []);

  const loginAsGuest = async () => {
    setError(null);
    setIsLoading(true);
    try {
      const { token: guestToken, user: guestUser } = await authApi.guestLogin();
      setUser(guestUser);
      setIsGuest(true);
      useCompanionStore.getState().setAuth(guestUser, guestToken, true);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Guest login failed';
      setError(message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const login = async (email: string, password: string) => {
    setError(null);
    setIsLoading(true);
    try {
      const { token, user: userData } = await authApi.login(email, password);
      setAuthToken(token);
      setUser(userData);
      setIsGuest(false);
      // Sync with companion Zustand store
      useCompanionStore.getState().setAuth(userData, token, false);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Login failed';
      setError(message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const signup = async (name: string, email: string, password: string) => {
    setError(null);
    setIsLoading(true);
    try {
      const { token, user: userData } = await authApi.signup(name, email, password);
      setAuthToken(token);
      setUser(userData);
      setIsGuest(false);
      // Sync with companion Zustand store
      useCompanionStore.getState().setAuth(userData, token, false);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Signup failed';
      setError(message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    authApi.logout();
    clearAuthToken();
    setUser(null);
    setIsGuest(false);
    setError(null);
    useCompanionStore.getState().logoutUser();
    // After logging out of account, initiate guest session
    authApi.guestLogin().then(({ token: guestToken, user: guestUser }) => {
      setUser(guestUser);
      setIsGuest(true);
      useCompanionStore.getState().setAuth(guestUser, guestToken, true);
    }).catch(() => {});
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isGuest,
        isLoading,
        login,
        signup,
        loginAsGuest,
        logout,
        error,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
