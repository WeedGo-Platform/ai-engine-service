export interface Personality {
  id: string;
  name: string;
  description: string;
  systemPrompt?: string;
}

export interface Tool {
  id: string;
  name: string;
  description: string;
  enabled: boolean;
}

export interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  responseTime?: number;
  tools?: any[];
  toolsUsed?: string[];
  tokens?: number;
  tokensPerSec?: number;
  agent?: string;
  personality?: string;
  model?: string;
  promptUsed?: string;
  metadata?: any;
}

export interface Preset {
  id: string;
  name: string;
  icon: string;
  description?: string;
  personality: string;
  agent: string;
  tools: Tool[];
}

export interface ConversationTemplate {
  id: string;
  title: string;
  message: string;
  icon: string;
  category?: string;
}

export interface Voice {
  id: string;
  name: string;
  language: string;
  gender: string;
  preview?: string;
}

export interface User {
  id: string;
  email: string;
  name?: string;
  phone?: string;
  preferences?: any;
}

export interface AIConfig {
  model: string;
  agent: string;
  personality: string;
  tools: Tool[];
  temperature: number;
  maxTokens: number;
}

export interface VoiceSettings {
  enabled: boolean;
  voiceId: string;
  speed: number;
  pitch: number;
}

export interface UsageStats {
  inputTokens: number;
  outputTokens: number;
  totalCost: number;
}