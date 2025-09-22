import React from 'react';
import {
  TextInput,
  View,
  Text,
  StyleSheet,
  TextInputProps,
  ViewStyle,
} from 'react-native';
import { useTheme } from '../templates/ThemeProvider';

export interface InputProps extends TextInputProps {
  label?: string;
  error?: string;
  containerStyle?: ViewStyle;
  inputStyle?: ViewStyle;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}

export const Input: React.FC<InputProps> = ({
  label,
  error,
  containerStyle,
  inputStyle,
  leftIcon,
  rightIcon,
  ...textInputProps
}) => {
  const { colors, typography, spacing, borderRadius } = useTheme();

  return (
    <View style={[styles.container, containerStyle]}>
      {label && (
        <Text
          style={[
            styles.label,
            {
              color: colors.textSecondary,
              fontSize: typography.sizes.bodySmall,
              marginBottom: spacing.xs,
            },
          ]}
        >
          {label}
        </Text>
      )}

      <View
        style={[
          styles.inputContainer,
          {
            borderColor: error ? colors.error : colors.border,
            borderRadius: borderRadius.sm,
            paddingHorizontal: spacing.md,
            backgroundColor: colors.surface,
          },
          textInputProps.editable === false && styles.disabled,
        ]}
      >
        {leftIcon && (
          <View style={{ marginRight: spacing.sm }}>{leftIcon}</View>
        )}

        <TextInput
          style={[
            styles.input,
            {
              color: colors.text,
              fontSize: typography.sizes.body,
            },
            inputStyle,
          ]}
          placeholderTextColor={colors.textSecondary}
          {...textInputProps}
        />

        {rightIcon && (
          <View style={{ marginLeft: spacing.sm }}>{rightIcon}</View>
        )}
      </View>

      {error && (
        <Text
          style={[
            styles.error,
            {
              color: colors.error,
              fontSize: typography.sizes.caption,
              marginTop: spacing.xs,
            },
          ]}
        >
          {error}
        </Text>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    marginVertical: 8,
  },
  label: {
    fontWeight: '500',
  },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    borderWidth: 1,
    minHeight: 44,
  },
  input: {
    flex: 1,
    paddingVertical: 10,
  },
  disabled: {
    opacity: 0.6,
  },
  error: {
    marginLeft: 4,
  },
});