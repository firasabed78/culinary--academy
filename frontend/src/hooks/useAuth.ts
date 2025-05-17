// frontend/src/hooks/useAuth.ts
import { useState, useEffect, useCallback } from 'react';
import authApi, { User } from '../api/auth';

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}

export function useAuth() {
  const [state, setState] = useState<AuthState>({
    user: null,
    isAuthenticated: false,
    isLoading: true,
    error: null,
  });
  
  const login = useCallback(async (email: string, password: string) => {
    setState(prev => ({ ...prev, isLoading: true, error: null }));
    try {
      const response = await authApi.login({ username: email, password });
      localStorage.setItem('token', response.access_token);
      
      // Get user details
      const user = await authApi.getCurrentUser();
      setState({
        user,
        isAuthenticated: true,
        isLoading: false,
        error: null,
      });
      return true;
    } catch (error) {
      setState(prev => ({ 
        ...prev, 
        isLoading: false, 
        error: error.response?.data?.detail || 'Login failed',
      }));
      return false;
    }
  }, []);
  
  const logout = useCallback(() => {
    localStorage.removeItem('token');
    setState({
      user: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
    });
  }, []);
  
  const checkAuth = useCallback(async () => {
    setState(prev => ({ ...prev, isLoading: true }));
    const token = localStorage.getItem('token');
    
    if (!token) {
      setState({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        error: null,
      });
      return;
    }
    
    try {
      const user = await authApi.getCurrentUser();
      setState({
        user,
        isAuthenticated: true,
        isLoading: false,
        error: null,
      });
    } catch (error) {
      localStorage.removeItem('token');
      setState({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        error: null,
      });
    }
  }, []);
  
  useEffect(() => {
    checkAuth();
  }, [checkAuth]);
  
  return {
    user: state.user,
    isAuthenticated: state.isAuthenticated,
    isLoading: state.isLoading,
    error: state.error,
    login,
    logout,
    checkAuth,
  };
}