/**
 * Currency formatting utilities for consistent display across the application
 */

/**
 * Format a number as USD currency
 * @param value - The numeric value to format
 * @param options - Optional formatting options
 * @returns Formatted currency string (e.g., "$1,234.56")
 */
export const formatCurrency = (
  value: number | string | null | undefined,
  options: {
    minimumFractionDigits?: number;
    maximumFractionDigits?: number;
    showSign?: boolean;
  } = {}
): string => {
  const {
    minimumFractionDigits = 2,
    maximumFractionDigits = 2,
    showSign = false,
  } = options;

  // Handle null/undefined
  if (value === null || value === undefined) {
    return '$0.00';
  }

  // Convert to number
  const numValue = typeof value === 'string' ? parseFloat(value) : value;

  // Handle NaN
  if (isNaN(numValue)) {
    return '$0.00';
  }

  // Format with Intl.NumberFormat for proper thousand separators
  const formatted = new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits,
    maximumFractionDigits,
  }).format(Math.abs(numValue));

  // Add sign if requested or if negative
  if (numValue < 0) {
    return `-${formatted}`;
  } else if (showSign && numValue > 0) {
    return `+${formatted}`;
  }

  return formatted;
};

/**
 * Format currency for input fields (without thousand separators for easier editing)
 * @param value - The numeric value to format
 * @returns Formatted string for input (e.g., "1234.56")
 */
export const formatCurrencyInput = (
  value: number | string | null | undefined
): string => {
  if (value === null || value === undefined || value === '') {
    return '';
  }

  const numValue = typeof value === 'string' ? parseFloat(value) : value;

  if (isNaN(numValue)) {
    return '';
  }

  return numValue.toFixed(2);
};

/**
 * Parse currency input string to number
 * @param value - The input string (may contain $, commas, etc.)
 * @returns Parsed number value
 */
export const parseCurrencyInput = (value: string): number => {
  // Remove all non-numeric characters except decimal point and minus sign
  const cleaned = value.replace(/[^0-9.-]/g, '');
  const parsed = parseFloat(cleaned);
  return isNaN(parsed) ? 0 : parsed;
};

/**
 * Format percentage value
 * @param value - The numeric value (e.g., 0.15 for 15%)
 * @param decimals - Number of decimal places
 * @returns Formatted percentage string (e.g., "15.0%")
 */
export const formatPercentage = (
  value: number | null | undefined,
  decimals: number = 1
): string => {
  if (value === null || value === undefined || isNaN(value)) {
    return '0%';
  }

  return `${(value * 100).toFixed(decimals)}%`;
};

/**
 * Format compact currency (for large values: $1.2K, $3.5M, etc.)
 * @param value - The numeric value to format
 * @returns Compact formatted currency string
 */
export const formatCurrencyCompact = (
  value: number | null | undefined
): string => {
  if (value === null || value === undefined || isNaN(value)) {
    return '$0';
  }

  const absValue = Math.abs(value);
  const sign = value < 0 ? '-' : '';

  if (absValue >= 1000000) {
    return `${sign}$${(absValue / 1000000).toFixed(1)}M`;
  } else if (absValue >= 1000) {
    return `${sign}$${(absValue / 1000).toFixed(1)}K`;
  } else {
    return `${sign}$${absValue.toFixed(0)}`;
  }
};
