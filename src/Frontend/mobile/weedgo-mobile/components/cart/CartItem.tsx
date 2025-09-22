import React from 'react';
import {
  View,
  Text,
  Image,
  TouchableOpacity,
  StyleSheet,
  Animated,
} from 'react-native';
import {
  Swipeable,
  GestureHandlerRootView,
} from 'react-native-gesture-handler';
import { Ionicons } from '@expo/vector-icons';
import useCartStore from '@/stores/cartStore';

interface CartItemProps {
  item: any; // Using any to match the CartItem interface from store
}

export function CartItem({ item }: CartItemProps) {
  const { updateQuantity, removeItem } = useCartStore();

  // Handle quantity changes
  const handleIncrease = () => {
    updateQuantity(item.sku, item.quantity + 1);
  };

  const handleDecrease = () => {
    if (item.quantity > 1) {
      updateQuantity(item.sku, item.quantity - 1);
    } else {
      removeItem(item.sku);
    }
  };

  // Render swipe to delete action
  const renderRightActions = (
    progress: Animated.AnimatedInterpolation<number>,
    dragX: Animated.AnimatedInterpolation<number>
  ) => {
    const translateX = dragX.interpolate({
      inputRange: [-100, 0],
      outputRange: [0, 100],
    });

    return (
      <Animated.View
        style={[
          styles.deleteContainer,
          {
            transform: [{ translateX }],
          },
        ]}
      >
        <TouchableOpacity
          style={styles.deleteButton}
          onPress={() => removeItem(item.sku)}
        >
          <Ionicons name="trash-outline" size={24} color="#fff" />
          <Text style={styles.deleteText}>Delete</Text>
        </TouchableOpacity>
      </Animated.View>
    );
  };

  return (
    <GestureHandlerRootView>
      <Swipeable
        renderRightActions={renderRightActions}
        rightThreshold={40}
      >
        <View style={styles.container}>
          {/* Product Image */}
          <Image
            source={{ uri: item.image || 'https://via.placeholder.com/80' }}
            style={styles.image}
          />

          {/* Product Details */}
          <View style={styles.details}>
            <Text style={styles.name} numberOfLines={2}>
              {item.name}
            </Text>
            {item.size && (
              <Text style={styles.size}>{item.size}</Text>
            )}
            <Text style={styles.price}>
              ${item.price.toFixed(2)} each
            </Text>
          </View>

          {/* Quantity Controls */}
          <View style={styles.quantityContainer}>
            <TouchableOpacity
              style={styles.quantityButton}
              onPress={handleDecrease}
            >
              <Ionicons
                name={item.quantity === 1 ? "trash-outline" : "remove"}
                size={20}
                color="#fff"
              />
            </TouchableOpacity>

            <Text style={styles.quantity}>{item.quantity}</Text>

            <TouchableOpacity
              style={styles.quantityButton}
              onPress={handleIncrease}
            >
              <Ionicons name="add" size={20} color="#fff" />
            </TouchableOpacity>
          </View>

          {/* Item Total */}
          <View style={styles.totalContainer}>
            <Text style={styles.total}>
              ${(item.price * item.quantity).toFixed(2)}
            </Text>
          </View>
        </View>
      </Swipeable>
    </GestureHandlerRootView>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#fff',
    padding: 12,
    marginHorizontal: 16,
    marginVertical: 8,
    borderRadius: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  image: {
    width: 80,
    height: 80,
    borderRadius: 8,
    backgroundColor: '#f0f0f0',
  },
  details: {
    flex: 1,
    marginLeft: 12,
  },
  name: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1a1a1a',
    marginBottom: 4,
  },
  size: {
    fontSize: 14,
    color: '#666',
    marginBottom: 4,
  },
  price: {
    fontSize: 14,
    color: '#00ff00',
    fontWeight: '500',
  },
  quantityContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginRight: 12,
  },
  quantityButton: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: '#00ff00',
    justifyContent: 'center',
    alignItems: 'center',
  },
  quantity: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1a1a1a',
    marginHorizontal: 12,
    minWidth: 20,
    textAlign: 'center',
  },
  totalContainer: {
    alignItems: 'flex-end',
  },
  total: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#1a1a1a',
  },
  deleteContainer: {
    width: 100,
    height: '100%',
    marginVertical: 8,
  },
  deleteButton: {
    flex: 1,
    backgroundColor: '#ff3b30',
    justifyContent: 'center',
    alignItems: 'center',
    marginHorizontal: 16,
    borderRadius: 12,
  },
  deleteText: {
    color: '#fff',
    fontSize: 12,
    marginTop: 4,
  },
});