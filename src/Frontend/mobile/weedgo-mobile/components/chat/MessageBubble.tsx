import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { format } from 'date-fns';
import { ChatMessage } from '../../stores/chatStore';
import { ProductMessage } from './ProductMessage';
import { ResponseMetrics } from './ResponseMetrics';
import { QuickActionPills } from './QuickActionPills';
import { Colors } from '@/constants/Colors';
import { Ionicons } from '@expo/vector-icons';

interface MessageBubbleProps {
  message: ChatMessage & {
    response_time?: number;
    token_count?: number;
    quick_actions?: Array<{ label: string; action: string; data?: any }>;
  };
  onQuickActionPress?: (action: string, data?: any) => void;
}

export const MessageBubble = React.memo(({ message, onQuickActionPress }: MessageBubbleProps) => {
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
      {isUser ? (
        <LinearGradient
          colors={['#8B5CF6', '#7C3AED']}
          style={[styles.bubble, styles.userBubble]}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 1 }}
        >
          <Text style={[styles.text, styles.userText]}>
            {message.content}
          </Text>

          {message.status === 'sending' && (
            <View style={styles.statusIndicator}>
              <Ionicons name="time-outline" size={12} color="#fff" />
            </View>
          )}
        </LinearGradient>
      ) : (
        <View style={[
          styles.bubble,
          styles.assistantBubble,
          isSystem && styles.systemBubble,
        ]}>
          <Text style={[
            styles.text,
            styles.assistantText,
            isSystem && styles.systemText,
          ]}>
            {message.content}
          </Text>

          {message.status === 'sending' && (
            <View style={styles.statusIndicator}>
              <Ionicons name="time-outline" size={12} color="#666" />
            </View>
          )}
        </View>
      )}

      {/* Quick Action Pills */}
      {!isUser && message.quick_actions && message.quick_actions.length > 0 && (
        <QuickActionPills
          actions={message.quick_actions}
          onActionPress={onQuickActionPress || (() => {})}
        />
      )}

      {/* Timestamp with inline metadata */}
      <View style={styles.metadata}>
        <Text style={[
          styles.time,
          isUser ? styles.userTime : styles.assistantTime,
        ]}>
          {message.timestamp && !isNaN(new Date(message.timestamp).getTime())
            ? format(new Date(message.timestamp), 'HH:mm')
            : ''}
          {!isUser && message.token_count && `, ${message.token_count}t`}
          {!isUser && message.response_time && `, ${message.response_time.toFixed(1)}s`}
        </Text>
      </View>
    </View>
  );
});

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
    paddingVertical: 12,
    borderRadius: 18,
  },
  userBubble: {
    borderBottomRightRadius: 4,
  },
  assistantBubble: {
    backgroundColor: '#F3F4F6',
    borderBottomLeftRadius: 4,
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
    color: '#1F2937',
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
    color: '#F59E0B',
    fontStyle: 'italic',
  },
  assistantTime: {
    color: '#F59E0B',
    fontStyle: 'italic',
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