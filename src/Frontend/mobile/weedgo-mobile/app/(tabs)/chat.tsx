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
import { AIThinkingIndicator } from '../../components/chat/AIThinkingIndicator';
import { SuggestionChips } from '../../components/chat/SuggestionChips';
import { PersonalitySelector } from '../../components/chat/PersonalitySelector';
import { useMultilingualVoiceTranscription } from '../../hooks/useMultilingualVoiceTranscription';
import { VoiceRecordingButton } from '../../components/chat/VoiceRecordingButton';
import { cleanupTranscript } from '../../utils/transcriptCleaner';
import { Colors, GlassStyles, BorderRadius, Shadows} from '@/constants/Colors';
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
  const { theme, isDark} = useTheme();
  const silenceTimerRef = useRef<NodeJS.Timeout | null>(null);
  const sentTranscriptsRef = useRef<Set<string>>(new Set());
  const [isUserScrolling, setIsUserScrolling] = useState(false);
  const autoScrollTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const [visibleMessageCount, setVisibleMessageCount] = useState(5);
  const [showLoadMore, setShowLoadMore] = useState(false);
  const lastVoiceMessageRef = useRef<boolean>(false);

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
      paddingHorizontal: 16,
      paddingTop: Platform.OS === 'ios' ? 8 : 8,
      paddingBottom: 12,
      backgroundColor: 'transparent',
    },
    keyboardAvoid: {
      flex: 1,
      backgroundColor: 'transparent',
      paddingHorizontal: 16,
      paddingTop: 20,
    },
    headerTop: {
      flexDirection: 'row' as const,
      justifyContent: 'space-between' as const,
      alignItems: 'center' as const,
      backgroundColor: 'rgba(142, 142, 147, 0.5)',
      paddingVertical: 10,
      paddingHorizontal: 20,
      marginTop: Platform.OS === 'ios' ? 10 : 5,
      marginHorizontal: 4,
      marginBottom: 8,
      borderRadius: 30,
      borderWidth: 1,
      borderColor: 'rgba(255, 255, 255, 0.5)',
    },
    headerControls: {
      flexDirection: 'row' as const,
      alignItems: 'center' as const,
      gap: 8,
    },
    agentInfo: {
      flexDirection: 'row' as const,
      alignItems: 'center' as const,
      gap: 12,
    },
    agentAvatar: {
      width: 40,
      height: 40,
      borderRadius: 20,
      backgroundColor: 'rgba(255, 255, 255, 0.2)',
      justifyContent: 'center' as const,
      alignItems: 'center' as const,
      borderWidth: 2,
      borderColor: 'rgba(255, 255, 255, 0.3)',
    },
    avatarText: {
      fontSize: 18,
      fontWeight: '700' as const,
      color: '#fff',
    },
    agentAvatarOnline: {
      borderColor: '#22C55E',
    },
    agentDetails: {
      gap: 2,
    },
    agentName: {
      fontSize: 16,
      fontWeight: '600' as const,
      color: '#fff',
    },
    agentStatus: {
      flexDirection: 'row' as const,
      alignItems: 'center' as const,
      gap: 6,
    },
    statusDot: {
      width: 6,
      height: 6,
      borderRadius: 3,
      backgroundColor: '#22C55E',
    },
    statusText: {
      fontSize: 12,
      color: 'rgba(255, 255, 255, 0.8)',
    },
    headerControls: {
      flexDirection: 'row' as const,
      alignItems: 'center' as const,
      gap: 12,
    },
    controlBtn: {
      width: 36,
      height: 36,
      borderRadius: 18,
      backgroundColor: 'rgba(255, 255, 255, 0.15)',
      justifyContent: 'center' as const,
      alignItems: 'center' as const,
    },
    controlBtnActive: {
      backgroundColor: 'rgba(255, 255, 255, 0.25)',
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
    loadMoreButton: {
      flexDirection: 'row' as const,
      alignItems: 'center' as const,
      justifyContent: 'center' as const,
      paddingVertical: 12,
      paddingHorizontal: 16,
      marginHorizontal: 16,
      marginVertical: 8,
      backgroundColor: 'rgba(139, 92, 246, 0.3)',
      borderRadius: 12,
      gap: 8,
    },
    loadMoreText: {
      fontSize: 14,
      fontWeight: '600' as const,
      color: '#fff',
    },
    messagesList: {
      paddingBottom: 20,
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

  // Auto-speak AI responses when user sent voice message
  useEffect(() => {
    // Check if a new assistant message was added
    if (messages.length > prevMessageCountRef.current) {
      const lastMessage = messages[messages.length - 1];

      // If last message is from assistant and user's last message was voice, auto-speak
      if (lastMessage.type === 'assistant' && lastVoiceMessageRef.current && isTTSEnabled) {
        // The MessageBubble component will handle the actual TTS
        // Reset the voice flag after triggering
        lastVoiceMessageRef.current = false;
      }
    }
  }, [messages, isTTSEnabled]);

  // Compute visible messages (last N messages)
  const visibleMessages = React.useMemo(() => {
    return messages.slice(-visibleMessageCount);
  }, [messages, visibleMessageCount]);

  // Determine if there are more messages to load
  useEffect(() => {
    setShowLoadMore(messages.length > visibleMessageCount);
  }, [messages.length, visibleMessageCount]);

  // Smart expansion: only expand visible count when user is viewing most messages
  useEffect(() => {
    if (messages.length > prevMessageCountRef.current) {
      // If user has already expanded to see most messages (within 2 of total),
      // expand to include the new message. Otherwise, keep current view.
      if (visibleMessageCount >= messages.length - 2) {
        setVisibleMessageCount(messages.length);
      }
    }
    prevMessageCountRef.current = messages.length;
  }, [messages.length, visibleMessageCount]);

  useEffect(() => {
    // Only auto-scroll if user isn't manually scrolling
    if (messages.length > prevMessageCountRef.current && !isUserScrolling) {
      // Small delay to ensure content is rendered
      setTimeout(() => {
        flatListRef.current?.scrollToEnd({ animated: true });
      }, 100);
    }
  }, [messages.length, isUserScrolling]);

  // Detect when user scrolls manually
  const handleScroll = useCallback((event: any) => {
    const { contentOffset, contentSize, layoutMeasurement } = event.nativeEvent;
    const isAtBottom = contentOffset.y + layoutMeasurement.height >= contentSize.height - 50;

    // If user is not at bottom, they're manually scrolling
    setIsUserScrolling(!isAtBottom);

    // Clear auto-scroll disable after a delay
    if (autoScrollTimeoutRef.current) {
      clearTimeout(autoScrollTimeoutRef.current);
    }
    autoScrollTimeoutRef.current = setTimeout(() => {
      setIsUserScrolling(false);
    }, 3000);
  }, []);

  const handleSendMessage = (text: string, fromVoice: boolean = false) => {
    if (text.trim()) {
      // Track if this message is from voice for auto-TTS response
      lastVoiceMessageRef.current = fromVoice;
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

  const handleLoadMore = () => {
    // Load 10 more messages
    setVisibleMessageCount(prev => Math.min(prev + 10, messages.length));
  };

  const handleQuickAction = useCallback((action: string, data?: any) => {
    console.log('[CHAT] Quick action pressed:', action, data);
    // Handle quick actions like "Add to Cart", "View Details", etc.
    // This could trigger navigation or other actions based on the action type
    if (action === 'view_product' && data?.productId) {
      // Navigate to product detail or trigger action
      console.log('[CHAT] View product:', data.productId);
    } else if (action === 'add_to_cart' && data) {
      console.log('[CHAT] Add to cart:', data);
    }
  }, []);

  const renderMessage = useCallback(({ item, index }: { item: any; index: number }) => {
    // Debug: Log message structure
    if (item.quick_actions) {
      console.log('[CHAT] Message has quick_actions:', item.quick_actions);
    }
    return (
      <MessageBubble
        message={item}
        onQuickActionPress={handleQuickAction}
      />
    );
  }, [handleQuickAction]);

  const renderHeader = () => {
    if (showLoadMore) {
      return (
        <TouchableOpacity
          style={styles.loadMoreButton}
          onPress={handleLoadMore}
          activeOpacity={0.7}
        >
          <Ionicons name="chevron-up" size={20} color={Colors.light.primary} />
          <Text style={styles.loadMoreText}>
            Load {Math.min(10, messages.length - visibleMessageCount)} more messages
          </Text>
        </TouchableOpacity>
      );
    }
    return null;
  };

  const renderFooter = () => {
    if (isTyping) {
      return <AIThinkingIndicator personality={personalityName} />;
    }
    return null;
  };

  return (
    <LinearGradient
      colors={isDark ? [theme.background, theme.backgroundSecondary, theme.surface] : [theme.gradientStart, theme.gradientMid, theme.gradientEnd]}
      style={styles.gradientContainer}
      start={{ x: 0, y: 0 }}
      end={{ x: 0.5, y: 1 }}
    >
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        {/* Header Top Row - Agent Info & Controls */}
        <View style={styles.headerTop}>
          <View style={styles.agentInfo}>
            <View style={[styles.agentAvatar, isConnected && styles.agentAvatarOnline]}>
              <Text style={styles.avatarText}>
                {personalityName ? personalityName.charAt(0).toUpperCase() : 'D'}
              </Text>
            </View>
            <PersonalitySelector />
          </View>

          <View style={styles.headerControls}>
            <TouchableOpacity
              style={[styles.controlBtn, isTTSEnabled && styles.controlBtnActive]}
              onPress={handleSpeakerToggle}
            >
              <Ionicons
                name={isTTSEnabled ? 'volume-high' : 'volume-mute'}
                size={20}
                color="#fff"
              />
            </TouchableOpacity>
            <TouchableOpacity style={styles.controlBtn}>
              <Ionicons name="settings-outline" size={20} color="#fff" />
            </TouchableOpacity>
          </View>
        </View>
      </View>

      <KeyboardAvoidingView
        style={styles.keyboardAvoid}
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        keyboardVerticalOffset={Platform.OS === 'ios' ? 0 : 20}
      >
        <FlatList
          ref={flatListRef}
          data={visibleMessages}
          renderItem={renderMessage}
          keyExtractor={(item, index) => `${item.id}-${index}`}
          contentContainerStyle={styles.messagesList}
          ListHeaderComponent={renderHeader}
          ListFooterComponent={renderFooter}
          keyboardShouldPersistTaps="handled"
          keyboardDismissMode="interactive"
          onScroll={handleScroll}
          scrollEventThrottle={16}
          removeClippedSubviews={true}
          maxToRenderPerBatch={10}
          updateCellsBatchingPeriod={50}
          windowSize={21}
          initialNumToRender={15}
        />

        {/* Suggestion Chips */}
        {!isRecording && messages.length > 0 && <SuggestionChips />}

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
              placeholder="Type or speak..."
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

            {inputText.trim() ? (
              <LinearGradient
                colors={['#8B5CF6', '#7C3AED']}
                style={styles.sendButton}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 1 }}
              >
                <TouchableOpacity
                  style={styles.sendButtonInner}
                  onPress={handleSend}
                >
                  <Ionicons name="chatbubbles" size={20} color="#fff" />
                </TouchableOpacity>
              </LinearGradient>
            ) : (
              <TouchableOpacity
                style={styles.sendButtonDisabled}
                disabled
              >
                <Ionicons name="chatbubbles" size={20} color="#fff" />
              </TouchableOpacity>
            )}
          </View>
        </View>
      </KeyboardAvoidingView>

    </SafeAreaView>
    </LinearGradient>
  );
}