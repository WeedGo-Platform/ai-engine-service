// Model and Agent Types
export interface Personality {
  id: string;
  name: string;
  filename: string;
  path: string;
}

export interface Tool {
  name: string;
  enabled: boolean;
}

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
  metadata?: any;
}

export interface Preset {
  id: string;
  name: string;
  icon: string;
  agent: string;
  personality: string;
  description: string;
}

export interface ConversationTemplate {
  id: string;
  category: string;
  icon: string;
  title: string;
  message: string;
}

export interface Voice {
  id: string;
  name: string;
  language?: string;
  gender?: string;
}

// User Types
export interface User {
  id?: string;
  name?: string;
  email: string;
  [key: string]: any;
}

// AI Configuration Types
export interface AIConfig {
  model: string;
  agent: string;
  personality: string;
  tools: Tool[];
  temperature?: number;
  maxTokens?: number;
  topP?: number;
  frequencyPenalty?: number;
  presencePenalty?: number;
}

// Voice Settings Types
export interface VoiceSettings {
  enabled: boolean;
  voiceId: string;
  speed?: number;
  pitch?: number;
  volume?: number;
}