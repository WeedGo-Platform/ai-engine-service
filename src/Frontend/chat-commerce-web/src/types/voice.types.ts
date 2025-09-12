export interface Voice {
  id: string;
  name: string;
  language?: string;
  gender?: string;
}

export interface VoiceState {
  availableVoices: Voice[];
  selectedVoice: string;
  isSpeakerEnabled: boolean;
  isSpeaking: boolean;
  isRecording: boolean;
  isTranscribing: boolean;
  transcript: string;
}

export interface VoiceContextType extends VoiceState {
  toggleSpeaker: () => void;
  changeVoice: (voiceId: string) => Promise<void>;
  startRecording: () => void;
  stopRecording: () => void;
  speakText: (text: string) => Promise<void>;
  stopSpeaking: () => void;
}