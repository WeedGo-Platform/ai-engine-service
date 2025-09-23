import { apiClient } from '../api/client';

export interface ChatSession {
  session_id: string;
  agent: string;
  personality: string;
  created_at: string;
}

export interface ChatMessage {
  id: string;
  type: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  session_id?: string;
}

export interface ChatHistoryItem {
  message_id: string;
  session_id: string;
  user_id: string;
  user_message: string;
  assistant_response: string;
  created_at: string;
  metadata: any;
}

class ChatAPI {
  /**
   * Create a new chat session
   */
  async createSession(agent = 'dispensary', personality = 'friendly'): Promise<ChatSession> {
    const response = await apiClient.post('/chat/session', {
      agent,
      personality,
    });
    return response.data as ChatSession;
  }

  /**
   * Get session details
   */
  async getSession(sessionId: string): Promise<ChatSession> {
    const response = await apiClient.get(`/chat/session/${sessionId}`);
    return response.data as ChatSession;
  }

  /**
   * Send a message to the chat
   */
  async sendMessage(sessionId: string, message: string, userId?: string): Promise<any> {
    const response = await apiClient.post('/chat/message', {
      session_id: sessionId,
      message,
      user_id: userId,
    });
    return response.data as ChatSession;
  }

  /**
   * End a chat session
   */
  async endSession(sessionId: string): Promise<void> {
    await apiClient.delete(`/chat/session/${sessionId}`);
  }

  /**
   * Get chat history for a user
   */
  async getChatHistory(userId: string, limit = 20): Promise<ChatHistoryItem[]> {
    const response = await apiClient.get(`/chat/history/${userId}`, {
      params: { limit },
    });
    return response.data.history || [];
  }

  /**
   * Get active sessions
   */
  async getActiveSessions(): Promise<any> {
    const response = await apiClient.get('/chat/sessions');
    return response.data as ChatSession;
  }
}

export const chatAPI = new ChatAPI();