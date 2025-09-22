import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import useCartStore from '@/stores/cartStore';

interface CartBadgeProps {
  color?: string;
}

export function CartBadge({ color = '#fff' }: CartBadgeProps) {
  const items = useCartStore((state) => state.items);
  const itemCount = items.reduce((sum, item) => sum + item.quantity, 0);

  if (itemCount === 0) return null;

  return (
    <View style={styles.badge}>
      <Text style={styles.badgeText}>
        {itemCount > 99 ? '99+' : itemCount.toString()}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  badge: {
    position: 'absolute',
    right: -8,
    top: -4,
    backgroundColor: '#ff3b30',
    borderRadius: 10,
    minWidth: 20,
    height: 20,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 4,
    borderWidth: 2,
    borderColor: '#fff',
  },
  badgeText: {
    color: '#fff',
    fontSize: 11,
    fontWeight: 'bold',
  },
});