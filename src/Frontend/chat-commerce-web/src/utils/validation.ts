// Email validation regex
const EMAIL_REGEX = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;

// Phone validation regex (supports various formats)
// Accepts: +1234567890, 123-456-7890, (123) 456-7890, 123.456.7890, 123 456 7890
const PHONE_REGEX = /^[\+]?[(]?[0-9]{1,3}[)]?[-\s\.]?[(]?[0-9]{1,4}[)]?[-\s\.]?[0-9]{1,4}[-\s\.]?[0-9]{1,9}$/;

export type ContactType = 'email' | 'phone' | 'invalid';

export interface ContactInfo {
  type: ContactType;
  value: string;
  formatted?: string;
}

/**
 * Validates if a string is a valid email address
 */
export function isValidEmail(email: string): boolean {
  return EMAIL_REGEX.test(email.trim());
}

/**
 * Validates if a string is a valid phone number
 */
export function isValidPhone(phone: string): boolean {
  const cleaned = phone.replace(/\D/g, '');
  return cleaned.length >= 10 && cleaned.length <= 15 && PHONE_REGEX.test(phone);
}

/**
 * Formats a phone number to a standard format
 */
export function formatPhoneNumber(phone: string): string {
  const cleaned = phone.replace(/\D/g, '');
  
  // Format as US phone number if 10 digits
  if (cleaned.length === 10) {
    return `(${cleaned.slice(0, 3)}) ${cleaned.slice(3, 6)}-${cleaned.slice(6)}`;
  }
  
  // Format as international if 11+ digits (assuming country code)
  if (cleaned.length >= 11) {
    const countryCode = cleaned.slice(0, cleaned.length - 10);
    const number = cleaned.slice(-10);
    return `+${countryCode} (${number.slice(0, 3)}) ${number.slice(3, 6)}-${number.slice(6)}`;
  }
  
  return phone;
}

/**
 * Detects whether input is email or phone and returns formatted info
 */
export function detectContactType(input: string): ContactInfo {
  const trimmed = input.trim();
  
  // Check if it's an email
  if (isValidEmail(trimmed)) {
    return {
      type: 'email',
      value: trimmed.toLowerCase(),
    };
  }
  
  // Check if it's a phone number
  if (isValidPhone(trimmed)) {
    return {
      type: 'phone',
      value: trimmed.replace(/\D/g, ''), // Store clean number
      formatted: formatPhoneNumber(trimmed),
    };
  }
  
  // If it contains @ but invalid email, assume user is trying to enter email
  if (trimmed.includes('@')) {
    return {
      type: 'invalid',
      value: trimmed,
    };
  }
  
  // If it contains only digits/phone chars, assume phone attempt
  const hasDigits = /\d/.test(trimmed);
  if (hasDigits) {
    return {
      type: 'invalid',
      value: trimmed,
    };
  }
  
  return {
    type: 'invalid',
    value: trimmed,
  };
}

/**
 * Get placeholder text based on whether we expect email or phone
 */
export function getContactPlaceholder(allowBoth: boolean = true): string {
  if (allowBoth) {
    return 'Email or Phone (e.g., user@example.com or (555) 123-4567)';
  }
  return 'Email address';
}

/**
 * Get input type based on detected contact type
 */
export function getInputType(contactType: ContactType): string {
  switch (contactType) {
    case 'phone':
      return 'tel';
    case 'email':
      return 'email';
    default:
      return 'text';
  }
}