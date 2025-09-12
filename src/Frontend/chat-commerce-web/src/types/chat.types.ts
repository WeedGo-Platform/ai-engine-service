export interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  responseTime?: number;
  tokens?: number;
  tokensPerSec?: number;
  promptUsed?: string;
  toolsUsed?: string[];
  model?: string;
  agent?: string;
  personality?: string;
  metadata?: MessageMetadata;
}

export interface MessageMetadata {
  tokens?: number;
  tokens_per_sec?: number;
  prompt_template?: string;
  prompt?: string;
  [key: string]: any;
}

export interface ConversationTemplate {
  id: string;
  category: string;
  icon: string;
  title: string;
  message: string;
}

export interface ChatState {
  messages: Message[];
  sessionId: string;
  isLoading: boolean;
  error: string | null;
}

export interface ChatContextType extends ChatState {
  sendMessage: (message: string) => Promise<void>;
  clearSession: () => void;
  addMessage: (message: Message) => void;
  setMessages: (messages: Message[]) => void;
}