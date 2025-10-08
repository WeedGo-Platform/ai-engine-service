/**
 * Special Instructions Modal
 * Cross-platform modal for entering delivery/preparation instructions
 * Replaces Alert.prompt which is iOS-only
 */

import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Modal,
  TextInput,
  KeyboardAvoidingView,
  Platform,
  Animated,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { Colors, BorderRadius, Shadows } from '@/constants/Colors';

interface SpecialInstructionsModalProps {
  visible: boolean;
  onClose: () => void;
  onSave: (instructions: string) => void;
  initialValue?: string;
  deliveryMethod: 'delivery' | 'pickup';
}

export function SpecialInstructionsModal({
  visible,
  onClose,
  onSave,
  initialValue = '',
  deliveryMethod,
}: SpecialInstructionsModalProps) {
  const [instructions, setInstructions] = useState(initialValue);
  const [charCount, setCharCount] = useState(initialValue.length);
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const inputRef = useRef<TextInput>(null);

  const MAX_CHARS = 500;

  useEffect(() => {
    if (visible) {
      setInstructions(initialValue);
      setCharCount(initialValue.length);

      // Animate in
      Animated.timing(fadeAnim, {
        toValue: 1,
        duration: 200,
        useNativeDriver: true,
      }).start();

      // Auto-focus input after a short delay
      setTimeout(() => {
        inputRef.current?.focus();
      }, 300);
    } else {
      // Animate out
      Animated.timing(fadeAnim, {
        toValue: 0,
        duration: 150,
        useNativeDriver: true,
      }).start();
    }
  }, [visible, initialValue]);

  const handleTextChange = (text: string) => {
    if (text.length <= MAX_CHARS) {
      setInstructions(text);
      setCharCount(text.length);
    }
  };

  const handleSave = () => {
    onSave(instructions.trim());
    onClose();
  };

  const handleCancel = () => {
    setInstructions(initialValue);
    setCharCount(initialValue.length);
    onClose();
  };

  const getSuggestions = () => {
    if (deliveryMethod === 'delivery') {
      return [
        'Ring doorbell',
        'Leave at door',
        'Call on arrival',
        'Meet at lobby',
        'Buzzer code: ',
      ];
    } else {
      return [
        'Extra napkins please',
        'No substitutions',
        'Call when ready',
        'Grind finely',
        'Keep separate',
      ];
    }
  };

  const handleSuggestionPress = (suggestion: string) => {
    const newText = instructions ? `${instructions}\n${suggestion}` : suggestion;
    if (newText.length <= MAX_CHARS) {
      setInstructions(newText);
      setCharCount(newText.length);
      inputRef.current?.focus();
    }
  };

  return (
    <Modal
      visible={visible}
      animationType="slide"
      presentationStyle="pageSheet"
      onRequestClose={handleCancel}
      transparent={false}
    >
      <KeyboardAvoidingView
        style={styles.container}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      >
        {/* Header */}
        <View style={styles.header}>
          <TouchableOpacity onPress={handleCancel} style={styles.headerButton}>
            <Text style={styles.cancelText}>Cancel</Text>
          </TouchableOpacity>
          <Text style={styles.title}>Special Instructions</Text>
          <TouchableOpacity
            onPress={handleSave}
            style={styles.headerButton}
            disabled={charCount > MAX_CHARS}
          >
            <Text style={[styles.saveText, charCount > MAX_CHARS && styles.saveTextDisabled]}>
              Save
            </Text>
          </TouchableOpacity>
        </View>

        {/* Content */}
        <Animated.View style={[styles.content, { opacity: fadeAnim }]}>
          {/* Info Banner */}
          <View style={styles.infoCard}>
            <Ionicons name="chatbox-outline" size={20} color={theme.primary} />
            <Text style={styles.infoText}>
              {deliveryMethod === 'delivery'
                ? 'Add any special delivery or preparation instructions for your order.'
                : 'Add any special preparation instructions for your order.'}
            </Text>
          </View>

          {/* Text Input */}
          <View style={styles.inputContainer}>
            <TextInput
              ref={inputRef}
              style={styles.input}
              value={instructions}
              onChangeText={handleTextChange}
              placeholder={
                deliveryMethod === 'delivery'
                  ? 'e.g., Ring doorbell, Leave at door, Buzzer code #123'
                  : 'e.g., Extra napkins, No substitutions, Call when ready'
              }
              placeholderTextColor={theme.disabled}
              multiline
              numberOfLines={8}
              textAlignVertical="top"
              maxLength={MAX_CHARS}
              autoCapitalize="sentences"
              autoCorrect={true}
            />

            {/* Character Counter */}
            <View style={styles.charCounter}>
              <Text
                style={[
                  styles.charCountText,
                  charCount > MAX_CHARS * 0.9 && styles.charCountWarning,
                  charCount >= MAX_CHARS && styles.charCountError,
                ]}
              >
                {charCount}/{MAX_CHARS}
              </Text>
            </View>
          </View>

          {/* Quick Suggestions */}
          <View style={styles.suggestionsContainer}>
            <Text style={styles.suggestionsTitle}>Quick Suggestions</Text>
            <View style={styles.suggestions}>
              {getSuggestions().map((suggestion, index) => (
                <TouchableOpacity
                  key={index}
                  style={styles.suggestionChip}
                  onPress={() => handleSuggestionPress(suggestion)}
                >
                  <Ionicons name="add-circle-outline" size={16} color={theme.primary} />
                  <Text style={styles.suggestionText}>{suggestion}</Text>
                </TouchableOpacity>
              ))}
            </View>
          </View>

          {/* Examples */}
          <View style={styles.examplesContainer}>
            <Text style={styles.examplesTitle}>Examples:</Text>
            {deliveryMethod === 'delivery' ? (
              <>
                <Text style={styles.exampleText}>• "Ring doorbell twice"</Text>
                <Text style={styles.exampleText}>
                  • "Leave at door, call when you arrive"
                </Text>
                <Text style={styles.exampleText}>• "Buzzer code is #1234"</Text>
              </>
            ) : (
              <>
                <Text style={styles.exampleText}>• "Extra napkins please"</Text>
                <Text style={styles.exampleText}>• "Please grind finely"</Text>
                <Text style={styles.exampleText}>• "Call when order is ready"</Text>
              </>
            )}
          </View>
        </Animated.View>
      </KeyboardAvoidingView>
    </Modal>
  );
}

const theme = Colors.dark;

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: theme.background,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingTop: 60,
    paddingBottom: 15,
    paddingHorizontal: 16,
    backgroundColor: theme.glass,
    borderBottomWidth: 1,
    borderBottomColor: theme.glassBorder,
  },
  headerButton: {
    padding: 8,
    minWidth: 60,
  },
  title: {
    fontSize: 18,
    fontWeight: '600',
    color: theme.text,
  },
  cancelText: {
    fontSize: 16,
    color: theme.textSecondary,
  },
  saveText: {
    fontSize: 16,
    fontWeight: '600',
    color: theme.primary,
  },
  saveTextDisabled: {
    color: theme.disabled,
  },
  content: {
    flex: 1,
    padding: 16,
  },
  infoCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(116, 185, 255, 0.1)',
    padding: 12,
    borderRadius: BorderRadius.lg,
    marginBottom: 20,
    gap: 12,
    borderLeftWidth: 3,
    borderLeftColor: theme.primary,
  },
  infoText: {
    flex: 1,
    fontSize: 13,
    color: theme.textSecondary,
    lineHeight: 18,
  },
  inputContainer: {
    backgroundColor: theme.cardBackground,
    borderRadius: BorderRadius.xl,
    borderWidth: 1,
    borderColor: theme.glassBorder,
    marginBottom: 20,
    ...Shadows.small,
  },
  input: {
    fontSize: 15,
    color: theme.text,
    padding: 16,
    minHeight: 150,
    maxHeight: 200,
  },
  charCounter: {
    paddingHorizontal: 16,
    paddingBottom: 12,
    alignItems: 'flex-end',
  },
  charCountText: {
    fontSize: 12,
    color: theme.textSecondary,
  },
  charCountWarning: {
    color: '#FFA500',
  },
  charCountError: {
    color: theme.error,
  },
  suggestionsContainer: {
    marginBottom: 20,
  },
  suggestionsTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: theme.text,
    marginBottom: 12,
  },
  suggestions: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  suggestionChip: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: theme.glass,
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: BorderRadius.full,
    gap: 6,
    borderWidth: 1,
    borderColor: theme.primaryBorder,
  },
  suggestionText: {
    fontSize: 13,
    color: theme.text,
  },
  examplesContainer: {
    backgroundColor: theme.glass,
    padding: 16,
    borderRadius: BorderRadius.lg,
    borderWidth: 1,
    borderColor: theme.glassBorder,
  },
  examplesTitle: {
    fontSize: 13,
    fontWeight: '600',
    color: theme.textSecondary,
    marginBottom: 8,
  },
  exampleText: {
    fontSize: 13,
    color: theme.textSecondary,
    lineHeight: 20,
    marginBottom: 4,
  },
});
