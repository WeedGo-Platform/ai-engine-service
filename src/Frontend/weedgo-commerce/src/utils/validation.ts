/**
 * Comprehensive form validation utilities for all forms
 */

import { useState } from 'react';
import { sanitizeInput } from './security';

export type ValidationResult = {
  isValid: boolean;
  errors: Record<string, string>;
};

export type ValidationRule = {
  required?: boolean;
  minLength?: number;
  maxLength?: number;
  pattern?: RegExp;
  custom?: (value: any) => string | null;
  email?: boolean;
  phone?: boolean;
  postalCode?: boolean;
  creditCard?: boolean;
  cvv?: boolean;
  expiryDate?: boolean;
  numeric?: boolean;
  alphanumeric?: boolean;
  url?: boolean;
  date?: boolean;
  minValue?: number;
  maxValue?: number;
  match?: string; // field name to match (for password confirmation)
};

export type ValidationSchema = Record<string, ValidationRule>;

// Validation patterns
const PATTERNS = {
  email: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
  phone: /^(\+\d{1,3}[- ]?)?\d{10}$/,
  canadianPostalCode: /^[A-Z]\d[A-Z] ?\d[A-Z]\d$/i,
  usZipCode: /^\d{5}(-\d{4})?$/,
  creditCard: /^\d{13,19}$/,
  cvv: /^\d{3,4}$/,
  expiryDate: /^(0[1-9]|1[0-2])\/\d{2}$/,
  url: /^https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)$/,
  alphanumeric: /^[a-zA-Z0-9]+$/,
  strongPassword: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]/,
};

// Error messages
const ERROR_MESSAGES = {
  required: 'This field is required',
  minLength: (min: number) => `Must be at least ${min} characters`,
  maxLength: (max: number) => `Must be no more than ${max} characters`,
  email: 'Please enter a valid email address',
  phone: 'Please enter a valid phone number',
  postalCode: 'Please enter a valid postal/zip code',
  creditCard: 'Please enter a valid credit card number',
  cvv: 'Please enter a valid CVV',
  expiryDate: 'Please enter a valid expiry date (MM/YY)',
  numeric: 'Must contain only numbers',
  alphanumeric: 'Must contain only letters and numbers',
  url: 'Please enter a valid URL',
  date: 'Please enter a valid date',
  minValue: (min: number) => `Must be at least ${min}`,
  maxValue: (max: number) => `Must be no more than ${max}`,
  match: 'Fields do not match',
  pattern: 'Invalid format',
  strongPassword: 'Password must contain at least one uppercase letter, one lowercase letter, one number, and one special character',
};

// Luhn algorithm for credit card validation
const luhnCheck = (cardNumber: string): boolean => {
  const digits = cardNumber.replace(/\D/g, '');
  let sum = 0;
  let isEven = false;

  for (let i = digits.length - 1; i >= 0; i--) {
    let digit = parseInt(digits[i], 10);
    if (isEven) {
      digit *= 2;
      if (digit > 9) {
        digit -= 9;
      }
    }
    sum += digit;
    isEven = !isEven;
  }

  return sum % 10 === 0;
};

// Validate a single field
export const validateField = (
  value: any,
  rule: ValidationRule,
  allValues?: Record<string, any>
): string | null => {
  // Sanitize input first
  if (typeof value === 'string') {
    value = sanitizeInput(value);
  }

  // Required check
  if (rule.required && (!value || (typeof value === 'string' && !value.trim()))) {
    return ERROR_MESSAGES.required;
  }

  // Skip other validations if field is empty and not required
  if (!value && !rule.required) {
    return null;
  }

  // String validations
  if (typeof value === 'string') {
    // Min length
    if (rule.minLength && value.length < rule.minLength) {
      return ERROR_MESSAGES.minLength(rule.minLength);
    }

    // Max length
    if (rule.maxLength && value.length > rule.maxLength) {
      return ERROR_MESSAGES.maxLength(rule.maxLength);
    }

    // Email
    if (rule.email && !PATTERNS.email.test(value)) {
      return ERROR_MESSAGES.email;
    }

    // Phone
    if (rule.phone && !PATTERNS.phone.test(value.replace(/[-()\s]/g, ''))) {
      return ERROR_MESSAGES.phone;
    }

    // Postal code (Canadian or US)
    if (rule.postalCode) {
      const isValidPostal = PATTERNS.canadianPostalCode.test(value) || PATTERNS.usZipCode.test(value);
      if (!isValidPostal) {
        return ERROR_MESSAGES.postalCode;
      }
    }

    // Credit card
    if (rule.creditCard) {
      const cleanCard = value.replace(/\D/g, '');
      if (!PATTERNS.creditCard.test(cleanCard) || !luhnCheck(cleanCard)) {
        return ERROR_MESSAGES.creditCard;
      }
    }

    // CVV
    if (rule.cvv && !PATTERNS.cvv.test(value)) {
      return ERROR_MESSAGES.cvv;
    }

    // Expiry date
    if (rule.expiryDate) {
      if (!PATTERNS.expiryDate.test(value)) {
        return ERROR_MESSAGES.expiryDate;
      }
      // Check if date is not in the past
      const [month, year] = value.split('/');
      const expiry = new Date(2000 + parseInt(year), parseInt(month) - 1);
      if (expiry < new Date()) {
        return 'Card has expired';
      }
    }

    // URL
    if (rule.url && !PATTERNS.url.test(value)) {
      return ERROR_MESSAGES.url;
    }

    // Alphanumeric
    if (rule.alphanumeric && !PATTERNS.alphanumeric.test(value)) {
      return ERROR_MESSAGES.alphanumeric;
    }

    // Custom pattern
    if (rule.pattern && !rule.pattern.test(value)) {
      return ERROR_MESSAGES.pattern;
    }

    // Match another field (e.g., password confirmation)
    if (rule.match && allValues && value !== allValues[rule.match]) {
      return ERROR_MESSAGES.match;
    }
  }

  // Numeric validations
  if (rule.numeric && isNaN(Number(value))) {
    return ERROR_MESSAGES.numeric;
  }

  // Number validations
  if (typeof value === 'number' || rule.numeric) {
    const numValue = Number(value);

    if (rule.minValue !== undefined && numValue < rule.minValue) {
      return ERROR_MESSAGES.minValue(rule.minValue);
    }

    if (rule.maxValue !== undefined && numValue > rule.maxValue) {
      return ERROR_MESSAGES.maxValue(rule.maxValue);
    }
  }

  // Date validation
  if (rule.date) {
    const date = new Date(value);
    if (isNaN(date.getTime())) {
      return ERROR_MESSAGES.date;
    }
  }

  // Custom validation
  if (rule.custom) {
    return rule.custom(value);
  }

  return null;
};

// Validate entire form
export const validateForm = (
  values: Record<string, any>,
  schema: ValidationSchema
): ValidationResult => {
  const errors: Record<string, string> = {};
  let isValid = true;

  Object.keys(schema).forEach(fieldName => {
    const error = validateField(values[fieldName], schema[fieldName], values);
    if (error) {
      errors[fieldName] = error;
      isValid = false;
    }
  });

  return { isValid, errors };
};

// Form-specific validation schemas
export const ValidationSchemas = {
  // Login form
  login: {
    email: {
      required: true,
      email: true,
    },
    password: {
      required: true,
      minLength: 6,
    },
  } as ValidationSchema,

  // Registration form
  register: {
    firstName: {
      required: true,
      minLength: 2,
      maxLength: 50,
    },
    lastName: {
      required: true,
      minLength: 2,
      maxLength: 50,
    },
    email: {
      required: true,
      email: true,
    },
    password: {
      required: true,
      minLength: 8,
      pattern: PATTERNS.strongPassword,
      custom: (value: string) => {
        if (!PATTERNS.strongPassword.test(value)) {
          return ERROR_MESSAGES.strongPassword;
        }
        return null;
      },
    },
    confirmPassword: {
      required: true,
      match: 'password',
    },
    phone: {
      required: true,
      phone: true,
    },
    dateOfBirth: {
      required: true,
      date: true,
      custom: (value: string) => {
        const dob = new Date(value);
        const age = (Date.now() - dob.getTime()) / (365.25 * 24 * 60 * 60 * 1000);
        if (age < 19) {
          return 'You must be 19 or older to register';
        }
        return null;
      },
    },
    acceptTerms: {
      required: true,
      custom: (value: boolean) => {
        if (!value) {
          return 'You must accept the terms and conditions';
        }
        return null;
      },
    },
  } as ValidationSchema,

  // Checkout form
  checkout: {
    email: {
      required: true,
      email: true,
    },
    firstName: {
      required: true,
      minLength: 2,
      maxLength: 50,
    },
    lastName: {
      required: true,
      minLength: 2,
      maxLength: 50,
    },
    phone: {
      required: true,
      phone: true,
    },
    address: {
      required: true,
      minLength: 5,
      maxLength: 100,
    },
    city: {
      required: true,
      minLength: 2,
      maxLength: 50,
    },
    province: {
      required: true,
    },
    postalCode: {
      required: true,
      postalCode: true,
    },
    deliveryDate: {
      required: true,
      date: true,
      custom: (value: string) => {
        const date = new Date(value);
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        if (date < today) {
          return 'Delivery date cannot be in the past';
        }
        return null;
      },
    },
    deliveryTime: {
      required: true,
    },
  } as ValidationSchema,

  // Payment form
  payment: {
    cardNumber: {
      required: true,
      creditCard: true,
    },
    cardholderName: {
      required: true,
      minLength: 3,
      maxLength: 50,
    },
    expiryDate: {
      required: true,
      expiryDate: true,
    },
    cvv: {
      required: true,
      cvv: true,
    },
    billingAddress: {
      required: true,
      minLength: 5,
      maxLength: 100,
    },
    billingCity: {
      required: true,
      minLength: 2,
      maxLength: 50,
    },
    billingPostalCode: {
      required: true,
      postalCode: true,
    },
  } as ValidationSchema,

  // Profile update form
  profileUpdate: {
    firstName: {
      minLength: 2,
      maxLength: 50,
    },
    lastName: {
      minLength: 2,
      maxLength: 50,
    },
    phone: {
      phone: true,
    },
    email: {
      email: true,
    },
  } as ValidationSchema,

  // Address form
  address: {
    label: {
      required: true,
      minLength: 2,
      maxLength: 30,
    },
    street: {
      required: true,
      minLength: 5,
      maxLength: 100,
    },
    unit: {
      maxLength: 20,
    },
    city: {
      required: true,
      minLength: 2,
      maxLength: 50,
    },
    province: {
      required: true,
    },
    postalCode: {
      required: true,
      postalCode: true,
    },
    instructions: {
      maxLength: 200,
    },
  } as ValidationSchema,

  // Password change form
  passwordChange: {
    currentPassword: {
      required: true,
      minLength: 6,
    },
    newPassword: {
      required: true,
      minLength: 8,
      pattern: PATTERNS.strongPassword,
      custom: (value: string) => {
        if (!PATTERNS.strongPassword.test(value)) {
          return ERROR_MESSAGES.strongPassword;
        }
        return null;
      },
    },
    confirmNewPassword: {
      required: true,
      match: 'newPassword',
    },
  } as ValidationSchema,

  // Product review form
  productReview: {
    rating: {
      required: true,
      numeric: true,
      minValue: 1,
      maxValue: 5,
    },
    title: {
      required: true,
      minLength: 3,
      maxLength: 100,
    },
    comment: {
      required: true,
      minLength: 10,
      maxLength: 1000,
    },
    wouldRecommend: {
      required: true,
    },
  } as ValidationSchema,

  // Contact form
  contact: {
    name: {
      required: true,
      minLength: 2,
      maxLength: 100,
    },
    email: {
      required: true,
      email: true,
    },
    subject: {
      required: true,
      minLength: 5,
      maxLength: 100,
    },
    message: {
      required: true,
      minLength: 10,
      maxLength: 2000,
    },
  } as ValidationSchema,
};

// Custom hook for form validation
export const useFormValidation = (
  initialValues: Record<string, any>,
  schema: ValidationSchema
) => {
  const [values, setValues] = useState(initialValues);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [touched, setTouched] = useState<Record<string, boolean>>({});

  const validateSingleField = (name: string, value: any) => {
    const fieldSchema = schema[name];
    if (!fieldSchema) return;

    const error = validateField(value, fieldSchema, values);
    setErrors(prev => ({
      ...prev,
      [name]: error || '',
    }));
  };

  const handleChange = (name: string, value: any) => {
    setValues(prev => ({
      ...prev,
      [name]: value,
    }));

    if (touched[name]) {
      validateSingleField(name, value);
    }
  };

  const handleBlur = (name: string) => {
    setTouched(prev => ({
      ...prev,
      [name]: true,
    }));
    validateSingleField(name, values[name]);
  };

  const handleSubmit = (callback: () => void) => {
    const validation = validateForm(values, schema);
    setErrors(validation.errors);

    // Mark all fields as touched
    const allTouched: Record<string, boolean> = {};
    Object.keys(schema).forEach(key => {
      allTouched[key] = true;
    });
    setTouched(allTouched);

    if (validation.isValid) {
      callback();
    }
  };

  const reset = () => {
    setValues(initialValues);
    setErrors({});
    setTouched({});
  };

  return {
    values,
    errors,
    touched,
    handleChange,
    handleBlur,
    handleSubmit,
    reset,
    isValid: Object.keys(errors).length === 0,
  };
};