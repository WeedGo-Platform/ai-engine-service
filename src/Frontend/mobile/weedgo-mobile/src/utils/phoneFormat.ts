/**
 * Phone number formatting utilities
 */

export interface PhoneNumberParts {
  countryCode: string;
  areaCode: string;
  centralOfficeCode: string;
  lineNumber: string;
  formatted: string;
  raw: string;
  isValid: boolean;
}

/**
 * Format a phone number for display (North American format)
 * @param text - Raw phone number string
 * @returns Formatted phone number
 */
export function formatPhoneNumber(text: string): string {
  // Remove all non-numeric characters
  const cleaned = text.replace(/\D/g, '');

  // Handle different lengths
  if (cleaned.length === 0) return '';
  if (cleaned.length <= 3) return cleaned;
  if (cleaned.length <= 6) {
    return `(${cleaned.slice(0, 3)}) ${cleaned.slice(3)}`;
  }
  if (cleaned.length <= 10) {
    return `(${cleaned.slice(0, 3)}) ${cleaned.slice(3, 6)}${cleaned.slice(6) ? '-' + cleaned.slice(6, 10) : ''}`;
  }

  // Handle numbers with country code
  const countryCode = cleaned.slice(0, cleaned.length - 10);
  const areaCode = cleaned.slice(-10, -7);
  const centralOffice = cleaned.slice(-7, -4);
  const lineNumber = cleaned.slice(-4);

  return `+${countryCode} (${areaCode}) ${centralOffice}-${lineNumber}`;
}

/**
 * Format phone number as user types
 * @param text - Current input text
 * @param previousText - Previous input text (to handle backspace)
 * @returns Formatted phone number
 */
export function formatPhoneOnType(text: string, previousText: string = ''): string {
  // If user is deleting, don't auto-format
  if (text.length < previousText.length) {
    return text;
  }

  const cleaned = text.replace(/\D/g, '');

  if (cleaned.length === 0) return '';
  if (cleaned.length <= 3) {
    return cleaned.length === 3 ? `(${cleaned}) ` : cleaned;
  }
  if (cleaned.length <= 6) {
    return `(${cleaned.slice(0, 3)}) ${cleaned.slice(3)}`;
  }
  if (cleaned.length <= 10) {
    const formatted = `(${cleaned.slice(0, 3)}) ${cleaned.slice(3, 6)}`;
    if (cleaned.length > 6) {
      return `${formatted}-${cleaned.slice(6, 10)}`;
    }
    return formatted;
  }

  // Limit to 11 digits (1 + 10 digit phone number)
  const limited = cleaned.slice(0, 11);
  if (limited.length === 11 && limited[0] === '1') {
    return `+1 (${limited.slice(1, 4)}) ${limited.slice(4, 7)}-${limited.slice(7)}`;
  }

  return formatPhoneNumber(limited);
}

/**
 * Parse a phone number into its components
 * @param phoneNumber - Phone number to parse
 * @returns Phone number parts
 */
export function parsePhoneNumber(phoneNumber: string): PhoneNumberParts {
  const cleaned = phoneNumber.replace(/\D/g, '');

  // Default invalid response
  const invalid: PhoneNumberParts = {
    countryCode: '',
    areaCode: '',
    centralOfficeCode: '',
    lineNumber: '',
    formatted: phoneNumber,
    raw: cleaned,
    isValid: false
  };

  // Check for valid North American phone number
  if (cleaned.length === 10) {
    // 10-digit number without country code
    return {
      countryCode: '1',
      areaCode: cleaned.slice(0, 3),
      centralOfficeCode: cleaned.slice(3, 6),
      lineNumber: cleaned.slice(6, 10),
      formatted: formatPhoneNumber(cleaned),
      raw: cleaned,
      isValid: validatePhoneNumber(cleaned)
    };
  } else if (cleaned.length === 11 && cleaned[0] === '1') {
    // 11-digit number with US/Canada country code
    return {
      countryCode: '1',
      areaCode: cleaned.slice(1, 4),
      centralOfficeCode: cleaned.slice(4, 7),
      lineNumber: cleaned.slice(7, 11),
      formatted: formatPhoneNumber(cleaned),
      raw: cleaned,
      isValid: validatePhoneNumber(cleaned.slice(1))
    };
  }

  return invalid;
}

/**
 * Validate a North American phone number
 * @param phoneNumber - Phone number to validate
 * @returns True if valid
 */
export function validatePhoneNumber(phoneNumber: string): boolean {
  const cleaned = phoneNumber.replace(/\D/g, '');

  // Remove country code if present
  const number = cleaned.length === 11 && cleaned[0] === '1'
    ? cleaned.slice(1)
    : cleaned;

  // Must be exactly 10 digits
  if (number.length !== 10) return false;

  // Area code cannot start with 0 or 1
  if (number[0] === '0' || number[0] === '1') return false;

  // Central office code cannot start with 0 or 1
  if (number[3] === '0' || number[3] === '1') return false;

  return true;
}

/**
 * Get the E.164 format of a phone number
 * @param phoneNumber - Phone number to format
 * @param defaultCountryCode - Default country code if not present
 * @returns E.164 formatted number
 */
export function toE164(phoneNumber: string, defaultCountryCode: string = '1'): string {
  const parsed = parsePhoneNumber(phoneNumber);

  if (!parsed.isValid) {
    throw new Error('Invalid phone number');
  }

  const countryCode = parsed.countryCode || defaultCountryCode;
  return `+${countryCode}${parsed.areaCode}${parsed.centralOfficeCode}${parsed.lineNumber}`;
}

/**
 * Mask a phone number for display (e.g., for privacy)
 * @param phoneNumber - Phone number to mask
 * @returns Masked phone number
 */
export function maskPhoneNumber(phoneNumber: string): string {
  const parsed = parsePhoneNumber(phoneNumber);

  if (!parsed.isValid) return phoneNumber;

  return `(${parsed.areaCode}) ***-**${parsed.lineNumber.slice(-2)}`;
}

/**
 * Get a display-friendly version of the phone number
 * @param phoneNumber - Phone number to format
 * @param includeCountryCode - Whether to include country code
 * @returns Display formatted number
 */
export function getDisplayPhone(phoneNumber: string, includeCountryCode: boolean = false): string {
  const parsed = parsePhoneNumber(phoneNumber);

  if (!parsed.isValid) return phoneNumber;

  if (includeCountryCode && parsed.countryCode) {
    return `+${parsed.countryCode} (${parsed.areaCode}) ${parsed.centralOfficeCode}-${parsed.lineNumber}`;
  }

  return `(${parsed.areaCode}) ${parsed.centralOfficeCode}-${parsed.lineNumber}`;
}