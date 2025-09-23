import React from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Animated,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';

interface DeliveryMethodToggleProps {
  value: 'delivery' | 'pickup';
  onChange: (value: 'delivery' | 'pickup') => void;
  deliveryAvailable?: boolean;
}

export function DeliveryMethodToggle({
  value,
  onChange,
  deliveryAvailable = true,
}: DeliveryMethodToggleProps) {
  const slideAnim = React.useRef(new Animated.Value(value === 'delivery' ? 0 : 1)).current;

  React.useEffect(() => {
    Animated.spring(slideAnim, {
      toValue: value === 'delivery' ? 0 : 1,
      useNativeDriver: false,
      friction: 8,
      tension: 65,
    }).start();
  }, [value, slideAnim]);

  const handlePress = (method: 'delivery' | 'pickup') => {
    if (method === 'delivery' && !deliveryAvailable) return;
    onChange(method);
  };

  const indicatorPosition = slideAnim.interpolate({
    inputRange: [0, 1],
    outputRange: ['2%', '48%'],
  });

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Delivery Method</Text>

      <View style={styles.toggleContainer}>
        <Animated.View
          style={[
            styles.indicator,
            {
              left: indicatorPosition,
            },
          ]}
        />

        <TouchableOpacity
          style={[styles.option, value === 'delivery' && styles.optionActive]}
          onPress={() => handlePress('delivery')}
          disabled={!deliveryAvailable}
        >
          <Ionicons
            name="car-outline"
            size={24}
            color={value === 'delivery' ? '#27AE60' : '#666'}
          />
          <Text style={[
            styles.optionText,
            value === 'delivery' && styles.optionTextActive,
            !deliveryAvailable && styles.optionTextDisabled
          ]}>
            Delivery
          </Text>
          {!deliveryAvailable && (
            <Text style={styles.unavailableText}>Unavailable</Text>
          )}
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.option, value === 'pickup' && styles.optionActive]}
          onPress={() => handlePress('pickup')}
        >
          <Ionicons
            name="storefront-outline"
            size={24}
            color={value === 'pickup' ? '#27AE60' : '#666'}
          />
          <Text style={[
            styles.optionText,
            value === 'pickup' && styles.optionTextActive
          ]}>
            Pickup
          </Text>
        </TouchableOpacity>
      </View>

      {value === 'delivery' && deliveryAvailable && (
        <View style={styles.infoBox}>
          <Ionicons name="information-circle" size={16} color="#27AE60" />
          <Text style={styles.infoText}>
            Free delivery on orders over $100
          </Text>
        </View>
      )}

      {value === 'pickup' && (
        <View style={styles.infoBox}>
          <Ionicons name="information-circle" size={16} color="#27AE60" />
          <Text style={styles.infoText}>
            Save on delivery fees with store pickup
          </Text>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#FFF',
    padding: 16,
  },
  title: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    marginBottom: 12,
  },
  toggleContainer: {
    flexDirection: 'row',
    backgroundColor: '#F8F9FA',
    borderRadius: 12,
    padding: 4,
    position: 'relative',
  },
  indicator: {
    position: 'absolute',
    width: '46%',
    height: '92%',
    backgroundColor: '#FFF',
    borderRadius: 10,
    top: '4%',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  option: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 12,
    gap: 8,
    zIndex: 1,
  },
  optionActive: {
    // Active styles handled by text color
  },
  optionText: {
    fontSize: 15,
    fontWeight: '500',
    color: '#666',
  },
  optionTextActive: {
    color: '#27AE60',
    fontWeight: '600',
  },
  optionTextDisabled: {
    color: '#CCC',
  },
  unavailableText: {
    fontSize: 10,
    color: '#FF6B6B',
    position: 'absolute',
    bottom: 2,
  },
  infoBox: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F0FFF4',
    padding: 12,
    borderRadius: 8,
    marginTop: 12,
    gap: 8,
  },
  infoText: {
    fontSize: 13,
    color: '#27AE60',
    flex: 1,
  },
});