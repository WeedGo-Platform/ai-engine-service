import React from 'react';
import {
  TouchableOpacity,
  Text,
  StyleSheet,
  ActivityIndicator,
  ViewStyle,
  View,
} from 'react-native';
import { ModernTheme } from '../Theme';

interface FlatButtonProps {
  title: string;
  onPress: () => void;
  variant?: 'primary' | 'secondary' | 'danger' | 'outline';
  loading?: boolean;
  disabled?: boolean;
  fullWidth?: boolean;
  size?: 'small' | 'medium' | 'large';
  icon?: React.ReactNode;
  style?: ViewStyle;
}

export const FlatButton: React.FC<FlatButtonProps> = ({
  title,
  onPress,
  variant = 'primary',
  loading = false,
  disabled = false,
  fullWidth = false,
  size = 'medium',
  icon,
  style,
}) => {
  const theme = ModernTheme;

  const getBackgroundColor = () => {
    if (disabled) return theme.colors.disabled;
    if (variant === 'outline') return 'transparent';

    switch (variant) {
      case 'primary':
        return theme.colors.primary;
      case 'secondary':
        return theme.colors.secondary;
      case 'danger':
        return theme.colors.error;
      default:
        return theme.colors.primary;
    }
  };

  const getTextColor = () => {
    if (disabled && variant !== 'outline') return '#FFFFFF';
    if (disabled && variant === 'outline') return theme.colors.disabled;
    if (variant === 'outline') return theme.colors.primary;
    return '#FFFFFF';
  };

  const getSizeStyle = () => {
    switch (size) {
      case 'small':
        return {
          paddingVertical: 6,
          paddingHorizontal: 12,
          minHeight: 32,
        };
      case 'large':
        return {
          paddingVertical: 14,
          paddingHorizontal: 28,
          minHeight: 48,
        };
      default:
        return {
          paddingVertical: 10,
          paddingHorizontal: 20,
          minHeight: 40,
        };
    }
  };

  const getTextSize = () => {
    switch (size) {
      case 'small':
        return theme.typography.sizes.bodySmall;
      case 'large':
        return 16;
      default:
        return theme.typography.sizes.button;
    }
  };

  const buttonStyle = [
    styles.button,
    getSizeStyle(),
    {
      backgroundColor: getBackgroundColor(),
      borderColor: variant === 'outline' ? theme.colors.primary : undefined,
      borderWidth: variant === 'outline' ? 1 : 0,
    },
    fullWidth && styles.fullWidth,
    disabled && styles.disabled,
    style,
  ];

  return (
    <TouchableOpacity
      onPress={onPress}
      disabled={disabled || loading}
      activeOpacity={0.7}
      style={buttonStyle}
    >
      {loading ? (
        <ActivityIndicator
          color={getTextColor()}
          size={size === 'small' ? 'small' : 'small'}
        />
      ) : (
        <View style={styles.content}>
          {icon && <View style={styles.iconContainer}>{icon}</View>}
          <Text
            style={[
              styles.text,
              {
                color: getTextColor(),
                fontSize: getTextSize(),
              },
            ]}
          >
            {title.toUpperCase()}
          </Text>
        </View>
      )}
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  button: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: ModernTheme.borderRadius.sm,
    ...ModernTheme.shadows.sm,
  },
  fullWidth: {
    width: '100%',
  },
  disabled: {
    opacity: 0.6,
  },
  content: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
  },
  iconContainer: {
    marginRight: 8,
  },
  text: {
    fontWeight: '500',
    letterSpacing: 1,
    textAlign: 'center',
  },
});