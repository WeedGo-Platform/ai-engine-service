import { appConfig } from '../config/app.config';
import axios from 'axios';

const API_BASE_URL = appConfig.api.baseUrl;

export interface StoreSetting {
  id: string;
  store_id: string;
  category: string;
  key: string;
  value: any;
  description?: string;
  created_at: string;
  updated_at: string;
}

export interface StoreSettingsCategory {
  category: string;
  settings: Record<string, any>;
}

export type SettingCategory = 
  | 'product' 
  | 'search' 
  | 'inventory' 
  | 'display' 
  | 'location' 
  | 'compliance';

class StoreSettingsService {
  private api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
      'Content-Type': 'application/json',
    },
  });

  // Get all settings for a store
  async getStoreSettings(storeId: string): Promise<StoreSetting[]> {
    const response = await this.api.get(`/api/stores/${storeId}/settings`);
    return response.data;
  }

  // Get settings by category
  async getSettingsByCategory(storeId: string, category: SettingCategory): Promise<StoreSetting[]> {
    const response = await this.api.get(`/api/stores/${storeId}/settings/${category}`);
    return response.data;
  }

  // Get a specific setting
  async getSetting(storeId: string, category: SettingCategory, key: string): Promise<StoreSetting> {
    const response = await this.api.get(`/api/stores/${storeId}/settings/${category}/${key}`);
    return response.data;
  }

  // Update a specific setting
  async updateSetting(
    storeId: string, 
    category: SettingCategory, 
    key: string, 
    value: any
  ): Promise<StoreSetting> {
    const response = await this.api.put(
      `/api/stores/${storeId}/settings/${category}/${key}`,
      { value }
    );
    return response.data;
  }

  // Bulk update settings for a category
  async updateCategorySettings(
    storeId: string,
    category: SettingCategory,
    settings: Record<string, any>
  ): Promise<StoreSetting[]> {
    const response = await this.api.put(
      `/api/stores/${storeId}/settings/${category}`,
      { settings }
    );
    return response.data;
  }

  // Reset settings to defaults
  async resetToDefaults(storeId: string, category?: SettingCategory): Promise<StoreSetting[]> {
    const url = category 
      ? `/api/stores/${storeId}/settings/${category}/reset`
      : `/api/stores/${storeId}/settings/reset`;
    const response = await this.api.post(url);
    return response.data;
  }

  // Helper method to transform settings array to grouped object
  groupSettingsByCategory(settings: StoreSetting[]): Record<SettingCategory, Record<string, any>> {
    const grouped: Record<string, Record<string, any>> = {};
    
    settings.forEach(setting => {
      if (!grouped[setting.category]) {
        grouped[setting.category] = {};
      }
      grouped[setting.category][setting.key] = setting.value;
    });
    
    return grouped as Record<SettingCategory, Record<string, any>>;
  }

  // Helper method to get formatted settings for UI
  async getFormattedSettings(storeId: string): Promise<Record<SettingCategory, Record<string, any>>> {
    const settings = await this.getStoreSettings(storeId);
    return this.groupSettingsByCategory(settings);
  }
}

export default new StoreSettingsService();