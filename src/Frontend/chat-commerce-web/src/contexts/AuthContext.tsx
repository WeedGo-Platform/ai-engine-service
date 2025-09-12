import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { authApi } from '../services/api';
import { otpService } from '../services/otp';
import { User, AuthState, LoginCredentials, RegisterData, AuthContextType } from '../types/auth.types';
import { detectContactType } from '../utils/validation';

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [authState, setAuthState] = useState<AuthState>({
    currentUser: null,
    isAuthenticated: false,
    isLoading: true,
    error: null,
  });

  // Initialize auth state from localStorage on mount
  useEffect(() => {
    const initAuth = async () => {
      try {
        const token = localStorage.getItem('access_token');
        const savedUser = localStorage.getItem('user');
        
        if (token && savedUser) {
          // Verify token is still valid
          try {
            await authApi.verifyToken();
            const userData = JSON.parse(savedUser);
            setAuthState({
              currentUser: userData,
              isAuthenticated: true,
              isLoading: false,
              error: null,
            });
          } catch (error) {
            // Token is invalid, clear storage
            localStorage.removeItem('access_token');
            localStorage.removeItem('user');
            setAuthState({
              currentUser: null,
              isAuthenticated: false,
              isLoading: false,
              error: null,
            });
          }
        } else {
          setAuthState({
            currentUser: null,
            isAuthenticated: false,
            isLoading: false,
            error: null,
          });
        }
      } catch (error) {
        console.error('Auth initialization error:', error);
        setAuthState({
          currentUser: null,
          isAuthenticated: false,
          isLoading: false,
          error: 'Failed to initialize authentication',
        });
      }
    };

    initAuth();
  }, []);

  const login = async (credentials: LoginCredentials) => {
    setAuthState(prev => ({ ...prev, isLoading: true, error: null }));
    
    try {
      const response = await authApi.login({
        email: credentials.email,
        password: credentials.password,
      });
      
      const user: User = {
        id: response.user.id,
        email: response.user.email,
        name: response.user.name || `${response.user.first_name} ${response.user.last_name}`,
        firstName: response.user.first_name,
        lastName: response.user.last_name,
        phoneNumber: response.user.phone,
        dateOfBirth: response.user.date_of_birth,
      };
      
      setAuthState({
        currentUser: user,
        isAuthenticated: true,
        isLoading: false,
        error: null,
      });
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || error.response?.data?.message || 'Login failed';
      setAuthState({
        currentUser: null,
        isAuthenticated: false,
        isLoading: false,
        error: errorMessage,
      });
      throw new Error(errorMessage);
    }
  };

  const loginWithOTP = async (contact: string, code: string) => {
    setAuthState(prev => ({ ...prev, isLoading: true, error: null }));
    
    try {
      const contactInfo = detectContactType(contact);
      
      if (contactInfo.type === 'invalid') {
        throw new Error('Please enter a valid email address or phone number');
      }
      
      // Verify OTP using the OTP service
      const response = await otpService.verifyOTP({
        identifier: contactInfo.value,
        code: code
      });
      
      if (response.success && response.user) {
        const user: User = {
          id: response.user.id,
          email: response.user.email || contactInfo.value,
          name: response.user.name || `${response.user.first_name} ${response.user.last_name}`,
          firstName: response.user.first_name,
          lastName: response.user.last_name,
          phoneNumber: response.user.phone,
          dateOfBirth: response.user.date_of_birth,
        };
        
        setAuthState({
          currentUser: user,
          isAuthenticated: true,
          isLoading: false,
          error: null,
        });
        
        // Store user info (tokens are handled by OTP service)
        localStorage.setItem('user', JSON.stringify(user));
      } else {
        throw new Error(response.message || 'OTP verification failed');
      }
    } catch (error: any) {
      const errorMessage = error.message || 'OTP login failed';
      setAuthState({
        currentUser: null,
        isAuthenticated: false,
        isLoading: false,
        error: errorMessage,
      });
      throw new Error(errorMessage);
    }
  };

  const register = async (data: RegisterData) => {
    setAuthState(prev => ({ ...prev, isLoading: true, error: null }));
    
    // Validate age (must be 21+)
    const birthDate = new Date(data.dateOfBirth);
    const today = new Date();
    const age = today.getFullYear() - birthDate.getFullYear();
    const monthDiff = today.getMonth() - birthDate.getMonth();
    const dayDiff = today.getDate() - birthDate.getDate();
    
    const actualAge = monthDiff < 0 || (monthDiff === 0 && dayDiff < 0) ? age - 1 : age;
    
    if (actualAge < 21) {
      setAuthState({
        currentUser: null,
        isAuthenticated: false,
        isLoading: false,
        error: 'You must be 21 or older to register',
      });
      throw new Error('You must be 21 or older to register');
    }
    
    try {
      const response = await authApi.register({
        email: data.email,
        password: data.password,
        first_name: data.first_name,
        last_name: data.last_name,
        date_of_birth: data.dateOfBirth,
        phone: data.phoneNumber,
      });
      
      const user: User = {
        id: response.user.id,
        email: response.user.email,
        name: response.user.name || `${response.user.first_name} ${response.user.last_name}`,
        firstName: response.user.first_name,
        lastName: response.user.last_name,
        phoneNumber: response.user.phone,
        dateOfBirth: response.user.date_of_birth,
      };
      
      setAuthState({
        currentUser: user,
        isAuthenticated: true,
        isLoading: false,
        error: null,
      });
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || error.response?.data?.message || 'Registration failed';
      setAuthState({
        currentUser: null,
        isAuthenticated: false,
        isLoading: false,
        error: errorMessage,
      });
      throw new Error(errorMessage);
    }
  };

  const sendOTP = async (contact: string): Promise<any> => {
    const contactInfo = detectContactType(contact);
    
    if (contactInfo.type === 'invalid') {
      throw new Error('Please enter a valid email address or phone number');
    }
    
    try {
      // Send OTP using the OTP service
      const response = await otpService.sendOTP({
        identifier: contactInfo.value,
        type: contactInfo.type === 'email' ? 'email' : 'phone'
      });
      
      return {
        success: response.success,
        message: response.message || `Verification code sent to ${otpService.maskIdentifier(contactInfo.value)}`,
        type: response.type,
        identifier: response.identifier
      };
    } catch (error: any) {
      throw new Error(error.message || 'Failed to send OTP');
    }
  };

  const resendOTP = async (identifier: string): Promise<any> => {
    try {
      const response = await otpService.resendOTP(identifier);
      return {
        success: response.success,
        message: response.message || `Verification code resent to ${otpService.maskIdentifier(identifier)}`,
        type: response.type,
        identifier: response.identifier
      };
    } catch (error: any) {
      throw new Error(error.message || 'Failed to resend OTP');
    }
  };

  const getOTPStatus = async (identifier: string): Promise<any> => {
    try {
      const status = await otpService.getOTPStatus(identifier);
      return status;
    } catch (error: any) {
      console.error('Error getting OTP status:', error);
      return {
        exists: false,
        identifier,
        can_resend: true
      };
    }
  };

  const logout = async () => {
    setAuthState(prev => ({ ...prev, isLoading: true, error: null }));
    
    try {
      await authApi.logout();
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      // Clear auth state regardless of API response
      localStorage.removeItem('access_token');
      localStorage.removeItem('user');
      setAuthState({
        currentUser: null,
        isAuthenticated: false,
        isLoading: false,
        error: null,
      });
    }
  };

  const clearError = () => {
    setAuthState(prev => ({ ...prev, error: null }));
  };

  const contextValue: AuthContextType = {
    ...authState,
    login,
    loginWithOTP,
    register,
    sendOTP,
    resendOTP,
    getOTPStatus,
    logout,
    clearError,
  };

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  );
};

export default AuthContext;