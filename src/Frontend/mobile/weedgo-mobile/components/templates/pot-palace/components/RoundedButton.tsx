import React from 'react';
import {
  TouchableOpacity,
  Text,
  StyleSheet,
  ActivityIndicator,
  Animated,
  ViewStyle,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { PotPalaceTheme } from '../Theme';

interface RoundedButtonProps {
  title: string;
  onPress: () => void;
  variant?: 'primary' | 'secondary' | 'danger';
  loading?: boolean;
  disabled?: boolean;
  fullWidth?: boolean;
  size?: 'small' | 'medium' | 'large';
  icon?: React.ReactNode;
  style?: ViewStyle;
}

export const RoundedButton: React.FC<RoundedButtonProps> = ({
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
  const scaleAnim = React.useRef(new Animated.Value(1)).current;
  const theme = PotPalaceTheme;

  const handlePressIn = () => {
    if (!disabled && !loading) {
      Animated.spring(scaleAnim, {
        toValue: 0.95,
        useNativeDriver: true,
      }).start();
    }
  };

  const handlePressOut = () => {
    Animated.spring(scaleAnim, {
      toValue: 1,
      friction: 3,
      tension: 100,
      useNativeDriver: true,
    }).start();
  };

  const getGradientColors = () => {
    if (disabled) return ['#E0E0E0', '#BDBDBD'];

    switch (variant) {
      case 'primary':
        return [theme.colors.primary, '#66BB6A'];
      case 'secondary':
        return [theme.colors.secondary, '#AB47BC'];
      case 'danger':
        return [theme.colors.error, '#EF5350'];
      default:
        return [theme.colors.primary, '#66BB6A'];
    }
  };

  const getSizeStyle = () => {
    switch (size) {
      case 'small':
        return {
          paddingVertical: 8,
          paddingHorizontal: 16,
          minHeight: 36,
        };
      case 'large':
        return {
          paddingVertical: 16,
          paddingHorizontal: 32,
          minHeight: 56,
        };
      default:
        return {
          paddingVertical: 12,
          paddingHorizontal: 24,
          minHeight: 44,
        };
    }
  };

  const getTextSize = () => {
    switch (size) {
      case 'small':
        return theme.typography.sizes.bodySmall;
      case 'large':
        return 18;
      default:
        return theme.typography.sizes.button;
    }
  };

  return (
    <Animated.View
      style={[
        fullWidth && styles.fullWidth,
        { transform: [{ scale: scaleAnim }] },
        style,
      ]}
    >
      <TouchableOpacity
        onPress={onPress}
        onPressIn={handlePressIn}
        onPressOut={handlePressOut}
        disabled={disabled || loading}
        activeOpacity={0.9}
        style={styles.touchable}
      >
        <LinearGradient
          colors={getGradientColors()}
          style={[
            styles.button,
            getSizeStyle(),
            fullWidth && styles.fullWidthButton,
          ]}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 1 }}
        >
          {loading ? (
            <ActivityIndicator
              color="#FFFFFF"
              size={size === 'small' ? 'small' : 'small'}
            />
          ) : (
            <>
              {icon && <>{icon}</>}
              <Text
                style={[
                  styles.text,
                  { fontSize: getTextSize() },
                  icon && styles.textWithIcon,
                ]}
              >
                {title}
              </Text>
            </>
          )}
        </LinearGradient>
      </TouchableOpacity>
    </Animated.View>
  );
};

const styles = StyleSheet.create({
  touchable: {
    borderRadius: PotPalaceTheme.borderRadius.round,
    overflow: 'hidden',
    ...PotPalaceTheme.shadows.md,
  },
  button: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: PotPalaceTheme.borderRadius.round,
  },
  fullWidth: {
    width: '100%',
  },
  fullWidthButton: {
    width: '100%',
  },
  text: {
    color: '#FFFFFF',
    fontWeight: 'bold',
    textAlign: 'center',
  },
  textWithIcon: {
    marginLeft: 8,
  },
});