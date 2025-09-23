/**
 * Phone number formatting utilities for Canadian phone numbers
 */

// Mask phone number for display (e.g., (416) ***-**23)
export function maskPhoneNumber(phone: string): string {
  const displayPhone = getDisplayPhone(phone);
  if (displayPhone.length < 14) return phone;

  return displayPhone.substring(0, 6) + '***-**' + displayPhone.substring(displayPhone.length - 2);
}

// Format phone number as user types (e.g., (416) 555-0123)
export function formatPhoneOnType(value: string): string {
  // Remove all non-digit characters
  const cleaned = value.replace(/\D/g, '');

  // Limit to 10 digits for North American format
  const limited = cleaned.slice(0, 10);

  if (limited.length === 0) return '';
  if (limited.length <= 3) return `(${limited}`;
  if (limited.length <= 6) return `(${limited.slice(0, 3)}) ${limited.slice(3)}`;
  return `(${limited.slice(0, 3)}) ${limited.slice(3, 6)}-${limited.slice(6)}`;
}

// Validate if phone number is complete and valid
export function validatePhoneNumber(phone: string): boolean {
  const cleaned = phone.replace(/\D/g, '');

  // Check if it's a valid 10-digit North American number
  if (cleaned.length !== 10) return false;

  // Check if area code is valid (first digit can't be 0 or 1)
  const areaCode = cleaned.slice(0, 3);
  if (areaCode[0] === '0' || areaCode[0] === '1') return false;

  // Check if exchange code is valid (first digit can't be 0 or 1)
  const exchangeCode = cleaned.slice(3, 6);
  if (exchangeCode[0] === '0' || exchangeCode[0] === '1') return false;

  return true;
}

// Convert phone number to E.164 format (+1XXXXXXXXXX)
export function toE164(phone: string): string {
  const cleaned = phone.replace(/\D/g, '');

  if (cleaned.length === 10) {
    return `+1${cleaned}`;
  }

  if (cleaned.length === 11 && cleaned[0] === '1') {
    return `+${cleaned}`;
  }

  throw new Error('Invalid phone number format');
}

// Get display format from E.164 or any format
export function getDisplayPhone(phone: string): string {
  const cleaned = phone.replace(/\D/g, '');

  // Remove country code if present
  const withoutCountry = cleaned.length === 11 && cleaned[0] === '1'
    ? cleaned.slice(1)
    : cleaned;

  if (withoutCountry.length !== 10) return phone;

  return `(${withoutCountry.slice(0, 3)}) ${withoutCountry.slice(3, 6)}-${withoutCountry.slice(6)}`;
}

// Parse phone number from various formats
export function parsePhoneNumber(phone: string): {
  countryCode: string;
  areaCode: string;
  exchangeCode: string;
  lineNumber: string;
} | null {
  const cleaned = phone.replace(/\D/g, '');

  let normalized = cleaned;
  let countryCode = '1';

  if (cleaned.length === 11 && cleaned[0] === '1') {
    countryCode = '1';
    normalized = cleaned.slice(1);
  } else if (cleaned.length === 10) {
    normalized = cleaned;
  } else {
    return null;
  }

  return {
    countryCode,
    areaCode: normalized.slice(0, 3),
    exchangeCode: normalized.slice(3, 6),
    lineNumber: normalized.slice(6, 10),
  };
}