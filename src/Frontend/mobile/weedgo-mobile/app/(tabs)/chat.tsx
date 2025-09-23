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
  StyleSheet,
  ActivityIndicator,
  ScrollView,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useChatStore } from '../../stores/chatStore';
import { MessageBubble } from '../../components/chat/MessageBubble';
import { TypingIndicator } from '../../components/chat/TypingIndicator';
import { SuggestionChips } from '../../components/chat/SuggestionChips';
import { useVoiceInput } from '../../hooks/useVoiceInput';
import { Colors } from '@/constants/Colors';

export default function ChatScreen() {
  const [inputText, setInputText] = useState('');
  const flatListRef = useRef<FlatList>(null);
  const inputRef = useRef<TextInput>(null);

  const {
    messages,
    isTyping,
    isConnected,
    connect,
    sendMessage,
    markAsRead,
    clearChat,
  } = useChatStore();

  const { isRecording, startRecording, stopRecording } = useVoiceInput({
    onTranscription: (text: string) => {
      if (text) {
        sendMessage(text, true);
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

  const handleSend = () => {
    if (inputText.trim()) {
      sendMessage(inputText);
      setInputText('');
    }
  };

  const handleVoicePress = async () => {
    if (isRecording) {
      await stopRecording();
    } else {
      await startRecording();
    }
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
        <TouchableOpacity onPress={clearChat} style={styles.clearButton}>
          <Ionicons name="trash-outline" size={20} color="#666" />
        </TouchableOpacity>
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
              <Ionicons name="send" size={20} color="#fff" />
            </TouchableOpacity>
          </View>
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.light.background,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 16,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  headerLeft: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: Colors.light.text,
  },
  statusDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginLeft: 8,
  },
  connected: {
    backgroundColor: Colors.light.primary,
  },
  disconnected: {
    backgroundColor: '#ef4444',
  },
  clearButton: {
    padding: 8,
  },
  keyboardAvoid: {
    flex: 1,
  },
  messagesList: {
    paddingHorizontal: 16,
    paddingTop: 8,
    paddingBottom: 16,
  },
  inputContainer: {
    backgroundColor: '#fff',
    borderTopWidth: 1,
    borderTopColor: '#e0e0e0',
    paddingHorizontal: 16,
    paddingVertical: 8,
    paddingBottom: Platform.OS === 'ios' ? 24 : 8,
  },
  inputWrapper: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    backgroundColor: '#f9f9f9',
    borderRadius: 24,
    paddingHorizontal: 16,
    paddingVertical: 8,
    minHeight: 48,
  },
  textInput: {
    flex: 1,
    fontSize: 16,
    color: Colors.light.text,
    maxHeight: 100,
    paddingTop: Platform.OS === 'ios' ? 4 : 0,
    paddingBottom: Platform.OS === 'ios' ? 4 : 0,
  },
  voiceButton: {
    width: 36,
    height: 36,
    borderRadius: 18,
    justifyContent: 'center',
    alignItems: 'center',
    marginLeft: 8,
    backgroundColor: '#f0fdf4',
  },
  recording: {
    backgroundColor: '#ef4444',
  },
  sendButton: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: Colors.light.primary,
    justifyContent: 'center',
    alignItems: 'center',
    marginLeft: 8,
  },
  sendButtonDisabled: {
    backgroundColor: '#ccc',
  },
});