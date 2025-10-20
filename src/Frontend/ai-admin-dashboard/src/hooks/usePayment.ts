/**
 * usePayment Hook
 *
 * Convenience re-export of the usePayment hook from PaymentContext.
 * This allows for cleaner imports throughout the application.
 *
 * @example
 * // Instead of:
 * import { usePayment } from '../contexts/PaymentContext';
 *
 * // Use:
 * import { usePayment } from '../hooks/usePayment';
 */

export { usePayment } from '../contexts/PaymentContext';
export type { PaymentState, PaymentContextValue, LoadingState, ErrorState } from '../contexts/PaymentContext';
