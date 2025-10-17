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
   * Select appropriate voice based on language and gender
   */
  selectVoice: (language: string = 'en', gender: 'male' | 'female' = 'male'): string => {
    // Language-specific voice mapping
    const voiceMap: Record<string, { male: string; female: string }> = {
      'en': { male: 'ryan', female: 'amy' },
      'en-US': { male: 'ryan', female: 'amy' },
      'en-GB': { male: 'alan', female: 'alba' },
      'fr': { male: 'gilles', female: 'siwis' },
      'fr-FR': { male: 'gilles', female: 'siwis' },
      'es': { male: 'davefx', female: 'ald' },
      'es-ES': { male: 'davefx', female: 'ald' },
      'es-MX': { male: 'davefx', female: 'ald' },
      'pt': { male: 'cadu', female: 'faber' },
      'pt-BR': { male: 'cadu', female: 'faber' },
      'zh': { male: 'huayan_male', female: 'huayan' },
      'zh-CN': { male: 'huayan_male', female: 'huayan' }
    };

    // Extract base language code (e.g., 'en-US' -> 'en')
    const baseLang = language.split('-')[0].toLowerCase();

    // Get voice for specific language or fallback to base language
    const voices = voiceMap[language] || voiceMap[baseLang] || voiceMap['en'];

    return gender === 'female' ? voices.female : voices.male;
  },

  /**
   * Synthesize text to speech
   */
  synthesize: async (text: string, voice?: string): Promise<Blob> => {
    try {
      // Use Ryan (male voice) for Carlos by default
      const selectedVoice = voice || 'ryan';

      console.log('[voiceApi] Synthesizing with voice:', selectedVoice, 'text length:', text.length);

      const formData = new FormData();
      formData.append('text', text);
      formData.append('voice', selectedVoice);
      formData.append('speed', '1.0');
      formData.append('format', 'wav');

      const response = await fetch(`${API_BASE_URL}/api/voice/synthesize`, {
        method: 'POST',
        body: formData
      });

      console.log('[voiceApi] Response status:', response.status, response.statusText);

      if (!response.ok) {
        const errorText = await response.text();
        console.error('[voiceApi] API error:', errorText);
        throw new Error(`TTS API failed: ${response.status} ${response.statusText}`);
      }

      const blob = await response.blob();
      console.log('[voiceApi] Received blob:', blob.size, 'bytes, type:', blob.type);

      return blob;
    } catch (error) {
      console.error('[voiceApi] Synthesis failed:', error);
      // Use browser TTS as last resort
      console.warn('[voiceApi] Falling back to browser TTS');
      return voiceApi.synthesizeBrowserTTS(text);
    }
  },

  /**
   * Fallback: Use browser's built-in speech synthesis (actual speaking, not blob)
   */
  synthesizeBrowserTTS: async (text: string): Promise<Blob> => {
    console.log('[voiceApi] Using browser TTS as fallback');

    // Just speak directly with browser TTS, return empty blob
    if ('speechSynthesis' in window) {
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = 1.0;
      utterance.pitch = 1.0;
      utterance.volume = 1.0;

      // Try to find a male voice
      const voices = window.speechSynthesis.getVoices();
      const maleVoice = voices.find(v =>
        v.name.includes('Male') ||
        v.name.includes('Daniel') ||
        v.name.includes('Fred')
      );
      if (maleVoice) {
        utterance.voice = maleVoice;
      }

      window.speechSynthesis.speak(utterance);
    }

    // Return a small silent audio blob for compatibility
    // (actual speech happens via speechSynthesis.speak above)
    const silentWav = new Uint8Array([
      0x52, 0x49, 0x46, 0x46, // "RIFF"
      0x26, 0x00, 0x00, 0x00, // File size
      0x57, 0x41, 0x56, 0x45, // "WAVE"
      0x66, 0x6D, 0x74, 0x20, // "fmt "
      0x10, 0x00, 0x00, 0x00, // Format chunk size
      0x01, 0x00, // PCM
      0x01, 0x00, // Mono
      0x44, 0xAC, 0x00, 0x00, // Sample rate (44100)
      0x88, 0x58, 0x01, 0x00, // Byte rate
      0x02, 0x00, // Block align
      0x10, 0x00, // Bits per sample
      0x64, 0x61, 0x74, 0x61, // "data"
      0x00, 0x00, 0x00, 0x00  // Data size
    ]);

    return new Blob([silentWav], { type: 'audio/wav' });
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