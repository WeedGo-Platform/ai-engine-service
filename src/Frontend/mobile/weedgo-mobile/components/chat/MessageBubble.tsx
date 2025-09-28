import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { format } from 'date-fns';
import { ChatMessage } from '../../stores/chatStore';
import { ProductMessage } from './ProductMessage';
import { Colors } from '@/constants/Colors';
import { Ionicons } from '@expo/vector-icons';

interface MessageBubbleProps {
  message: ChatMessage & {
    response_time?: number;
    token_count?: number;
  };
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.type === 'user';
  const isSystem = message.type === 'system';

  if (message.type === 'product' && message.products) {
    return <ProductMessage products={message.products} message={message.content} />;
  }

  return (
    <View style={[
      styles.container,
      isUser ? styles.userContainer : styles.assistantContainer,
    ]}>
      {message.isVoice && (
        <View style={styles.voiceIndicator}>
          <Ionicons name="mic" size={12} color={isUser ? '#fff' : Colors.light.primary} />
        </View>
      )}

      <View style={[
        styles.bubble,
        isUser ? styles.userBubble : styles.assistantBubble,
        isSystem && styles.systemBubble,
      ]}>
        <Text style={[
          styles.text,
          isUser ? styles.userText : styles.assistantText,
          isSystem && styles.systemText,
        ]}>
          {message.content}
        </Text>

        {message.status === 'sending' && (
          <View style={styles.statusIndicator}>
            <Ionicons name="time-outline" size={12} color={isUser ? '#fff' : '#666'} />
          </View>
        )}
      </View>

      <View style={styles.metadata}>
        <Text style={[
          styles.time,
          isUser ? styles.userTime : styles.assistantTime,
        ]}>
          {message.timestamp && !isNaN(new Date(message.timestamp).getTime())
            ? format(new Date(message.timestamp), 'HH:mm')
            : ''}
        </Text>
        {!isUser && message.response_time !== undefined && (
          <Text style={styles.metaText}>
            {' • '}{message.response_time.toFixed(2)}s
          </Text>
        )}
        {!isUser && message.token_count !== undefined && (
          <Text style={styles.metaText}>
            {' • '}{message.token_count} tokens
          </Text>
        )}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    marginVertical: 4,
    paddingHorizontal: 4,
  },
  userContainer: {
    alignItems: 'flex-end',
  },
  assistantContainer: {
    alignItems: 'flex-start',
  },
  bubble: {
    maxWidth: '80%',
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 18,
  },
  userBubble: {
    backgroundColor: Colors.light.primary,
    borderBottomRightRadius: 4,
  },
  assistantBubble: {
    backgroundColor: '#fff',
    borderBottomLeftRadius: 4,
    borderWidth: 1,
    borderColor: '#e0e0e0',
  },
  systemBubble: {
    backgroundColor: '#f9fafb',
    borderColor: '#e5e7eb',
  },
  text: {
    fontSize: 16,
    lineHeight: 22,
  },
  userText: {
    color: '#fff',
  },
  assistantText: {
    color: Colors.light.text,
  },
  systemText: {
    color: '#6b7280',
    fontStyle: 'italic',
    fontSize: 14,
  },
  time: {
    fontSize: 11,
    marginTop: 4,
    paddingHorizontal: 4,
  },
  userTime: {
    color: '#9ca3af',
  },
  assistantTime: {
    color: '#9ca3af',
  },
  voiceIndicator: {
    position: 'absolute',
    top: -4,
    right: 16,
    backgroundColor: Colors.light.primary,
    borderRadius: 10,
    paddingHorizontal: 6,
    paddingVertical: 2,
    zIndex: 1,
  },
  statusIndicator: {
    position: 'absolute',
    bottom: 4,
    right: 8,
  },
  metadata: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 4,
    paddingHorizontal: 4,
  },
  metaText: {
    fontSize: 11,
    color: '#9ca3af',
  },
});