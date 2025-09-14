import { appConfig } from '../config/app.config';
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5024';

interface UploadResult {
  success: boolean;
  message: string;
  stats: {
    totalRecords: number;
    inserted: number;
    updated: number;
    errors: number;
  };
}

export const uploadProvincialCatalog = async (
  file: File,
  province: string
): Promise<UploadResult> => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('province', province);

  try {
    const token = localStorage.getItem('authToken');
    
    const response = await axios.post(
      `${API_BASE_URL}/api/admin/provincial-catalog/upload`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
          'Authorization': `Bearer ${token}`
        },
        onUploadProgress: (progressEvent) => {
          if (progressEvent.total) {
            const percentCompleted = Math.round(
              (progressEvent.loaded * 100) / progressEvent.total
            );
            console.log(`Upload Progress: ${percentCompleted}%`);
          }
        }
      }
    );

    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      throw new Error(error.response?.data?.detail || 'Failed to upload catalog');
    }
    throw error;
  }
};