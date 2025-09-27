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
import { LinearGradient } from 'expo-linear-gradient';
import useCartStore from '@/stores/cartStore';
import { Colors, BorderRadius, Shadows, Gradients } from '@/constants/Colors';

const isDark = true;
const theme = isDark ? Colors.dark : Colors.light;

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
          onPress={() => removeItem(item.sku)}
          style={{ flex: 1 }}
        >
          <LinearGradient
            colors={['#FF6B9D', '#FF5587']}
            style={styles.deleteButton}
            start={{ x: 0, y: 0 }}
            end={{ x: 1, y: 1 }}
          >
            <Ionicons name="trash-outline" size={24} color="#fff" />
            <Text style={styles.deleteText}>Delete</Text>
          </LinearGradient>
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
          <View style={styles.imageContainer}>
            <Image
              source={
                item.image && item.image.trim() !== ''
                  ? { uri: item.image }
                  : require('@/assets/icon.png')
              }
              style={styles.image}
              resizeMode={item.image && item.image.trim() !== '' ? "cover" : "contain"}
              defaultSource={require('@/assets/icon.png')}
              onError={() => {
                // Image failed to load, but defaultSource will handle it
              }}
            />
          </View>

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
              onPress={handleDecrease}
              activeOpacity={0.7}
            >
              <LinearGradient
                colors={item.quantity === 1 ? ['#FF6B9D', '#FF5587'] : ['#74B9FF', '#8BE9FD']}
                style={styles.quantityButton}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 1 }}
              >
                <Ionicons
                  name={item.quantity === 1 ? "trash-outline" : "remove"}
                  size={20}
                  color="#fff"
                />
              </LinearGradient>
            </TouchableOpacity>

            <Text style={styles.quantity}>{item.quantity}</Text>

            <TouchableOpacity
              onPress={handleIncrease}
              activeOpacity={0.7}
            >
              <LinearGradient
                colors={['#74B9FF', '#8BE9FD']}
                style={styles.quantityButton}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 1 }}
              >
                <Ionicons name="add" size={20} color="#fff" />
              </LinearGradient>
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
    backgroundColor: theme.glass,
    padding: 12,
    marginHorizontal: 16,
    marginVertical: 8,
    borderRadius: BorderRadius.xl,
    borderWidth: 1,
    borderColor: theme.glassBorder,
    ...Shadows.medium,
  },
  imageContainer: {
    width: 80,
    height: 80,
    borderRadius: BorderRadius.lg,
    overflow: 'hidden',
    backgroundColor: theme.inputBackground,
    borderWidth: 1,
    borderColor: theme.glassBorder,
  },
  image: {
    width: '100%',
    height: '100%',
  },
  details: {
    flex: 1,
    marginLeft: 12,
  },
  name: {
    fontSize: 16,
    fontWeight: '600',
    color: theme.text,
    marginBottom: 4,
  },
  size: {
    fontSize: 14,
    color: theme.textSecondary,
    marginBottom: 4,
  },
  price: {
    fontSize: 14,
    color: theme.textSecondary,
    fontWeight: '600',
  },
  quantityContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginRight: 12,
  },
  quantityButton: {
    width: 32,
    height: 32,
    borderRadius: BorderRadius.full,
    justifyContent: 'center',
    alignItems: 'center',
    ...Shadows.small,
  },
  quantity: {
    fontSize: 16,
    fontWeight: '700',
    color: theme.text,
    marginHorizontal: 12,
    minWidth: 20,
    textAlign: 'center',
  },
  totalContainer: {
    alignItems: 'flex-end',
  },
  total: {
    fontSize: 18,
    fontWeight: '800',
    color: theme.text,
  },
  deleteContainer: {
    width: 100,
    height: '100%',
    marginVertical: 8,
  },
  deleteButton: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    marginHorizontal: 16,
    borderRadius: BorderRadius.xl,
    ...Shadows.medium,
  },
  deleteText: {
    color: '#fff',
    fontSize: 12,
    marginTop: 4,
  },
});