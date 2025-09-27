import React, { useEffect, useRef, useState } from 'react';
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
import { useEnhancedTranscription } from '../../hooks/useEnhancedTranscription';
import { VoiceRecordingButton } from '../../components/chat/VoiceRecordingButton';
import { TranscriptDisplay } from '../../components/chat/TranscriptDisplay';
import { Colors, GlassStyles, BorderRadius, Shadows } from '@/constants/Colors';
import { useTheme } from '@/contexts/ThemeContext';
import { glassChatStyles as staticStyles } from '@/constants/GlassmorphismStyles';
import { BlurView } from 'expo-blur';

export default function ChatScreen() {
  const [inputText, setInputText] = useState('');
  const [isTTSEnabled, setIsTTSEnabled] = useState(true);
  const flatListRef = useRef<FlatList>(null);
  const inputRef = useRef<TextInput>(null);
  const { theme, isDark } = useTheme();

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
      flexDirection: 'row',
      justifyContent: 'space-between',
      alignItems: 'center',
      backgroundColor: 'rgba(142, 142, 147, 0.5)', // Space gray with 50% opacity
      backdropFilter: 'blur(10px)',
      paddingVertical: 10,
      paddingHorizontal: 20,
      marginTop: Platform.OS === 'ios' ? 10 : 5,
      marginHorizontal: 16,
      marginBottom: 8,
      borderRadius: 30,
      borderWidth: 1,
      borderColor: 'rgba(255, 255, 255, 0.5)',
    },
    inputContainer: {
      position: 'relative', // Changed from absolute to work with KeyboardAvoidingView
      bottom: 0,
      left: 0,
      right: 0,
      paddingBottom: Platform.OS === 'ios' ? 90 : 68, // Space for tab bar
      paddingTop: 8,
      paddingHorizontal: 16,
      backgroundColor: 'transparent',
    },
    inputWrapper: {
      flexDirection: 'row',
      alignItems: 'center',
      backgroundColor: 'rgba(142, 142, 147, 0.5)', // Same space gray as header
      backdropFilter: 'blur(10px)',
      borderRadius: 30,
      paddingHorizontal: 12,
      paddingVertical: 8,
      borderWidth: 1,
      borderColor: 'rgba(255, 255, 255, 0.5)',
      marginBottom: 0, // No bottom margin
      marginTop: 0, // No top margin
      gap: 8,
    },
    textInput: {
      flex: 1,
      fontSize: 16,
      color: theme.text,
      paddingVertical: 8,
      paddingHorizontal: 8,
      minHeight: 36,
      maxHeight: 100,
    },
    messagesList: {
      paddingHorizontal: 16,
      paddingBottom: 20, // Reduced since input is no longer absolute
      paddingTop: 8,
    },
  }), [theme, isDark]);

  const {
    isRecording,
    transcript,
    partialTranscript,
    status: transcriptionStatus,
    error: transcriptionError,
    recordingDuration,
    audioLevel,
    startRecording,
    stopRecording,
    cancelRecording,
    resetTranscription,
  } = useEnhancedTranscription({
    onTranscription: (text: string) => {
      // Auto-send when silence detected (2 seconds)
      if (text.trim()) {
        handleSendMessage(text, true);
        setInputText('');
      }
    },
    onPartialTranscript: (text: string) => {
      // Show real-time transcript as user speaks
      setInputText(text);
    },
    maxDuration: 60000, // 1 minute max recording
    silenceThreshold: 2000, // 2 seconds of silence triggers send
    language: 'en',
    onError: (error) => {
      console.log('Transcription error:', error);
      // Don't show error for connection issues, just reset
      resetTranscription();
      setInputText('');
    },
  });

  useEffect(() => {
    // Connect to chat when screen loads
    connect();
    markAsRead();

    return () => {
      // Mark as read when leaving
      markAsRead();
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

  const handleVoicePress = async () => {
    try {
      if (isRecording) {
        await stopRecording();
      } else {
        setInputText('');
        resetTranscription();
        await startRecording();
      }
    } catch (error) {
      console.log('Voice recording error:', error);
      // Silent error handling - just reset state
      resetTranscription();
      setInputText('');
    }
  };

  const handleVoiceLongPress = () => {
    if (isRecording) {
      cancelRecording();
    }
  };

  const handleSpeakerToggle = () => {
    setIsTTSEnabled(!isTTSEnabled);
  };

  const renderMessage = ({ item }: { item: any }) => {
    return <MessageBubble message={item} />;
  };

  const renderHeader = () => {
    return (
      <View style={styles.header}>
        <View style={styles.headerLeft}>
          <Text style={styles.headerTitle}>WeedGo AI</Text>
          <View style={[styles.statusDot, isConnected ? styles.connected : styles.disconnected]} />
        </View>
        <View style={styles.headerRight}>
          <TouchableOpacity
            onPress={handleSpeakerToggle}
            style={[styles.speakerButton, !isTTSEnabled && styles.speakerButtonOff]}
          >
            <Ionicons
              name={isTTSEnabled ? "volume-high" : "volume-mute"}
              size={22}
              color={isTTSEnabled ? Colors.light.primary : "#999"}
            />
          </TouchableOpacity>
          <TouchableOpacity onPress={clearChat} style={styles.clearButton}>
            <Ionicons name="trash-outline" size={20} color="#666" />
          </TouchableOpacity>
        </View>
      </View>
    );
  };

  const renderFooter = () => {
    return (
      <>
        {messages.length === 0 || messages[messages.length - 1]?.type === 'assistant' ? (
          <SuggestionChips />
        ) : null}
        {isTyping && <TypingIndicator />}
      </>
    );
  };

  return (
    <LinearGradient
      colors={isDark ? [theme.background, theme.backgroundSecondary, theme.surface] : [theme.gradientStart, theme.gradientMid, theme.gradientEnd]}
      style={styles.gradientContainer}
      start={{ x: 0, y: 0 }}
      end={{ x: 0.5, y: 1 }}
    >
      <SafeAreaView style={styles.container}>
        {renderHeader()}

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

        <View style={styles.inputContainer}>
          {/* Enhanced Transcript Display - show partial transcript while recording */}
          {isRecording && partialTranscript && (
            <TranscriptDisplay
              transcript={partialTranscript}
              isRecording={isRecording}
              isProcessing={transcriptionStatus === 'processing' || transcriptionStatus === 'transcribing'}
              error={null} // Don't show errors in UI
            />
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
                disabled={transcriptionStatus === 'processing' || transcriptionStatus === 'transcribing'}
                size={44}
              />
              {isRecording && (
                <Text style={styles.recordingTime}>
                  {Math.floor(recordingDuration / 1000)}s
                </Text>
              )}
            </View>

            <TouchableOpacity
              style={[styles.sendButton, !inputText.trim() && styles.sendButtonDisabled]}
              onPress={handleSend}
              disabled={!inputText.trim()}
            >
              <Ionicons name="chatbubble" size={20} color="#fff" />
            </TouchableOpacity>
          </View>
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
    </LinearGradient>
  );
}