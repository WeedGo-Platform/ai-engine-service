/**
 * API Service Unit Tests
 * Tests for API service layer with mocked fetch
 */

import { apiService, APIError } from '../services/api';

// Mock fetch globally
global.fetch = jest.fn();

describe('API Service', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    // Reset localStorage
    localStorage.clear();
    localStorage.setItem('auth_token', 'test-token');
  });

  describe('Request Configuration', () => {
    it('should add authentication headers to requests', async () => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ success: true }),
        headers: new Headers({ 'content-type': 'application/json' })
      });

      await apiService.get('/test');

      expect(fetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          headers: expect.objectContaining({
            'Authorization': 'Bearer test-token',
            'Content-Type': 'application/json'
          })
        })
      );
    });

    it('should handle requests without authentication token', async () => {
      localStorage.removeItem('auth_token');

      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ success: true }),
        headers: new Headers({ 'content-type': 'application/json' })
      });

      await apiService.get('/test');

      expect(fetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          headers: expect.not.objectContaining({
            'Authorization': expect.any(String)
          })
        })
      );
    });
  });

  describe('HTTP Methods', () => {
    it('should make GET requests', async () => {
      const mockResponse = { data: 'test' };
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
        headers: new Headers({ 'content-type': 'application/json' })
      });

      const result = await apiService.get('/test');

      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/test'),
        expect.objectContaining({ method: 'GET' })
      );
      expect(result).toEqual(mockResponse);
    });

    it('should make POST requests with body', async () => {
      const requestBody = { name: 'test' };
      const mockResponse = { id: 1, ...requestBody };

      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
        headers: new Headers({ 'content-type': 'application/json' })
      });

      const result = await apiService.post('/test', requestBody);

      expect(fetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify(requestBody)
        })
      );
      expect(result).toEqual(mockResponse);
    });

    it('should make PUT requests', async () => {
      const requestBody = { name: 'updated' };

      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => requestBody,
        headers: new Headers({ 'content-type': 'application/json' })
      });

      const result = await apiService.put('/test/1', requestBody);

      expect(fetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          method: 'PUT',
          body: JSON.stringify(requestBody)
        })
      );
    });

    it('should make DELETE requests', async () => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ success: true }),
        headers: new Headers({ 'content-type': 'application/json' })
      });

      await apiService.delete('/test/1');

      expect(fetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({ method: 'DELETE' })
      );
    });
  });

  describe('Error Handling', () => {
    it('should handle 401 unauthorized errors', async () => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 401,
        statusText: 'Unauthorized',
        json: async () => ({ message: 'Invalid token' })
      });

      await expect(apiService.get('/test')).rejects.toThrow(APIError);

      try {
        await apiService.get('/test');
      } catch (error) {
        expect(error).toBeInstanceOf(APIError);
        if (error instanceof APIError) {
          expect(error.status).toBe(401);
          expect(error.message).toBe('Invalid token');
        }
      }
    });

    it('should handle 404 not found errors', async () => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 404,
        statusText: 'Not Found',
        json: async () => ({ message: 'Resource not found' })
      });

      await expect(apiService.get('/test')).rejects.toThrow(APIError);
    });

    it('should handle 500 server errors', async () => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error',
        json: async () => ({ message: 'Server error' })
      });

      await expect(apiService.get('/test')).rejects.toThrow(APIError);
    });

    it('should handle network errors', async () => {
      (fetch as jest.Mock).mockRejectedValueOnce(new Error('Network error'));

      await expect(apiService.get('/test')).rejects.toThrow('Network error');
    });

    it('should handle non-JSON responses', async () => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        text: async () => 'Plain text response',
        headers: new Headers({ 'content-type': 'text/plain' })
      });

      const result = await apiService.get('/test');
      expect(result).toBe('Plain text response');
    });
  });

  describe('Query Parameters', () => {
    it('should append query parameters to GET requests', async () => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ data: [] }),
        headers: new Headers({ 'content-type': 'application/json' })
      });

      await apiService.get('/test', {
        params: {
          page: 1,
          limit: 10,
          filter: 'active'
        }
      });

      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('?page=1&limit=10&filter=active'),
        expect.any(Object)
      );
    });

    it('should handle empty query parameters', async () => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ data: [] }),
        headers: new Headers({ 'content-type': 'application/json' })
      });

      await apiService.get('/test', { params: {} });

      expect(fetch).toHaveBeenCalledWith(
        expect.not.stringContaining('?'),
        expect.any(Object)
      );
    });
  });

  describe('Request Interceptors', () => {
    it('should support request timeout', async () => {
      jest.useFakeTimers();

      (fetch as jest.Mock).mockImplementation(() =>
        new Promise(resolve => setTimeout(resolve, 10000))
      );

      const promise = apiService.get('/test', { timeout: 5000 });

      jest.advanceTimersByTime(5000);

      await expect(promise).rejects.toThrow('Request timeout');

      jest.useRealTimers();
    });

    it('should retry failed requests', async () => {
      (fetch as jest.Mock)
        .mockRejectedValueOnce(new Error('Network error'))
        .mockRejectedValueOnce(new Error('Network error'))
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ success: true }),
          headers: new Headers({ 'content-type': 'application/json' })
        });

      const result = await apiService.get('/test', { retry: 3 });

      expect(fetch).toHaveBeenCalledTimes(3);
      expect(result).toEqual({ success: true });
    });
  });

  describe('Response Transformation', () => {
    it('should transform snake_case to camelCase', async () => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          user_name: 'test',
          created_at: '2024-01-01',
          is_active: true
        }),
        headers: new Headers({ 'content-type': 'application/json' })
      });

      const result = await apiService.get('/test');

      expect(result).toEqual({
        userName: 'test',
        createdAt: '2024-01-01',
        isActive: true
      });
    });

    it('should handle nested object transformation', async () => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          user_data: {
            first_name: 'John',
            last_name: 'Doe',
            contact_info: {
              phone_number: '123456'
            }
          }
        }),
        headers: new Headers({ 'content-type': 'application/json' })
      });

      const result = await apiService.get('/test');

      expect(result).toEqual({
        userData: {
          firstName: 'John',
          lastName: 'Doe',
          contactInfo: {
            phoneNumber: '123456'
          }
        }
      });
    });
  });

  describe('Caching', () => {
    it('should cache GET requests', async () => {
      const mockResponse = { data: 'cached' };

      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
        headers: new Headers({ 'content-type': 'application/json' })
      });

      // First request
      const result1 = await apiService.get('/test', { cache: true });
      // Second request should use cache
      const result2 = await apiService.get('/test', { cache: true });

      expect(fetch).toHaveBeenCalledTimes(1);
      expect(result1).toEqual(result2);
    });

    it('should invalidate cache on POST/PUT/DELETE', async () => {
      (fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => ({ success: true }),
        headers: new Headers({ 'content-type': 'application/json' })
      });

      await apiService.get('/test', { cache: true });
      await apiService.post('/test', {});
      await apiService.get('/test', { cache: true });

      expect(fetch).toHaveBeenCalledTimes(3);
    });
  });
});

describe('APIError Class', () => {
  it('should create error with status and message', () => {
    const error = new APIError(404, 'Not Found', { details: 'Resource missing' });

    expect(error.status).toBe(404);
    expect(error.message).toBe('Not Found');
    expect(error.data).toEqual({ details: 'Resource missing' });
    expect(error.name).toBe('APIError');
  });

  it('should be instanceof Error', () => {
    const error = new APIError(500, 'Server Error');
    expect(error).toBeInstanceOf(Error);
    expect(error).toBeInstanceOf(APIError);
  });
});