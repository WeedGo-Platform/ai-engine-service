import React from 'react';
import {
  ScrollView,
  TouchableOpacity,
  Text,
  StyleSheet,
  View,
} from 'react-native';
import { useChatStore } from '../../stores/chatStore';
import { Colors } from '@/constants/Colors';

const defaultSuggestions = [
  'Show me indica strains',
  'What has high THC?',
  'Best for sleep',
  'New arrivals',
  'Edibles under $30',
  'CBD products',
  'Vape cartridges',
  'Daily deals',
];

export function SuggestionChips() {
  const { sendMessage, suggestions: storeSuggestions } = useChatStore();
  const suggestions = storeSuggestions.length > 0 ? storeSuggestions : defaultSuggestions;

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Suggestions:</Text>
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={styles.scrollContent}
      >
        {suggestions.map((suggestion, index) => (
          <TouchableOpacity
            key={`${suggestion}-${index}`}
            style={styles.chip}
            onPress={() => sendMessage(suggestion)}
            activeOpacity={0.7}
          >
            <Text style={styles.chipText}>{suggestion}</Text>
          </TouchableOpacity>
        ))}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    paddingVertical: 12,
  },
  title: {
    fontSize: 12,
    color: '#9ca3af',
    marginBottom: 8,
    paddingHorizontal: 20,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  scrollContent: {
    paddingHorizontal: 16,
  },
  chip: {
    backgroundColor: '#fff',
    borderWidth: 1,
    borderColor: '#e0e0e0',
    borderRadius: 18,
    paddingHorizontal: 14,
    paddingVertical: 8,
    marginHorizontal: 4,
  },
  chipText: {
    fontSize: 14,
    color: Colors.light.text,
  },
});