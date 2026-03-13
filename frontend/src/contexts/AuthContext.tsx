'use client';

import React, { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react';

// Configuration de l'URL de l'API
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

// User interface
export interface User {
  id: string;
  phone: string;
  email: string | null;
  full_name: string | null;
  country: string | null;
  balance: number;
  savings: number;
  is_verified: boolean;
  is_active?: boolean;
  avatar_url?: string | null;
  created_at: string;
  role?: string;
}

// Auth state interface
interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}

// Auth context interface
interface AuthContextType extends AuthState {
  login: (phone: string, password: string) => Promise<boolean>;
  register: (data: {
    phone: string;
    password: string;
    full_name?: string;
    email?: string;
    country?: string;
    pin?: string;
  }) => Promise<{ success: boolean; message: string }>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
  clearError: () => void;
}

// Create context
const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Helper to get auth header (FIXED: Explicit return type for TypeScript)
const getAuthHeader = (): Record<string, string> => {
  const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
  return token ? { 'Authorization': `Bearer ${token}` } : {};
};

// Provider component
export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AuthState>({
    user: null,
    isAuthenticated: false,
    isLoading: true,
    error: null,
  });

  // Check if user is authenticated on mount
  useEffect(() => {
    const checkAuth = async () => {
      try {
        const token = localStorage.getItem('access_token');
        if (!token) {
          setState({ user: null, isAuthenticated: false, isLoading: false, error: null });
          return;
        }

        // FIX: Explicitly type headers to satisfy TypeScript strict mode
        const headers: Record<string, string> = {
          'Content-Type': 'application/json',
          ...getAuthHeader(),
        };

        const response = await fetch(`${API_URL}/auth/me`, {
          headers: headers,
        });

        if (response.ok) {
          const data = await response.json();
          if (data.success && data.data?.user) {
            setState({
              user: data.data.user,
              isAuthenticated: true,
              isLoading: false,
              error: null,
            });
            return;
          }
        }
        
        // If token invalid, clear it
        localStorage.removeItem('access_token');
        setState({
          user: null,
          isAuthenticated: false,
          isLoading: false,
          error: null,
        });
      } catch (error) {
        localStorage.removeItem('access_token');
        setState({
          user: null,
          isAuthenticated: false,
          isLoading: false,
          error: null,
        });
      }
    };

    checkAuth();
  }, []);

  // Login function
  const login = useCallback(async (phone: string, password: string): Promise<boolean> => {
    setState(prev => ({ ...prev, isLoading: true, error: null }));

    try {
      const response = await fetch(`${API_URL}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ phone, password }),
      });

      const data = await response.json();

      if (data.success && data.data?.user) {
        // IMPORTANT: Sauvegarder le token pour les futures requêtes
        if (data.data.access_token) {
          localStorage.setItem('access_token', data.data.access_token);
        }

        setState({
          user: data.data.user,
          isAuthenticated: true,
          isLoading: false,
          error: null,
        });
        return true;
      }

      setState(prev => ({
        ...prev,
        isLoading: false,
        error: data.message || 'Échec de la connexion',
      }));
      return false;
    } catch (error) {
      setState(prev => ({
        ...prev,
        isLoading: false,
        error: 'Une erreur est survenue',
      }));
      return false;
    }
  }, []);

  // Register function
  const register = useCallback(async (data: {
    phone: string;
    password: string;
    full_name?: string;
    email?: string;
    country?: string;
    pin?: string;
  }): Promise<{ success: boolean; message: string }> => {
    setState(prev => ({ ...prev, isLoading: true, error: null }));

    try {
      const response = await fetch(`${API_URL}/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });

      const result = await response.json();

      if (result.success && result.data?.user) {
        // IMPORTANT: Sauvegarder le token
        if (result.data.access_token) {
          localStorage.setItem('access_token', result.data.access_token);
        }

        setState({
          user: result.data.user,
          isAuthenticated: true,
          isLoading: false,
          error: null,
        });
        return {
          success: true,
          message: result.message || 'Compte créé avec succès',
        };
      }

      setState(prev => ({ ...prev, isLoading: false }));
      return {
        success: false,
        message: result.message || 'Échec de l\'inscription',
      };
    } catch (error) {
      setState(prev => ({ ...prev, isLoading: false }));
      return {
        success: false,
        message: 'Une erreur est survenue',
      };
    }
  }, []);

  // Logout function
  const logout = useCallback(async () => {
    try {
      // FIX: Explicitly type headers
      const headers: Record<string, string> = {
        ...getAuthHeader(),
      };
      
      await fetch(`${API_URL}/auth/logout`, { 
        method: 'POST',
        headers: headers,
      });
    } catch (error) {
      // Silent fail
    }
    // Supprimer le token local
    localStorage.removeItem('access_token');
    setState({
      user: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
    });
  }, []);

  // Refresh user data
  const refreshUser = useCallback(async () => {
    if (!state.isAuthenticated) return;

    try {
      // FIX: Explicitly type headers
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
        ...getAuthHeader(),
      };

      const response = await fetch(`${API_URL}/auth/me`, {
        headers: headers,
      });
      
      if (response.ok) {
        const data = await response.json();
        if (data.success && data.data?.user) {
          setState(prev => ({
            ...prev,
            user: data.data.user,
          }));
        }
      }
    } catch (error) {
      // Silent fail
    }
  }, [state.isAuthenticated]);

  // Clear error
  const clearError = useCallback(() => {
    setState(prev => ({ ...prev, error: null }));
  }, []);

  const value: AuthContextType = {
    ...state,
    login,
    register,
    logout,
    refreshUser,
    clearError,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

// Hook to use auth context
export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}