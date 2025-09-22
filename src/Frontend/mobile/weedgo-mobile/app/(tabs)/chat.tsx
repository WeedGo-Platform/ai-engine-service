import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Colors } from '@/constants/Colors';

export default function ChatScreen() {
  return (
    <View style={styles.container}>
      <Text style={styles.text}>AI Assistant</Text>
      <Text style={styles.subtext}>Chat assistant coming soon...</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.light.background,
    justifyContent: 'center',
    alignItems: 'center',
  },
  text: {
    fontSize: 24,
    fontWeight: '600',
    color: Colors.light.text,
    marginBottom: 8,
  },
  subtext: {
    fontSize: 14,
    color: Colors.light.gray,
  },
});