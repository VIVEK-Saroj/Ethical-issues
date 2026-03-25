import { createContext, useContext, useState, useCallback, useEffect, ReactNode } from 'react';
import api from '../api/client';
import type { User, TokenResponse } from '../types';

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (username: string, password: string) => Promise<void>;
  register: (username: string, email: string, password: string, role?: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(() => {
    const saved = localStorage.getItem('bigmart_user');
    return saved ? JSON.parse(saved) : null;
  });
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('bigmart_token'));
  const [isLoading, setIsLoading] = useState(false);

  const isAuthenticated = !!token && !!user;

  const login = useCallback(async (username: string, password: string) => {
    setIsLoading(true);
    try {
      const { data } = await api.post<TokenResponse>('/auth/login', { username, password });
      localStorage.setItem('bigmart_token', data.access_token);
      localStorage.setItem('bigmart_user', JSON.stringify(data.user));
      setToken(data.access_token);
      setUser(data.user);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const register = useCallback(async (username: string, email: string, password: string, role = 'manager') => {
    setIsLoading(true);
    try {
      const { data } = await api.post<TokenResponse>('/auth/register', { username, email, password, role });
      localStorage.setItem('bigmart_token', data.access_token);
      localStorage.setItem('bigmart_user', JSON.stringify(data.user));
      setToken(data.access_token);
      setUser(data.user);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem('bigmart_token');
    localStorage.removeItem('bigmart_user');
    setToken(null);
    setUser(null);
  }, []);

  // Verify token on mount
  useEffect(() => {
    if (token) {
      api.get('/auth/me').catch(() => logout());
    }
  }, [token, logout]);

  return (
    <AuthContext.Provider value={{ user, token, isAuthenticated, isLoading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
