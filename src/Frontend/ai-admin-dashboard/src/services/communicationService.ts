import { CommunicationSettings } from '../components/CommunicationSettings';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

class CommunicationService {
  /**
   * Get tenant communication settings
   */
  async getTenantCommunicationSettings(tenantId: string): Promise<CommunicationSettings> {
    const token = localStorage.getItem('token');
    const response = await fetch(`${API_URL}/api/v1/tenants/${tenantId}/communication-settings`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      throw new Error('Failed to fetch communication settings');
    }

    const data = await response.json();
    return data.settings || this.getDefaultSettings();
  }

  /**
   * Update tenant communication settings
   */
  async updateTenantCommunicationSettings(
    tenantId: string,
    settings: CommunicationSettings
  ): Promise<void> {
    const token = localStorage.getItem('token');
    const response = await fetch(`${API_URL}/api/v1/tenants/${tenantId}/communication-settings`, {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ settings }),
    });

    if (!response.ok) {
      throw new Error('Failed to update communication settings');
    }
  }

  /**
   * Validate communication channel configuration
   */
  async validateCommunicationChannel(
    tenantId: string,
    channel: 'sms' | 'email'
  ): Promise<{ valid: boolean; message: string }> {
    const token = localStorage.getItem('token');
    const response = await fetch(
      `${API_URL}/api/v1/tenants/${tenantId}/communication-settings/validate`,
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ channel }),
      }
    );

    if (!response.ok) {
      const error = await response.json();
      return { valid: false, message: error.message || 'Validation failed' };
    }

    const data = await response.json();
    return { valid: data.valid, message: data.message };
  }

  /**
   * Get default communication settings
   */
  private getDefaultSettings(): CommunicationSettings {
    return {
      sms: {
        provider: 'twilio',
        enabled: false,
        twilio: {
          accountSid: '',
          authToken: '',
          phoneNumber: '',
          verifyServiceSid: '',
        },
      },
      email: {
        provider: 'sendgrid',
        enabled: false,
        sendgrid: {
          apiKey: '',
          fromEmail: '',
          fromName: '',
          replyToEmail: '',
        },
      },
    };
  }
}

export default new CommunicationService();