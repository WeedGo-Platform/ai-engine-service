import { StoreAddress } from '@/types/api.types';

export function formatAddress(address: StoreAddress | undefined): string {
  if (!address) {
    return 'Address not available';
  }

  // Format the full address
  const parts = [];

  if (address.street) {
    parts.push(address.street);
  }

  const cityProvince = [];
  if (address.city) {
    cityProvince.push(address.city);
  }
  if (address.province) {
    cityProvince.push(address.province);
  }

  if (cityProvince.length > 0) {
    parts.push(cityProvince.join(', '));
  }

  if (address.postal_code) {
    parts.push(address.postal_code);
  }

  // Only include country if it's not Canada (assumed default)
  if (address.country && address.country !== 'Canada') {
    parts.push(address.country);
  }

  return parts.join(', ') || 'Address not available';
}

export function formatShortAddress(address: StoreAddress | undefined): string {
  if (!address) {
    return 'Address not available';
  }

  // Format short address (street and city only)
  const parts = [];

  if (address.street) {
    parts.push(address.street);
  }

  if (address.city) {
    parts.push(address.city);
  }

  return parts.join(', ') || 'Address not available';
}