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
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useChatStore } from '../../stores/chatStore';
import { MessageBubble } from '../../components/chat/MessageBubble';
import { TypingIndicator } from '../../components/chat/TypingIndicator';
import { SuggestionChips } from '../../components/chat/SuggestionChips';
import { useSimpleTranscription } from '../../hooks/useSimpleTranscription';
import { Colors, GlassStyles, BorderRadius, Shadows } from '@/constants/Colors';
import { glassChatStyles as styles } from '@/constants/GlassmorphismStyles';
import { BlurView } from 'expo-blur';

export default function ChatScreen() {
  const [inputText, setInputText] = useState('');
  const [isTTSEnabled, setIsTTSEnabled] = useState(true);
  const flatListRef = useRef<FlatList>(null);
  const inputRef = useRef<TextInput>(null);
  const isDark = true; // Force dark mode
  const theme = isDark ? Colors.dark : Colors.light;

  const {
    messages,
    isTyping,
    isConnected,
    connect,
    sendMessage: sendChatMessage,
    markAsRead,
    clearChat,
  } = useChatStore();

  const {
    isRecording,
    transcript,
    startRecording,
    stopRecording,
  } = useSimpleTranscription({
    onTranscription: (text: string) => {
      if (text.trim()) {
        setInputText(text);
        // Auto-send the message
        handleSendMessage(text, true);
      }
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
    if (isRecording) {
      await stopRecording();
    } else {
      setInputText('');
      await startRecording();
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
    <SafeAreaView style={styles.container}>
      {renderHeader()}

      <KeyboardAvoidingView
        style={styles.keyboardAvoid}
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        keyboardVerticalOffset={Platform.OS === 'ios' ? 90 : 0}
      >
        <FlatList
          ref={flatListRef}
          data={messages}
          renderItem={renderMessage}
          keyExtractor={(item) => item.id}
          contentContainerStyle={styles.messagesList}
          ListFooterComponent={renderFooter}
          onContentSizeChange={() => flatListRef.current?.scrollToEnd({ animated: true })}
        />

        <View style={styles.inputContainer}>
          {/* Recording indicator */}
          {isRecording && (
            <View style={styles.transcriptIndicator}>
              <View style={styles.transcriptHeader}>
                <View style={styles.listeningDot} />
                <Text style={styles.transcriptLabel}>Recording... Speak now</Text>
              </View>
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

            <TouchableOpacity
              style={[styles.voiceButton, isRecording && styles.recording]}
              onPress={handleVoicePress}
            >
              <Ionicons
                name={isRecording ? 'stop' : 'mic'}
                size={24}
                color={isRecording ? '#fff' : Colors.light.primary}
              />
            </TouchableOpacity>

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
  );
}