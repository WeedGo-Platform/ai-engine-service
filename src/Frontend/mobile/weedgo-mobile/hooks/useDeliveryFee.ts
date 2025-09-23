import { useState, useEffect } from 'react';
import { DeliveryAddress } from '@/stores/orderStore';
import { deliveryService } from '@/services/api/delivery';

interface DeliveryFeeResult {
  fee: number;
  estimatedTime: string;
  available: boolean;
  distance?: number;
  minimumOrder?: number;
}

export function useDeliveryFee(
  address: DeliveryAddress | null,
  storeId: string
): DeliveryFeeResult {
  const [fee, setFee] = useState(0);
  const [estimatedTime, setEstimatedTime] = useState('30-45 mins');
  const [available, setAvailable] = useState(true);
  const [distance, setDistance] = useState<number | undefined>();
  const [minimumOrder, setMinimumOrder] = useState<number | undefined>();

  useEffect(() => {
    if (!address || !storeId) {
      setFee(0);
      setEstimatedTime('30-45 mins');
      setAvailable(true);
      return;
    }

    const calculateFee = async () => {
      try {
        const response = await deliveryService.calculateFee({
          store_id: storeId,
          delivery_address: address,
        });

        const data = response.data;
        setFee(data.delivery_fee);
        setEstimatedTime(data.estimated_time || '30-45 mins');
        setAvailable(data.available);
        setDistance(data.distance);
        setMinimumOrder(data.minimum_order);
      } catch (error) {
        console.error('Failed to calculate delivery fee:', error);
        // Use fallback calculation if API fails
        calculateFallbackFee(address);
      }
    };

    // Debounce the calculation
    const timer = setTimeout(() => {
      calculateFee();
    }, 500);

    return () => clearTimeout(timer);
  }, [address, storeId]);

  // Fallback fee calculation based on simple rules
  const calculateFallbackFee = (address: DeliveryAddress) => {
    // Basic fee structure
    let baseFee = 5.00; // Base delivery fee

    // Free delivery for orders over $100 (handled in checkout)
    // Distance-based fees would normally be calculated here

    // For now, use a simple zone-based system
    const postalPrefix = address.postal_code?.substring(0, 3).toUpperCase();

    // Downtown Toronto zones (free delivery zone)
    const freeZones = ['M5V', 'M5H', 'M5G', 'M5A', 'M5B', 'M5C', 'M5E', 'M5J', 'M5K', 'M5L', 'M5M', 'M5N', 'M5P', 'M5R', 'M5S', 'M5T', 'M5W', 'M5X'];

    // Nearby zones (standard fee)
    const nearbyZones = ['M4V', 'M4W', 'M4X', 'M4Y', 'M6G', 'M6H', 'M6J', 'M6K', 'M6P', 'M6R'];

    // Far zones (higher fee)
    const farZones = ['M1', 'M2', 'M3', 'M8', 'M9'];

    if (freeZones.includes(postalPrefix || '')) {
      baseFee = 0;
      setEstimatedTime('20-30 mins');
    } else if (nearbyZones.some(zone => postalPrefix?.startsWith(zone))) {
      baseFee = 5.00;
      setEstimatedTime('30-45 mins');
    } else if (farZones.some(zone => postalPrefix?.startsWith(zone))) {
      baseFee = 10.00;
      setEstimatedTime('45-60 mins');
    } else {
      // Outside delivery zone
      setAvailable(false);
      setFee(0);
      setEstimatedTime('Not available');
      return;
    }

    setFee(baseFee);
    setAvailable(true);
  };

  return {
    fee,
    estimatedTime,
    available,
    distance,
    minimumOrder,
  };
}

// Hook for checking if an order qualifies for free delivery
export function useFreeDelivery(subtotal: number, threshold: number = 100): boolean {
  return subtotal >= threshold;
}