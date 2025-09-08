/**
 * Utility to safely extract message content from API responses
 * Handles various response formats and edge cases
 */

interface ApiResponse {
  response?: string | any;
  message?: string | any;
  text?: string | any;
  content?: string | any;
  data?: string | any;
  [key: string]: any;
}

/**
 * Safely converts any value to a string representation
 * @param value - The value to convert
 * @param fallback - Fallback value if conversion fails
 * @returns A string representation of the value
 */
export function safeStringify(value: any, fallback: string = ''): string {
  // Handle null/undefined
  if (value === null || value === undefined) {
    return fallback;
  }

  // Already a string
  if (typeof value === 'string') {
    return value;
  }

  // Numbers and booleans
  if (typeof value === 'number' || typeof value === 'boolean') {
    return String(value);
  }

  // Arrays and objects
  if (typeof value === 'object') {
    try {
      // Special handling for Error objects
      if (value instanceof Error) {
        return value.message || value.toString();
      }

      // Try to stringify objects/arrays
      const stringified = JSON.stringify(value, null, 2);
      
      // If it's just an empty object/array, return a more user-friendly message
      if (stringified === '{}') {
        return fallback || 'Empty response';
      }
      if (stringified === '[]') {
        return fallback || 'Empty list';
      }
      
      return stringified;
    } catch (error) {
      console.error('Failed to stringify value:', error);
      // If circular reference or other stringify error, try toString
      try {
        return value.toString();
      } catch {
        return fallback || '[Unable to display content]';
      }
    }
  }

  // Functions or other types
  return fallback || '[Unsupported content type]';
}

/**
 * Extracts message content from various API response formats
 * @param response - The API response
 * @returns The extracted message content as a string
 */
export function extractMessageContent(response: any): string {
  // Log for debugging in development
  if (typeof window !== 'undefined' && window.location.hostname === 'localhost') {
    console.log('Extracting content from response:', response);
  }

  // Handle null/undefined response
  if (!response) {
    console.warn('Received null/undefined response');
    return 'No response received';
  }

  // If response is already a string, return it
  if (typeof response === 'string') {
    return response;
  }

  // Check common response fields in order of preference
  const responseFields = [
    'response',     // Primary field based on actual API
    'message',      // Common alternative
    'text',         // Another common field
    'content',      // Content field
    'data',         // Generic data field
    'result',       // Result field
    'output',       // Output field
    'answer',       // Answer field (for Q&A systems)
    'reply',        // Reply field
  ];

  // Try to extract content from known fields
  for (const field of responseFields) {
    if (field in response && response[field] !== null && response[field] !== undefined) {
      const value = response[field];
      
      // If it's a string and not empty, use it
      if (typeof value === 'string' && value.trim()) {
        return value;
      }
      
      // If it's not a string but has content, convert it
      if (value) {
        const converted = safeStringify(value, '');
        if (converted && converted !== 'Empty response' && converted !== 'Empty list') {
          return converted;
        }
      }
    }
  }

  // Check for nested response patterns
  if (response.data?.response) {
    return safeStringify(response.data.response, '');
  }
  
  if (response.body?.message) {
    return safeStringify(response.body.message, '');
  }

  // Check for error responses
  if (response.error || response.errorMessage) {
    const errorMsg = response.error || response.errorMessage;
    return `Error: ${safeStringify(errorMsg, 'Unknown error')}`;
  }

  // Last resort: stringify the entire response
  const fullStringified = safeStringify(response, 'Unable to parse response');
  
  // If it looks like we're about to show a complex object, provide a more helpful message
  if (fullStringified.startsWith('{') && fullStringified.includes('"')) {
    console.warn('Complex response object without standard message field:', response);
    
    // Try to extract something useful from the object
    const keys = Object.keys(response);
    const nonMetaKeys = keys.filter(k => 
      !['metadata', 'session_id', 'tools_used', 'confidence', 'timestamp', 'id'].includes(k)
    );
    
    if (nonMetaKeys.length > 0) {
      // Try the first non-metadata key
      const firstKey = nonMetaKeys[0];
      const value = safeStringify(response[firstKey], '');
      if (value && value !== 'Empty response') {
        return value;
      }
    }
    
    return 'Received response but unable to extract message content';
  }
  
  return fullStringified;
}

/**
 * Validates that a message content is displayable
 * @param content - The content to validate
 * @returns true if the content is valid for display
 */
export function isValidMessageContent(content: any): boolean {
  if (!content) return false;
  
  const stringContent = safeStringify(content, '');
  
  // Check if it's not empty
  if (!stringContent.trim()) return false;
  
  // Check if it's not just an object representation
  if (stringContent === '[object Object]') return false;
  
  // Check if it's not an error placeholder
  if (stringContent.startsWith('[') && stringContent.endsWith(']') && 
      stringContent.includes('Unable to')) return false;
  
  return true;
}

/**
 * Formats message content for display
 * @param content - The content to format
 * @returns Formatted content ready for display
 */
export function formatMessageContent(content: any): string {
  const extracted = extractMessageContent(content);
  
  // Clean up common formatting issues
  let formatted = extracted
    .replace(/^\s+|\s+$/g, '') // Trim whitespace
    .replace(/\\n/g, '\n')      // Convert escaped newlines
    .replace(/\\t/g, '  ')      // Convert tabs to spaces
    .replace(/\\"/g, '"')       // Unescape quotes
    .replace(/\\\\/g, '\\');    // Unescape backslashes
  
  // If it's JSON, try to pretty-print it
  if ((formatted.startsWith('{') || formatted.startsWith('[')) && 
      (formatted.endsWith('}') || formatted.endsWith(']'))) {
    try {
      const parsed = JSON.parse(formatted);
      formatted = JSON.stringify(parsed, null, 2);
    } catch {
      // Not valid JSON, keep as is
    }
  }
  
  return formatted;
}