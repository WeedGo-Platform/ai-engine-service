import api from './api';

export interface OTPSendRequest {
  identifier: string; // email or phone number
  type?: 'email' | 'phone' | 'auto'; // auto will detect based on format
}

export interface OTPSendResponse {
  success: boolean;
  message: string;
  identifier: string;
  type: 'email' | 'phone';
  expires_at?: string;
}

export interface OTPVerifyRequest {
  identifier: string;
  code: string;
}

export interface OTPVerifyResponse {
  success: boolean;
  message: string;
  access_token?: string;
  refresh_token?: string;
  user?: {
    id: string;
    email?: string;
    phone?: string;
    name?: string;
    first_name?: string;
    last_name?: string;
    date_of_birth?: string;
  };
}

export interface OTPStatusResponse {
  exists: boolean;
  identifier: string;
  type: 'email' | 'phone';
  attempts_remaining?: number;
  expires_at?: string;
  can_resend: boolean;
  resend_cooldown?: number; // seconds until can resend
}

class OTPService {
  /**
   * Send OTP to email or phone
   */
  async sendOTP(request: OTPSendRequest): Promise<OTPSendResponse> {
    try {
      const response = await api.post('/api/v1/auth/otp/send', request);
      return response.data;
    } catch (error: any) {
      console.error('Error sending OTP:', error);
      throw {
        success: false,
        message: error.response?.data?.message || 'Failed to send OTP',
        error: error.response?.data || error
      };
    }
  }

  /**
   * Verify OTP code
   */
  async verifyOTP(request: OTPVerifyRequest): Promise<OTPVerifyResponse> {
    try {
      const response = await api.post('/api/v1/auth/otp/verify', request);
      
      // Store tokens if successful
      if (response.data.access_token) {
        localStorage.setItem('access_token', response.data.access_token);
        if (response.data.refresh_token) {
          localStorage.setItem('refresh_token', response.data.refresh_token);
        }
        if (response.data.user) {
          localStorage.setItem('user', JSON.stringify(response.data.user));
        }
      }
      
      return response.data;
    } catch (error: any) {
      console.error('Error verifying OTP:', error);
      throw {
        success: false,
        message: error.response?.data?.message || 'Invalid or expired OTP',
        error: error.response?.data || error
      };
    }
  }

  /**
   * Resend OTP
   */
  async resendOTP(identifier: string): Promise<OTPSendResponse> {
    try {
      const response = await api.post('/api/v1/auth/otp/resend', { identifier });
      return response.data;
    } catch (error: any) {
      console.error('Error resending OTP:', error);
      throw {
        success: false,
        message: error.response?.data?.message || 'Failed to resend OTP',
        error: error.response?.data || error
      };
    }
  }

  /**
   * Check OTP status
   */
  async getOTPStatus(identifier: string): Promise<OTPStatusResponse> {
    try {
      const response = await api.get(`/api/auth/otp/status/${encodeURIComponent(identifier)}`);
      return response.data;
    } catch (error: any) {
      console.error('Error checking OTP status:', error);
      return {
        exists: false,
        identifier,
        type: 'email',
        can_resend: true
      };
    }
  }

  /**
   * Detect if identifier is email or phone
   */
  detectIdentifierType(identifier: string): 'email' | 'phone' {
    // Simple email regex
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    // Simple phone regex (digits, spaces, dashes, parentheses, plus sign)
    const phoneRegex = /^[\+]?[(]?[0-9]{1,3}[)]?[-\s\.]?[(]?[0-9]{1,4}[)]?[-\s\.]?[0-9]{1,4}[-\s\.]?[0-9]{1,9}$/;
    
    if (emailRegex.test(identifier)) {
      return 'email';
    } else if (phoneRegex.test(identifier.replace(/\s/g, ''))) {
      return 'phone';
    }
    
    // Default to email if uncertain
    return 'email';
  }

  /**
   * Format phone number for display
   */
  formatPhoneNumber(phone: string): string {
    // Remove all non-digits
    const cleaned = phone.replace(/\D/g, '');
    
    // Format as (XXX) XXX-XXXX for US numbers
    if (cleaned.length === 10) {
      return `(${cleaned.slice(0, 3)}) ${cleaned.slice(3, 6)}-${cleaned.slice(6)}`;
    } else if (cleaned.length === 11 && cleaned[0] === '1') {
      return `+1 (${cleaned.slice(1, 4)}) ${cleaned.slice(4, 7)}-${cleaned.slice(7)}`;
    }
    
    return phone;
  }

  /**
   * Mask identifier for display (e.g., em***@gmail.com or (***) ***-1234)
   */
  maskIdentifier(identifier: string, type?: 'email' | 'phone'): string {
    const detectedType = type || this.detectIdentifierType(identifier);
    
    if (detectedType === 'email') {
      const [localPart, domain] = identifier.split('@');
      if (localPart.length <= 3) {
        return `${localPart[0]}***@${domain}`;
      }
      return `${localPart.slice(0, 2)}***@${domain}`;
    } else {
      const cleaned = identifier.replace(/\D/g, '');
      if (cleaned.length >= 10) {
        return `(***) ***-${cleaned.slice(-4)}`;
      }
      return identifier.replace(/\d(?=\d{4})/g, '*');
    }
  }
}

// Export singleton instance
export const otpService = new OTPService();