import React, { createContext, useState, useEffect, ReactNode } from 'react';
import authApi from '../api/auth';
import { User, UserRole } from '../types/auth.types';

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<boolean>;
  register: (userData: any) => Promise<boolean>;
  logout: () => void;
  updateUser: (userData: Partial<User>) => void;
  error: string | null;
}

export const AuthContext = createContext<AuthContextType>({
  user: null,
  isAuthenticated: false,
  isLoading: true,
  login: async () => false,
  register: async () => false,
  logout: () => {},
  updateUser: () => {},
  error: null,
});

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const checkAuth = async () => {
      const token = localStorage.getItem('token');
      
      if (token) {
        try {
          const userData = await authApi.getCurrentUser();
          setUser(userData);
          setIsAuthenticated(true);
        } catch (error) {
          console.error('Authentication check failed:', error);
          localStorage.removeItem('token');
        }
      }
      
      setIsLoading(false);
    };

    checkAuth();
  }, []);

  const login = async (email: string, password: string): Promise<boolean> => {
    setError(null);
    setIsLoading(true);
    
    try {
      const response = await authApi.login({ username: email, password });
      localStorage.setItem('token', response.access_token);
      
      // Get user details
      const userData = await authApi.getCurrentUser();
      setUser(userData);
      setIsAuthenticated(true);
      
      return true;
    } catch (error) {
      console.error('Login failed:', error);
      setError(error.response?.data?.detail || 'Login failed. Please check your credentials.');
      return false;
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (userData: any): Promise<boolean> => {
    setError(null);
    setIsLoading(true);
    
    try {
      await authApi.register(userData);
      
      // Auto-login after registration
      return await login(userData.email, userData.password);
    } catch (error) {
      console.error('Registration failed:', error);
      setError(error.response?.data?.detail || 'Registration failed. Please try again.');
      return false;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    setUser(null);
    setIsAuthenticated(false);
  };

  const updateUser = (userData: Partial<User>) => {
    if (user) {
      setUser({ ...user, ...userData });
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated,
        isLoading,
        login,
        register,
        logout,
        updateUser,
        error,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};