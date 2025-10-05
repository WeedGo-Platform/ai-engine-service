import React from 'react';
import {
  ScrollView,
  TouchableOpacity,
  Text,
  StyleSheet,
  View,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { useChatStore } from '../../stores/chatStore';
import { Colors } from '@/constants/Colors';

const defaultSuggestions = [
  'I want edibles',
  'I want sativa pre-rolls',
  'Show me indica strains',
  'Best for sleep',
];

export function SuggestionChips() {
  const { sendMessage, suggestions: storeSuggestions } = useChatStore();
  const suggestions = storeSuggestions.length > 0 ? storeSuggestions : defaultSuggestions;

  return (
    <ScrollView
      horizontal
      showsHorizontalScrollIndicator={false}
      contentContainerStyle={styles.scrollContent}
      style={styles.container}
    >
      {suggestions.map((suggestion, index) => (
        <TouchableOpacity
          key={`${suggestion}-${index}`}
          onPress={() => sendMessage(suggestion)}
          activeOpacity={0.8}
        >
          <LinearGradient
            colors={['#8B5CF6', '#7C3AED']}
            style={styles.chip}
            start={{ x: 0, y: 0 }}
            end={{ x: 1, y: 0 }}
          >
            <Text style={styles.chipText}>{suggestion}</Text>
          </LinearGradient>
        </TouchableOpacity>
      ))}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    paddingVertical: 8,
    paddingHorizontal: 12,
  },
  scrollContent: {
    gap: 8,
    paddingRight: 12,
  },
  chip: {
    borderRadius: 16,
    paddingHorizontal: 16,
    paddingVertical: 8,
    minHeight: 36,
  },
  chipText: {
    fontSize: 13,
    fontWeight: '600',
    color: '#FFFFFF',
    textShadowColor: 'rgba(0, 0, 0, 0.1)',
    textShadowOffset: { width: 0, height: 1 },
    textShadowRadius: 2,
    lineHeight: 20,
  },
});