import { StoreAddress } from '@/types/api.types';

export function formatAddress(address: string | StoreAddress | undefined): string {
  if (!address) {
    return 'Address not available';
  }

  // If address is already a string, return it
  if (typeof address === 'string') {
    return address;
  }

  // Format the address object
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

  if (address.country && address.country !== 'Canada') {
    parts.push(address.country);
  }

  return parts.join(', ') || 'Address not available';
}

export function formatShortAddress(address: string | StoreAddress | undefined): string {
  if (!address) {
    return 'Address not available';
  }

  // If address is already a string, return it
  if (typeof address === 'string') {
    return address;
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