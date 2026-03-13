'use client';

import React, { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react';
import { useRouter } from 'next/navigation';

interface User {
  id: string;
  phone: string;
  full_name: string | null;
  email: string | null;
  balance: number;
  savings: number;
  country: string | null;
  role: string;
  is_verified: boolean;
  created_at: string;
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (phone: string, password: string) => Promise<boolean>;
  register: (data: { phone: string; password: string; full_name?: string; email?: string; country?: string }) => Promise<{ success: boolean; message: string }>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();

  const getAuthHeader = useCallback(() => {
    if (typeof window === 'undefined') return {};
    const token = localStorage.getItem('token');
    return token ? { Authorization: `Bearer ${token}` } : {};
  }, []);

  const fetchUser = useCallback(async () => {
    try {
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
        ...getAuthHeader(),
      };

      const response = await fetch(`${API_URL}/auth/me`, {
        method: 'GET',
        headers: headers,
      });

      if (response.ok) {
        const data = await response.json();
        setUser(data);
        return true;
      } else {
        localStorage.removeItem('token');
        setUser(null);
        return false;
      }
    } catch (error) {
      console.error('Failed to fetch user:', error);
      setUser(null);
      return false;
    }
  }, [getAuthHeader]);

  useEffect(() => {
    const initAuth = async () => {
      const token = localStorage.getItem('token');
      if (token) {
        await fetchUser();
      }
      setIsLoading(false);
    };
    initAuth();
  }, [fetchUser]);

  const login = async (phone: string, password: string): Promise<boolean> => {
    try {
      const response = await fetch(`${API_URL}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ phone, password }),
      });

      if (response.ok) {
        const data = await response.json();
        localStorage.setItem('token', data.access_token);
        setUser(data.user);
        return true;
      }
      return false;
    } catch (error) {
      console.error('Login failed:', error);
      return false;
    }
  };

  const register = async (data: { phone: string; password: string; full_name?: string; email?: string; country?: string }): Promise<{ success: boolean; message: string }> => {
    try {
      const response = await fetch(`${API_URL}/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });

      const result = await response.json();

      if (response.ok) {
        return { success: true, message: 'Compte créé' };
      }
      return { success: false, message: result.detail || 'Erreur lors de l\'inscription' };
    } catch (error) {
      console.error('Registration failed:', error);
      return { success: false, message: 'Erreur réseau' };
    }
  };

  const logout = async () => {
    localStorage.removeItem('token');
    setUser(null);
    router.push('/');
  };

  const refreshUser = useCallback(async () => {
    await fetchUser();
  }, [fetchUser]);

  return (
    <AuthContext.Provider value={{ user, isAuthenticated: !!user, isLoading, login, register, logout, refreshUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}