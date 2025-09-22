import React from 'react';
import {
  View,
  ActivityIndicator,
  Text,
  StyleSheet,
} from 'react-native';
import { HeadlessTheme } from '../Theme';

interface BasicLoadingProps {
  message?: string;
}

export const BasicLoading: React.FC<BasicLoadingProps> = ({ message }) => {
  return (
    <View style={styles.container}>
      <ActivityIndicator
        size="large"
        color={HeadlessTheme.colors.primary}
      />
      {message && <Text style={styles.message}>{message}</Text>}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: HeadlessTheme.spacing.lg,
  },
  message: {
    marginTop: HeadlessTheme.spacing.md,
    fontSize: HeadlessTheme.typography.sizes.body,
    color: HeadlessTheme.colors.textSecondary,
    textAlign: 'center',
  },
});