/**
 * Voice API Service
 * Handles text-to-speech (TTS) and voice synthesis
 */

const API_BASE_URL = 'http://localhost:5024';

export interface Voice {
  id: string;
  name: string;
  language: string;
  gender?: string;
  sample_url?: string;
}

export const voiceApi = {
  /**
   * Get available TTS voices
   */
  getVoices: async (): Promise<Voice[]> => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/voice/voices`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error('Failed to fetch voices');
      }

      const data = await response.json();
      return data.voices || data || [];
    } catch (error) {
      console.error('Failed to get voices:', error);
      return [];
    }
  },

  /**
   * Synthesize text to speech
   */
  synthesize: async (text: string, voice?: string): Promise<Blob> => {
    try {
      const formData = new FormData();
      formData.append('text', text);
      if (voice) {
        formData.append('voice', voice);
      }
      formData.append('speed', '1.0');
      formData.append('format', 'wav');

      const response = await fetch(`${API_BASE_URL}/api/voice/synthesize`, {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        // Fallback to browser's speech synthesis if API fails
        return voiceApi.synthesizeLocal(text);
      }

      return await response.blob();
    } catch (error) {
      console.error('Failed to synthesize speech:', error);
      // Fallback to browser's speech synthesis
      return voiceApi.synthesizeLocal(text);
    }
  },

  /**
   * Fallback: Use browser's built-in speech synthesis
   */
  synthesizeLocal: async (text: string): Promise<Blob> => {
    return new Promise((resolve, reject) => {
      if (!('speechSynthesis' in window)) {
        reject(new Error('Speech synthesis not supported'));
        return;
      }

      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = 1.0;
      utterance.pitch = 1.0;
      utterance.volume = 1.0;

      // Create a dummy blob for compatibility
      const audioContext = new AudioContext();
      const oscillator = audioContext.createOscillator();
      const destination = audioContext.createMediaStreamDestination();
      oscillator.connect(destination);

      const mediaRecorder = new MediaRecorder(destination.stream);
      const chunks: Blob[] = [];

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          chunks.push(e.data);
        }
      };

      mediaRecorder.onstop = () => {
        const blob = new Blob(chunks, { type: 'audio/webm' });
        resolve(blob);
      };

      utterance.onstart = () => {
        oscillator.start();
        mediaRecorder.start();
      };

      utterance.onend = () => {
        oscillator.stop();
        mediaRecorder.stop();
      };

      utterance.onerror = (error) => {
        reject(error);
      };

      window.speechSynthesis.speak(utterance);
    });
  },

  /**
   * Stop any currently playing speech
   */
  stopSpeaking: () => {
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
    }
  }
};