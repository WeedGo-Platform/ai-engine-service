export interface User {
  id?: string;
  email: string;
  name?: string;
  firstName?: string;
  lastName?: string;
  phoneNumber?: string;
  dateOfBirth?: string;
}

export interface AuthState {
  currentUser: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterData {
  first_name: string;
  last_name: string;
  email: string;
  phoneNumber: string;
  dateOfBirth: string;
  password: string;
}

export interface AuthContextType extends AuthState {
  login: (credentials: LoginCredentials) => Promise<void>;
  loginWithOTP: (email: string, code: string) => Promise<void>;
  register: (data: RegisterData) => Promise<void>;
  sendOTP: (email: string) => Promise<any>;
  resendOTP: (identifier: string) => Promise<any>;
  getOTPStatus: (identifier: string) => Promise<any>;
  logout: () => Promise<void>;
  clearError: () => void;
}