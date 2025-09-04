import { useState, useEffect, useCallback } from 'react';
import toast from 'react-hot-toast';

interface UseApiOptions {
  showError?: boolean;
  showSuccess?: boolean;
  successMessage?: string;
  errorMessage?: string;
}

interface UseApiResult<T> {
  data: T | null;
  loading: boolean;
  error: Error | null;
  refetch: () => Promise<void>;
  mutate: (newData: T) => void;
}

export function useApi<T>(
  apiCall: () => Promise<T>,
  dependencies: any[] = [],
  options: UseApiOptions = {}
): UseApiResult<T> {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const {
    showError = true,
    showSuccess = false,
    successMessage = 'Success!',
    errorMessage = 'An error occurred',
  } = options;

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const result = await apiCall();
      setData(result);
      if (showSuccess) {
        toast.success(successMessage);
      }
    } catch (err) {
      const error = err as Error;
      setError(error);
      if (showError) {
        toast.error(errorMessage || error.message);
      }
    } finally {
      setLoading(false);
    }
  }, [apiCall, showError, showSuccess, successMessage, errorMessage]);

  useEffect(() => {
    fetchData();
  }, dependencies);

  const refetch = useCallback(async () => {
    await fetchData();
  }, [fetchData]);

  const mutate = useCallback((newData: T) => {
    setData(newData);
  }, []);

  return { data, loading, error, refetch, mutate };
}

export function useApiMutation<TData, TVariables>(
  apiCall: (variables: TVariables) => Promise<TData>,
  options: UseApiOptions = {}
) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const {
    showError = true,
    showSuccess = true,
    successMessage = 'Success!',
    errorMessage = 'An error occurred',
  } = options;

  const mutate = useCallback(async (variables: TVariables): Promise<TData | null> => {
    try {
      setLoading(true);
      setError(null);
      const result = await apiCall(variables);
      if (showSuccess) {
        toast.success(successMessage);
      }
      return result;
    } catch (err) {
      const error = err as Error;
      setError(error);
      if (showError) {
        toast.error(errorMessage || error.message);
      }
      return null;
    } finally {
      setLoading(false);
    }
  }, [apiCall, showError, showSuccess, successMessage, errorMessage]);

  return { mutate, loading, error };
}