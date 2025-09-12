import axios from 'axios';

const API_BASE_URL = 'http://localhost:5024/api/stores';

export interface TimeSlot {
  open: string;
  close: string;
}

export interface ServiceHours {
  enabled: boolean;
  time_slots: TimeSlot[];
}

export interface RegularHours {
  day_of_week: number;
  is_closed: boolean;
  time_slots: TimeSlot[];
  delivery_hours?: ServiceHours;
  pickup_hours?: ServiceHours;
}

export interface HolidayHours {
  id?: string;
  holiday_id: string;
  is_closed: boolean;
  time_slots: TimeSlot[];
  delivery_hours?: ServiceHours;
  pickup_hours?: ServiceHours;
}

export interface SpecialHours {
  id?: string;
  date: string;
  is_closed: boolean;
  reason?: string;
  time_slots: TimeSlot[];
  delivery_hours?: ServiceHours;
  pickup_hours?: ServiceHours;
}

export interface StoreHoursSettings {
  observe_federal_holidays: boolean;
  observe_provincial_holidays: boolean;
  observe_municipal_holidays: boolean;
  default_holiday_action: 'closed' | 'modified' | 'open';
  modified_holiday_hours?: TimeSlot[];
  delivery_holiday_behavior: 'same_as_store' | 'closed' | 'modified';
  pickup_holiday_behavior: 'same_as_store' | 'closed' | 'modified';
}

export interface Holiday {
  id: string;
  name: string;
  holiday_type: 'federal' | 'provincial' | 'municipal' | 'custom';
  province_code?: string;
  date_type: 'fixed' | 'floating' | 'calculated';
  month?: number;
  day?: number;
  occurrence_week?: number;
  occurrence_day?: number;
}

export interface StoreHoursResponse {
  regular_hours: RegularHours[];
  holiday_hours: HolidayHours[];
  special_hours: SpecialHours[];
  settings: StoreHoursSettings;
  holidays: Holiday[];
}

class StoreHoursService {
  async getStoreHours(storeId: string): Promise<StoreHoursResponse> {
    const response = await axios.get(`${API_BASE_URL}/${storeId}/hours`);
    return response.data;
  }

  async updateRegularHours(storeId: string, hours: RegularHours[]): Promise<void> {
    await axios.put(`${API_BASE_URL}/${storeId}/hours/regular`, hours);
  }

  async addHolidayHours(storeId: string, holidayHours: HolidayHours): Promise<HolidayHours> {
    const response = await axios.post(`${API_BASE_URL}/${storeId}/hours/holidays`, holidayHours);
    return response.data;
  }

  async updateHolidayHours(storeId: string, holidayHoursId: string, holidayHours: HolidayHours): Promise<HolidayHours> {
    const response = await axios.put(`${API_BASE_URL}/${storeId}/hours/holidays/${holidayHoursId}`, holidayHours);
    return response.data;
  }

  async deleteHolidayHours(storeId: string, holidayHoursId: string): Promise<void> {
    await axios.delete(`${API_BASE_URL}/${storeId}/hours/holidays/${holidayHoursId}`);
  }

  async addSpecialHours(storeId: string, specialHours: SpecialHours): Promise<SpecialHours> {
    const response = await axios.post(`${API_BASE_URL}/${storeId}/hours/special`, specialHours);
    return response.data;
  }

  async updateSpecialHours(storeId: string, specialHoursId: string, specialHours: SpecialHours): Promise<SpecialHours> {
    const response = await axios.put(`${API_BASE_URL}/${storeId}/hours/special/${specialHoursId}`, specialHours);
    return response.data;
  }

  async deleteSpecialHours(storeId: string, specialHoursId: string): Promise<void> {
    await axios.delete(`${API_BASE_URL}/${storeId}/hours/special/${specialHoursId}`);
  }

  async updateSettings(storeId: string, settings: StoreHoursSettings): Promise<void> {
    await axios.put(`${API_BASE_URL}/${storeId}/hours/settings`, settings);
  }

  async getHolidays(): Promise<Holiday[]> {
    const response = await axios.get(`${API_BASE_URL}/holidays`);
    return response.data;
  }
}

export default new StoreHoursService();