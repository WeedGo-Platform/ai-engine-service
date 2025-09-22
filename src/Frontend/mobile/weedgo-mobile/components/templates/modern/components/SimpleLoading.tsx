import React from 'react';
import {
  View,
  ActivityIndicator,
  Text,
  StyleSheet,
} from 'react-native';
import { ModernTheme } from '../Theme';

interface SimpleLoadingProps {
  size?: 'small' | 'medium' | 'large';
  message?: string;
  color?: string;
}

export const SimpleLoading: React.FC<SimpleLoadingProps> = ({
  size = 'medium',
  message,
  color,
}) => {
  const theme = ModernTheme;

  const getSize = () => {
    switch (size) {
      case 'small':
        return 'small';
      case 'large':
        return 'large';
      default:
        return 'small';
    }
  };

  return (
    <View style={styles.container}>
      <ActivityIndicator
        size={getSize()}
        color={color || theme.colors.primary}
      />
      {message && (
        <Text style={[styles.message, { color: color || theme.colors.textSecondary }]}>
          {message}
        </Text>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: ModernTheme.spacing.lg,
  },
  message: {
    marginTop: ModernTheme.spacing.md,
    fontSize: ModernTheme.typography.sizes.body,
    textAlign: 'center',
  },
});