export interface LoginCredentials {
  username: string;
  password: string;
}

export interface RegisterData {
  email: string;
  password: string;
  full_name: string;
  role: UserRole;
  phone?: string;
  address?: string;
}

export interface Token {
  access_token: string;
  token_type: string;
}

export enum UserRole {
  STUDENT = "student",
  INSTRUCTOR = "instructor",
  ADMIN = "admin"
}

export interface User {
  id: number;
  email: string;
  full_name: string;
  role: UserRole;
  phone?: string;
  address?: string;
  is_active: boolean;
  profile_picture?: string;
  created_at: string;
  updated_at: string;
}

export interface UserWithToken extends User {
  access_token: string;
  token_type: string;
}