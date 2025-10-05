import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Ionicons } from '@expo/vector-icons';

interface ResponseMetricsProps {
  responseTime?: number;
  tokenCount?: number;
  streamingTokens?: number;
  isVoice?: boolean;
}

export const ResponseMetrics: React.FC<ResponseMetricsProps> = ({
  responseTime,
  tokenCount,
  streamingTokens,
  isVoice
}) => {
  // Prefer streaming tokens (live count) over final token count
  const displayTokens = streamingTokens !== undefined ? streamingTokens : tokenCount;

  if (!responseTime && !displayTokens && !isVoice) return null;

  return (
    <View style={styles.container}>
      {isVoice && (
        <View style={styles.badge}>
          <Ionicons name="mic" size={10} color="#EC4899" />
          <Text style={[styles.text, { color: '#EC4899' }]}>Voice</Text>
        </View>
      )}
      {responseTime !== undefined && (
        <View style={styles.badge}>
          <Ionicons name="time-outline" size={10} color="#F59E0B" />
          <Text style={[styles.text, { color: '#F59E0B' }]}>{responseTime.toFixed(1)}s</Text>
        </View>
      )}
      {displayTokens !== undefined && displayTokens > 0 && (
        <View style={styles.badge}>
          <Ionicons name="flash-outline" size={10} color="#F59E0B" />
          <Text style={[styles.text, { color: '#F59E0B' }]}>
            {displayTokens} {displayTokens === 1 ? 'token' : 'tokens'}
          </Text>
        </View>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 4,
    paddingHorizontal: 8,
    paddingVertical: 6,
    gap: 8,
    backgroundColor: 'rgba(0, 0, 0, 0.05)',
    borderRadius: 12,
  },
  badge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 3,
  },
  text: {
    fontSize: 10,
    color: '#9CA3AF',
    fontWeight: '500',
  },
});
