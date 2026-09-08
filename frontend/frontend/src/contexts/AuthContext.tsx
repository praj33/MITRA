import React, { createContext, useContext, useState, useEffect } from 'react';
import { authApi } from '../services/authApi';
import { getAuthToken, setAuthToken, clearAuthToken } from '../services/apiConfig';
import { useCompanionStore } from '../store/companion.store';

interface User {
  id: string;
  email: string;
  name: string;
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  signup: (name: string, email: string, password: string) => Promise<void>;
  logout: () => void;
  error: string | null;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // On mount: restore session from stored canonical JWT
  useEffect(() => {
    const restoreSession = async () => {
      const token = getAuthToken();
      if (!token) {
        setIsLoading(false);
        return;
      }

      try {
        const me = await authApi.getMe();
        if (me) {
          setUser(me);
          // Sync with companion Zustand store
          useCompanionStore.getState().setAuth(me, token);
        } else {
          setUser(null);
          clearAuthToken();
        }
      } catch {
        // Token invalid or backend unreachable – start unauthenticated
        setUser(null);
        clearAuthToken();
      } finally {
        setIsLoading(false);
      }
    };
    restoreSession();
  }, []);

  const login = async (email: string, password: string) => {
    setError(null);
    setIsLoading(true);
    try {
      const { token, user: userData } = await authApi.login(email, password);
      setAuthToken(token);
      setUser(userData);
      // Sync with companion Zustand store
      useCompanionStore.getState().setAuth(userData, token);
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
      // Sync with companion Zustand store
      useCompanionStore.getState().setAuth(userData, token);
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
    setError(null);
    useCompanionStore.getState().logoutUser();
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isLoading,
        login,
        signup,
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
