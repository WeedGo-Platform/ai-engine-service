/**
 * Format API error response for display
 * Handles both FastAPI validation errors (array) and regular error strings
 */
export const formatApiError = (error: any, fallbackMessage: string = 'An error occurred'): string => {
  // Handle FastAPI validation errors (array of {type, loc, msg, input, ctx})
  if (Array.isArray(error.detail)) {
    return error.detail.map((e: any) => e.msg || e.message || 'Validation error').join(', ');
  }
  
  // Handle string detail
  if (typeof error.detail === 'string') {
    return error.detail;
  }
  
  // Handle error message
  if (typeof error.message === 'string') {
    return error.message;
  }
  
  // Fallback
  return fallbackMessage;
};
