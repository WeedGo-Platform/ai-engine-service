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

export interface Preset {
  id: string;
  name: string;
  icon: string;
  agent: string;
  personality: string;
  description: string;
}

export interface ModelConfig {
  name?: string;
  version?: string;
  temperature?: number;
  max_tokens?: number;
  [key: string]: any;
}

export interface ModelState {
  isModelLoaded: boolean;
  selectedModel: string;
  selectedAgent: string;
  selectedPersonality: string;
  personalities: Personality[];
  activeTools: Tool[];
  presets: Preset[];
  configDetails: ModelConfig | null;
}

export interface ModelContextType extends ModelState {
  loadPreset: (preset: Preset) => Promise<void>;
  changePersonality: (agentId: string, personalityId: string) => Promise<void>;
  checkModelStatus: () => Promise<void>;
}