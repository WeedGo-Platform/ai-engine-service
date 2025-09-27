import React, { useEffect, useRef, useState, useCallback } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  FlatList,
  KeyboardAvoidingView,
  Platform,
  SafeAreaView,
  ActivityIndicator,
  ScrollView,
  StyleSheet,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { useChatStore } from '../../stores/chatStore';
import { MessageBubble } from '../../components/chat/MessageBubble';
import { TypingIndicator } from '../../components/chat/TypingIndicator';
import { SuggestionChips } from '../../components/chat/SuggestionChips';
import { useStreamingTranscription } from '../../hooks/useStreamingTranscription';
import { VoiceRecordingButton } from '../../components/chat/VoiceRecordingButton';
import { StreamingTranscriptUI } from '../../components/StreamingTranscriptUI';
import { Colors, GlassStyles, BorderRadius, Shadows } from '@/constants/Colors';
import { useTheme } from '@/contexts/ThemeContext';
import { glassChatStyles as staticStyles } from '@/constants/GlassmorphismStyles';
import { BlurView } from 'expo-blur';

export default function ChatScreen() {
  const [inputText, setInputText] = useState('');
  const [isTTSEnabled, setIsTTSEnabled] = useState(true);
  const [showTranscript, setShowTranscript] = useState(false);
  const [pendingTranscript, setPendingTranscript] = useState('');
  const flatListRef = useRef<FlatList>(null);
  const inputRef = useRef<TextInput>(null);
  const { theme, isDark } = useTheme();
  const silenceTimerRef = useRef<NodeJS.Timeout | null>(null);

  const {
    messages,
    isTyping,
    isConnected,
    connect,
    sendMessage: sendChatMessage,
    markAsRead,
    clearChat,
  } = useChatStore();

  const styles = React.useMemo(() => ({
    ...staticStyles,
    gradientContainer: { flex: 1 },
    container: { ...staticStyles.container, backgroundColor: 'transparent' },
    header: {
      flexDirection: 'row' as const,
      justifyContent: 'space-between' as const,
      alignItems: 'center' as const,
      padding: 16,
      paddingTop: Platform.OS === 'ios' ? 48 : 16,
      backgroundColor: 'rgba(255,255,255,0.05)',
      borderBottomWidth: 0.5,
      borderBottomColor: 'rgba(255,255,255,0.1)',
    },
    headerTitle: {
      fontSize: 20,
      fontWeight: '600' as const,
      color: '#fff',
    },
    headerActions: {
      flexDirection: 'row' as const,
      alignItems: 'center' as const,
      gap: 16,
    },
    messagesList: {
      paddingHorizontal: 16,
      paddingBottom: 20,
      paddingTop: 8,
    },
    transcriptBox: {
      marginHorizontal: 16,
      marginBottom: 8,
      backgroundColor: 'rgba(255, 255, 255, 0.95)',
      borderRadius: 12,
      maxHeight: 120,
      shadowColor: '#000',
      shadowOffset: { width: 0, height: -2 },
      shadowOpacity: 0.1,
      shadowRadius: 4,
      elevation: 3,
    },
  }), [theme, isDark]);

  // Handle sending final transcript to chat
  const handleSendTranscript = useCallback((text: string) => {
    if (text.trim()) {
      sendChatMessage(text, true);
      setShowTranscript(false);
      setPendingTranscript('');
    }
  }, [sendChatMessage]);

  // Initialize streaming transcription with callbacks
  const {
    isRecording,
    isConnected: wsConnected,
    partialTranscript,
    partialConfidence,
    finalTranscript,
    connectionQuality,
    latencyMs,
    error,
    startRecording: startStreamingRecording,
    stopRecording: stopStreamingRecording,
    clearTranscripts,
    connectWebSocket,
    disconnect,
  } = useStreamingTranscription({
    chunkDurationMs: 250,
    enableWebRTC: false,
    autoReconnect: true,
  });

  // Auto-stop on 3 seconds of silence
  useEffect(() => {
    if (isRecording && !partialTranscript && pendingTranscript) {
      // Start silence timer
      if (!silenceTimerRef.current) {
        silenceTimerRef.current = setTimeout(() => {
          console.log('[CHAT] Auto-stopping due to 3 seconds of silence');
          handleStopRecording();
        }, 3000);
      }
    } else if (partialTranscript) {
      // Clear silence timer when speech detected
      if (silenceTimerRef.current) {
        clearTimeout(silenceTimerRef.current);
        silenceTimerRef.current = null;
      }
    }

    return () => {
      if (silenceTimerRef.current) {
        clearTimeout(silenceTimerRef.current);
        silenceTimerRef.current = null;
      }
    };
  }, [isRecording, partialTranscript, pendingTranscript]);

  // Handle partial transcripts - accumulate them
  useEffect(() => {
    if (partialTranscript) {
      setPendingTranscript(partialTranscript);
    }
  }, [partialTranscript]);

  // Handle final transcripts (sent on pause detection)
  useEffect(() => {
    if (finalTranscript && finalTranscript.trim()) {
      // Check for sentence ending punctuation
      const endsWithPunctuation = /[.!?]$/.test(finalTranscript.trim());

      if (endsWithPunctuation) {
        // Send immediately if it's a complete sentence
        handleSendTranscript(finalTranscript);
        clearTranscripts();
        setPendingTranscript('');
      } else {
        // Keep accumulating if not a complete sentence
        setPendingTranscript(finalTranscript);
      }
    }
  }, [finalTranscript, handleSendTranscript, clearTranscripts]);

  useEffect(() => {
    // Connect to chat when screen loads
    connect();
    markAsRead();

    return () => {
      // Mark as read when leaving
      markAsRead();
      disconnect();
    };
  }, []);

  useEffect(() => {
    // Scroll to bottom when new messages arrive
    if (messages.length > 0) {
      setTimeout(() => {
        flatListRef.current?.scrollToEnd({ animated: true });
      }, 100);
    }
  }, [messages]);

  const handleSendMessage = (text: string, fromVoice: boolean = false) => {
    if (text.trim()) {
      sendChatMessage(text, fromVoice);
      setInputText('');
    }
  };

  const handleSend = () => {
    if (inputText.trim()) {
      handleSendMessage(inputText);
    }
  };

  const handleStartRecording = async () => {
    try {
      setShowTranscript(true);
      setPendingTranscript('');
      clearTranscripts();

      // Connect WebSocket if not connected
      if (!wsConnected) {
        await connectWebSocket();
      }

      await startStreamingRecording();
    } catch (error) {
      console.error('[CHAT] Failed to start recording:', error);
      setShowTranscript(false);
    }
  };

  const handleStopRecording = async () => {
    try {
      await stopStreamingRecording();

      // Send any pending transcript
      if (pendingTranscript && pendingTranscript.trim()) {
        handleSendTranscript(pendingTranscript);
      }

      // Clear state
      clearTranscripts();
      setPendingTranscript('');
      setShowTranscript(false);

      // Clear silence timer
      if (silenceTimerRef.current) {
        clearTimeout(silenceTimerRef.current);
        silenceTimerRef.current = null;
      }
    } catch (error) {
      console.error('[CHAT] Failed to stop recording:', error);
    }
  };

  const handleVoicePress = async () => {
    if (isRecording) {
      await handleStopRecording();
    } else {
      await handleStartRecording();
    }
  };

  const handleSpeakerToggle = () => {
    setIsTTSEnabled(!isTTSEnabled);
  };

  const renderMessage = ({ item, index }: { item: any; index: number }) => (
    <MessageBubble
      message={item}
      onSpeak={isTTSEnabled ? undefined : null}
    />
  );

  const renderFooter = () => {
    if (isTyping) {
      return <TypingIndicator />;
    }
    return null;
  };

  return (
    <LinearGradient
      colors={isDark ? ['#1a1a2e', '#16213e'] : ['#667eea', '#764ba2']}
      style={styles.gradientContainer}
    >
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>AI Assistant</Text>
        <View style={styles.headerActions}>
          <TouchableOpacity onPress={handleSpeakerToggle}>
            <Ionicons
              name={isTTSEnabled ? 'volume-high' : 'volume-mute'}
              size={24}
              color="#fff"
            />
          </TouchableOpacity>
          <TouchableOpacity onPress={clearChat}>
            <Ionicons name="trash-outline" size={24} color="#fff" />
          </TouchableOpacity>
        </View>
      </View>

      <KeyboardAvoidingView
        style={styles.keyboardAvoid}
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        keyboardVerticalOffset={Platform.OS === 'ios' ? 0 : 20}
      >
        <FlatList
          ref={flatListRef}
          data={messages}
          renderItem={renderMessage}
          keyExtractor={(item, index) => `${item.id}-${index}`}
          contentContainerStyle={styles.messagesList}
          ListFooterComponent={renderFooter}
          onContentSizeChange={() => flatListRef.current?.scrollToEnd({ animated: true })}
          keyboardShouldPersistTaps="handled"
          keyboardDismissMode="interactive"
        />

        {/* Non-blocking Transcript UI - positioned above input */}
        {showTranscript && (
          <View style={styles.transcriptBox}>
            <StreamingTranscriptUI
              isRecording={isRecording}
              isConnected={wsConnected}
              partialTranscript={partialTranscript}
              partialConfidence={partialConfidence}
              finalTranscript={pendingTranscript}
              connectionQuality={connectionQuality}
              latencyMs={latencyMs}
              error={error}
              onStartRecording={handleStartRecording}
              onStopRecording={handleStopRecording}
              onClearTranscripts={clearTranscripts}
              onSendTranscript={handleSendTranscript}
              compact={true}
            />
          </View>
        )}

        <View style={styles.inputContainer}>
          <View style={styles.inputWrapper}>
            <TextInput
              ref={inputRef}
              style={styles.textInput}
              value={inputText}
              onChangeText={setInputText}
              placeholder="Type your message..."
              placeholderTextColor="#999"
              multiline
              onSubmitEditing={handleSend}
              returnKeyType="send"
            />

            <View style={styles.voiceButtonWrapper}>
              <VoiceRecordingButton
                isRecording={isRecording}
                onPress={handleVoicePress}
                disabled={false}
                size={44}
              />
            </View>

            <TouchableOpacity
              style={[styles.sendButton, !inputText.trim() && styles.sendButtonDisabled]}
              onPress={handleSend}
              disabled={!inputText.trim()}
            >
              <Ionicons name="send" size={20} color="#fff" />
            </TouchableOpacity>
          </View>
        </View>
      </KeyboardAvoidingView>

    </SafeAreaView>
    </LinearGradient>
  );
}