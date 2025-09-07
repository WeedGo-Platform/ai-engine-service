export interface User {
  id: string;
  name: string;
  email: string;
  avatar?: string;
}

export interface Message {
  id: string;
  text: string;
  content?: string;
  sender: 'user' | 'assistant';
  role?: 'user' | 'assistant' | 'system';
  timestamp: number;
  responseTime?: number;
  tools?: any[];
  toolsUsed?: string[];
  tokens?: number;
  agent?: string;
  personality?: string;
}

export interface ConversationTemplate {
  id: string;
  name: string;
  description: string;
  icon: string;
  prompt: string;
}

export interface Preset {
  id: string;
  name: string;
  description: string;
  icon: string;
  personality: string;
  config?: any;
}

export interface Tool {
  name: string;
  enabled: boolean;
  description?: string;
}

export interface Voice {
  id: string;
  name: string;
  language?: string;
  gender?: string;
}