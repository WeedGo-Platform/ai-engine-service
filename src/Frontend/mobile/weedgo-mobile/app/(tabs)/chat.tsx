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
import { PersonalitySelector } from '../../components/chat/PersonalitySelector';
import { useMultilingualVoiceTranscription } from '../../hooks/useMultilingualVoiceTranscription';
import { VoiceRecordingButton } from '../../components/chat/VoiceRecordingButton';
import { cleanupTranscript } from '../../utils/transcriptCleaner';
import { Colors, GlassStyles, BorderRadius, Shadows } from '@/constants/Colors';
import { useTheme } from '@/contexts/ThemeContext';
import { glassChatStyles as staticStyles } from '@/constants/GlassmorphismStyles';
import { BlurView } from 'expo-blur';

// Voice configuration
const VOICE_CONFIG = {
  autoPauseMs: 2000,  // Send chunk after 2 seconds pause
  autoStopMs: 2000,   // Stop recording after 2 seconds silence
  language: 'en-US'
};

export default function ChatScreen() {
  const [inputText, setInputText] = useState('');
  const [isTTSEnabled, setIsTTSEnabled] = useState(true);
  const [pendingTranscript, setPendingTranscript] = useState('');
  const [sentenceBuffer, setSentenceBuffer] = useState('');
  const [lastSentTranscript, setLastSentTranscript] = useState('');
  const [localError, setLocalError] = useState<string | null>(null);
  const flatListRef = useRef<FlatList>(null);
  const inputRef = useRef<TextInput>(null);
  const { theme, isDark } = useTheme();
  const silenceTimerRef = useRef<NodeJS.Timeout | null>(null);
  const sentTranscriptsRef = useRef<Set<string>>(new Set());

  const {
    messages,
    isTyping,
    isConnected,
    personalityName,
    personality,
    getHeaderTitle,
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
      paddingHorizontal: 16,
      paddingTop: Platform.OS === 'ios' ? 8 : 8,
      paddingBottom: 8,
      backgroundColor: 'transparent',
    },
    headerTitle: {
      fontSize: 16,
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
    transcriptContainer: {
      backgroundColor: 'rgba(255, 255, 255, 0.1)',
      paddingHorizontal: 16,
      paddingVertical: 12,
      marginHorizontal: 16,
      marginBottom: 8,
      borderRadius: 12,
      borderWidth: 1,
      borderColor: 'rgba(255, 255, 255, 0.2)',
    },
    transcriptHeader: {
      flexDirection: 'row' as const,
      alignItems: 'center' as const,
      marginBottom: 8,
      gap: 8,
    },
    recordingIndicator: {
      width: 8,
      height: 8,
      borderRadius: 4,
      backgroundColor: '#FF4444',
    },
    transcriptLabel: {
      fontSize: 12,
      fontWeight: '600' as const,
      color: 'rgba(255, 255, 255, 0.8)',
      flex: 1,
    },
    languageIndicator: {
      fontSize: 11,
      color: '#fff',
      backgroundColor: 'rgba(255, 255, 255, 0.2)',
      paddingHorizontal: 8,
      paddingVertical: 2,
      borderRadius: 8,
    },
    transcriptText: {
      fontSize: 14,
      color: '#fff',
      lineHeight: 20,
    },
  }), [theme, isDark]);

  // Handle sending final transcript to chat
  const handleSendTranscript = useCallback((text: string) => {
    if (text.trim()) {
      sendChatMessage(text, true);
      setPendingTranscript('');
    }
  }, [sendChatMessage]);

  // Initialize multilingual voice transcription
  const {
    isRecording,
    isTranscribing,
    transcript,
    liveTranscript,
    error: voiceError,
    isConnected: voiceConnected,
    detectedLanguage,
    currentLanguage,
    startRecording,
    stopRecording,
    toggleRecording,
    clearTranscript,
    setLanguage,
    connect: connectVoice,
    disconnect: disconnectVoice,
  } = useMultilingualVoiceTranscription({
    autoPauseMs: VOICE_CONFIG.autoPauseMs,
    autoStopMs: VOICE_CONFIG.autoStopMs,
    preferredLanguages: ['en-US', 'fr-FR', 'yo-NG', 'es-ES'], // Add user's preferred languages
    autoDetect: true,
    onTranscriptComplete: (text: string, language: string) => {
      // Send the transcript as a message with detected language
      console.log(`[Chat] Transcript complete in ${language}:`, text);
      if (text.trim()) {
        sendChatMessage(text, true);
        setPendingTranscript('');
      }
    }
  });

  // No need for manual silence detection - the hook handles it

  // Log voice errors (don't send as messages)
  useEffect(() => {
    if (voiceError) {
      console.error('[CHAT] Voice error:', voiceError);
      setLocalError(voiceError);
      setTimeout(() => setLocalError(null), 3000);
    }
  }, [voiceError]);

  // Handle real-time transcript updates
  useEffect(() => {
    // Show the live transcript immediately
    if (transcript || liveTranscript) {
      const displayText = transcript || liveTranscript;
      setPendingTranscript(cleanupTranscript(displayText));
    } else {
      setPendingTranscript('');
    }
  }, [transcript, liveTranscript]);

  useEffect(() => {
    // Connect to chat when screen loads
    connect();
    markAsRead();

    return () => {
      // Mark as read when leaving
      markAsRead();
      disconnectVoice();
    };
  }, []);

  // Track message count to detect new messages
  const prevMessageCountRef = useRef(messages.length);

  useEffect(() => {
    // Only scroll when new messages are added
    if (messages.length > prevMessageCountRef.current) {
      // Small delay to ensure content is rendered
      setTimeout(() => {
        flatListRef.current?.scrollToEnd({ animated: true });
      }, 50);
    }
    prevMessageCountRef.current = messages.length;
  }, [messages.length]);

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
      setPendingTranscript('');
      setSentenceBuffer('');
      clearTranscript();
      sentTranscriptsRef.current.clear(); // Clear sent transcripts when starting new recording

      const success = await startRecording();
      if (!success) {
        setLocalError('Failed to start recording');
      }
    } catch (error) {
      console.error('[CHAT] Failed to start recording:', error);
    }
  };

  const handleStopRecording = async () => {
    try {
      await stopRecording();

      // No need to send pending transcript - the hook handles it via onTranscriptComplete

      // Clear state
      clearTranscript();
      setPendingTranscript('');
      setSentenceBuffer('');
      sentTranscriptsRef.current.clear(); // Clear sent transcripts

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
        <View>
          <Text style={styles.headerTitle}>
            {getHeaderTitle()}
          </Text>
        </View>
        <View style={styles.headerActions}>
          <TouchableOpacity onPress={handleSpeakerToggle}>
            <Ionicons
              name={isTTSEnabled ? 'volume-high' : 'volume-mute'}
              size={24}
              color="#fff"
            />
          </TouchableOpacity>
          <PersonalitySelector />
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
          keyboardShouldPersistTaps="handled"
          keyboardDismissMode="interactive"
        />

        <View style={styles.inputContainer}>
          {/* Live Transcript Display - Under Input */}
          {isRecording && (pendingTranscript || isTranscribing) && (
            <View style={styles.transcriptContainer}>
              <View style={styles.transcriptHeader}>
                <View style={styles.recordingIndicator} />
                <Text style={styles.transcriptLabel}>
                  {isTranscribing ? 'Listening...' : 'Processing...'}
                </Text>
                {detectedLanguage && detectedLanguage !== currentLanguage && (
                  <Text style={styles.languageIndicator}>
                    {detectedLanguage.split('-')[0].toUpperCase()}
                  </Text>
                )}
              </View>
              <Text style={styles.transcriptText}>
                {pendingTranscript || 'Start speaking...'}
              </Text>
            </View>
          )}
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