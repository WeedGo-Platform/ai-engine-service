import { Audio } from 'expo-av';
import * as Speech from 'expo-speech';
import { Platform } from 'react-native';

interface VoiceRecordingResult {
  success: boolean;
  uri?: string;
  error?: string;
  transcript?: string;
}

interface VoiceSettings {
  language: string;
  pitch: number;
  rate: number;
}

class VoiceService {
  private recording: Audio.Recording | null = null;
  private isRecording = false;
  private permissionsGranted = false;

  /**
   * Request audio recording permissions
   */
  async requestPermissions(): Promise<boolean> {
    try {
      const { granted } = await Audio.requestPermissionsAsync();
      this.permissionsGranted = granted;
      return granted;
    } catch (error) {
      console.error('Failed to request audio permissions:', error);
      return false;
    }
  }

  /**
   * Start voice recording
   */
  async startRecording(): Promise<boolean> {
    try {
      // Check permissions
      if (!this.permissionsGranted) {
        const granted = await this.requestPermissions();
        if (!granted) {
          console.error('Audio permissions not granted');
          return false;
        }
      }

      // Configure audio mode
      await Audio.setAudioModeAsync({
        allowsRecordingIOS: true,
        playsInSilentModeIOS: true,
        playThroughEarpieceAndroid: false,
        staysActiveInBackground: false,
        shouldDuckAndroid: true,
      });

      // Create and start recording
      const { recording } = await Audio.Recording.createAsync(
        Audio.RecordingOptionsPresets.HIGH_QUALITY
      );

      this.recording = recording;
      this.isRecording = true;

      return true;
    } catch (error) {
      console.error('Failed to start recording:', error);
      return false;
    }
  }

  /**
   * Stop voice recording and return the audio file URI
   */
  async stopRecording(): Promise<VoiceRecordingResult> {
    try {
      if (!this.recording || !this.isRecording) {
        return {
          success: false,
          error: 'No recording in progress',
        };
      }

      await this.recording.stopAndUnloadAsync();
      const uri = this.recording.getURI();

      // Reset audio mode
      await Audio.setAudioModeAsync({
        allowsRecordingIOS: false,
      });

      this.recording = null;
      this.isRecording = false;

      if (!uri) {
        return {
          success: false,
          error: 'Failed to get recording URI',
        };
      }

      return {
        success: true,
        uri,
      };
    } catch (error) {
      console.error('Failed to stop recording:', error);
      this.recording = null;
      this.isRecording = false;

      return {
        success: false,
        error: 'Failed to stop recording',
      };
    }
  }

  /**
   * Cancel current recording
   */
  async cancelRecording(): Promise<void> {
    try {
      if (this.recording && this.isRecording) {
        await this.recording.stopAndUnloadAsync();
        this.recording = null;
        this.isRecording = false;
      }
    } catch (error) {
      console.error('Failed to cancel recording:', error);
    }
  }

  /**
   * Send audio to backend for transcription
   */
  async transcribeAudio(audioUri: string): Promise<string | null> {
    try {
      const apiUrl = process.env.EXPO_PUBLIC_API_URL || 'http://10.0.0.169:5024';

      // Create form data
      const formData = new FormData();
      formData.append('audio', {
        uri: audioUri,
        type: 'audio/m4a',
        name: 'recording.m4a',
      } as any);

      // Send to backend
      const response = await fetch(`${apiUrl}/api/voice/transcribe`, {
        method: 'POST',
        body: formData,
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      if (!response.ok) {
        throw new Error('Transcription failed');
      }

      const data = await response.json();
      return data.transcript || null;
    } catch (error) {
      console.error('Failed to transcribe audio:', error);
      return null;
    }
  }

  /**
   * Text-to-speech: Speak the given text
   */
  async speak(
    text: string,
    settings?: Partial<VoiceSettings>
  ): Promise<void> {
    try {
      const options: Speech.SpeechOptions = {
        language: settings?.language || 'en-US',
        pitch: settings?.pitch || 1.0,
        rate: settings?.rate || 1.0,
      };

      await Speech.speak(text, options);
    } catch (error) {
      console.error('Failed to speak text:', error);
    }
  }

  /**
   * Stop speaking
   */
  async stopSpeaking(): Promise<void> {
    try {
      await Speech.stop();
    } catch (error) {
      console.error('Failed to stop speaking:', error);
    }
  }

  /**
   * Check if currently speaking
   */
  async isSpeaking(): Promise<boolean> {
    try {
      return await Speech.isSpeakingAsync();
    } catch (error) {
      console.error('Failed to check speaking status:', error);
      return false;
    }
  }

  /**
   * Get available voices
   */
  async getAvailableVoices(): Promise<Speech.Voice[]> {
    try {
      return await Speech.getAvailableVoicesAsync();
    } catch (error) {
      console.error('Failed to get available voices:', error);
      return [];
    }
  }

  /**
   * Quick voice search flow
   */
  async performVoiceSearch(
    onTranscriptionComplete: (text: string) => void,
    onError?: (error: string) => void
  ): Promise<void> {
    try {
      // Start recording
      const started = await this.startRecording();
      if (!started) {
        onError?.('Failed to start recording');
        return;
      }

      // Record for max 10 seconds or until stopped
      setTimeout(async () => {
        if (this.isRecording) {
          const result = await this.stopRecording();

          if (result.success && result.uri) {
            // Transcribe the audio
            const transcript = await this.transcribeAudio(result.uri);

            if (transcript) {
              onTranscriptionComplete(transcript);
            } else {
              onError?.('Failed to transcribe audio');
            }
          } else {
            onError?.(result.error || 'Recording failed');
          }
        }
      }, 10000);
    } catch (error) {
      console.error('Voice search failed:', error);
      onError?.('Voice search failed');
    }
  }

  /**
   * Get recording status
   */
  getIsRecording(): boolean {
    return this.isRecording;
  }

  /**
   * Haptic feedback for voice interactions
   */
  async provideHapticFeedback(type: 'light' | 'medium' | 'heavy' = 'light'): Promise<void> {
    if (Platform.OS === 'ios') {
      const { impactAsync, ImpactFeedbackStyle } = await import('expo-haptics');

      const style = {
        light: ImpactFeedbackStyle.Light,
        medium: ImpactFeedbackStyle.Medium,
        heavy: ImpactFeedbackStyle.Heavy,
      }[type];

      await impactAsync(style);
    }
  }
}

// Export singleton instance
export const voiceService = new VoiceService();