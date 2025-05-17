// frontend/src/api/auth.ts
import apiClient from './client';

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface RegisterData {
  email: string;
  password: string;
  full_name: string;
  role: 'student' | 'instructor' | 'admin';
  phone?: string;
  address?: string;
}

export interface User {
  id: number;
  email: string;
  full_name: string;
  role: string;
  phone?: string;
  address?: string;
  is_active: boolean;
  profile_picture?: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
}

const authApi = {
  login: async (credentials: LoginCredentials): Promise<AuthResponse> => {
    const formData = new URLSearchParams();
    formData.append('username', credentials.username);
    formData.append('password', credentials.password);
    
    return apiClient.post<AuthResponse>('/auth/login', formData.toString(), {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });
  },
  
  register: async (userData: RegisterData): Promise<User> => {
    return apiClient.post<User>('/auth/register', userData);
  },
  
  getCurrentUser: async (): Promise<User> => {
    return apiClient.get<User>('/auth/me');
  },
};

export default authApi;