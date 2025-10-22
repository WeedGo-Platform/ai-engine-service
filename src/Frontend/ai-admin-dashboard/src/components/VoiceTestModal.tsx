import React, { useState, useEffect, useRef } from 'react';
import { X, Volume2, Loader2 } from 'lucide-react';
import toast from 'react-hot-toast';
import { api } from '../services/api';

interface VoiceTestModalProps {
  personality: {
    id: string;
    personality_name: string;
    name: string;
    has_voice_sample: boolean;
    voice_provider: string;
  };
  onClose: () => void;
  token: string;
}

const VoiceTestModal: React.FC<VoiceTestModalProps> = ({ personality, onClose, token }) => {
  const [testText, setTestText] = useState('');
  const [isSynthesizing, setIsSynthesizing] = useState(false);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [history, setHistory] = useState<Array<{ text: string; timestamp: Date }>>([]);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const audioUrlsRef = useRef<Set<string>>(new Set());

  // Cleanup function to revoke all object URLs
  useEffect(() => {
    return () => {
      // Cleanup all audio URLs when component unmounts
      audioUrlsRef.current.forEach(url => {
        URL.revokeObjectURL(url);
      });
      audioUrlsRef.current.clear();
      
      // Stop any playing audio
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current.src = '';
        audioRef.current = null;
      }
    };
  }, []);

  // Sample test phrases
  const samplePhrases = [
    "Hello! Welcome to WeedGo. How can I help you today?",
    "This strain is known for its relaxing properties and earthy aroma.",
    "I'd recommend starting with a lower dosage and adjusting as needed.",
    "Our staff can help you find the perfect product for your needs."
  ];

  const synthesizeVoice = async () => {
    if (!testText.trim()) {
      toast.error('Please enter some text to test');
      return;
    }

    setIsSynthesizing(true);

    try {
      const response = await api.voice.synthesize({
        text: testText,
        personality_id: personality.id,
        language: 'en',
        speed: 1.0,
        pitch: 0.0,
        quality: 'high'
      });

      // Get audio blob from response
      const audioBlob = response.data;
      
      // Revoke previous audio URL to prevent memory leak
      if (audioUrl) {
        URL.revokeObjectURL(audioUrl);
        audioUrlsRef.current.delete(audioUrl);
      }
      
      // Stop any currently playing audio
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current.currentTime = 0;
      }
      
      // Create new URL and track it
      const url = URL.createObjectURL(audioBlob);
      audioUrlsRef.current.add(url);
      setAudioUrl(url);
      setHistory([{ text: testText, timestamp: new Date() }, ...history]);

      // Play audio automatically
      const audio = new Audio(url);
      audioRef.current = audio;
      
      audio.onended = () => {
        // Audio finished playing
        audioRef.current = null;
      };
      
      audio.onerror = (err) => {
        console.error('Audio playback failed:', err);
        toast.error('Failed to play audio');
        audioRef.current = null;
      };
      
      audio.play().catch(err => {
        console.error('Audio playback failed:', err);
        toast.error('Failed to play audio. Click the play button to try again.');
      });

      // Get provider info from response headers
      const provider = response.headers['x-provider'];
      toast.success(`Voice synthesized using ${provider || 'TTS provider'}!`);
      setTestText('');
    } catch (error: any) {
      console.error('Synthesis error:', error);
      toast.error(error.message || 'Voice synthesis failed. Please try again.');
    } finally {
      setIsSynthesizing(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 dark:bg-opacity-70 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-6 py-4 flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              Test Voice
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
              {personality.personality_name}
              {personality.has_voice_sample && (
                <span className="ml-2 text-green-600 dark:text-green-400">
                  • Custom Voice Uploaded
                </span>
              )}
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
          >
            <X className="h-6 w-6" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Info Banner */}
          {!personality.has_voice_sample && (
            <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4">
              <p className="text-sm text-yellow-800 dark:text-yellow-200">
                This personality is using the default {personality.voice_provider} voice.
                Upload a custom voice sample for personalized voice cloning.
              </p>
            </div>
          )}

          {/* Sample Phrases */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Sample Phrases
            </label>
            <div className="grid grid-cols-1 gap-2">
              {samplePhrases.map((phrase, idx) => (
                <button
                  key={idx}
                  onClick={() => setTestText(phrase)}
                  className="text-left px-3 py-2 text-sm bg-gray-50 dark:bg-gray-900/50 hover:bg-gray-100 dark:hover:bg-gray-900 rounded-md text-gray-700 dark:text-gray-300 transition-colors"
                >
                  {phrase}
                </button>
              ))}
            </div>
          </div>

          {/* Input Area */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Test Message
            </label>
            <div className="flex gap-2">
              <textarea
                value={testText}
                onChange={(e) => setTestText(e.target.value)}
                placeholder="Type a message to hear in this personality's voice..."
                rows={3}
                className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-2 focus:ring-accent-500 dark:focus:ring-accent-400 bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500"
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && e.ctrlKey) {
                    e.preventDefault();
                    synthesizeVoice();
                  }
                }}
              />
            </div>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              Press Ctrl+Enter to synthesize
            </p>
          </div>

          {/* Synthesize Button */}
          <button
            onClick={synthesizeVoice}
            disabled={!testText.trim() || isSynthesizing}
            className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-accent-600 dark:bg-accent-500 text-white rounded-md hover:bg-accent-700 dark:hover:bg-accent-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isSynthesizing ? (
              <>
                <Loader2 className="h-5 w-5 animate-spin" />
                Synthesizing Voice...
              </>
            ) : (
              <>
                <Volume2 className="h-5 w-5" />
                Generate Voice
              </>
            )}
          </button>

          {/* Audio Player */}
          {audioUrl && (
            <div className="bg-gray-50 dark:bg-gray-900/50 rounded-lg p-4">
              <p className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Latest Generated Audio:
              </p>
              <audio
                src={audioUrl}
                controls
                className="w-full"
                style={{
                  backgroundColor: 'transparent',
                  border: 'none',
                }}
              />
            </div>
          )}

          {/* History */}
          {history.length > 0 && (
            <div>
              <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Test History
              </h4>
              <div className="space-y-2 max-h-48 overflow-y-auto">
                {history.map((item, idx) => (
                  <div
                    key={idx}
                    className="text-sm bg-gray-50 dark:bg-gray-900/50 rounded-md p-2"
                  >
                    <p className="text-gray-900 dark:text-white">{item.text}</p>
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                      {item.timestamp.toLocaleTimeString()}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Info */}
          <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
            <p className="text-sm text-blue-800 dark:text-blue-200">
              <strong>Note:</strong> Voice synthesis uses{' '}
              {personality.has_voice_sample ? 'XTTS v2 with your uploaded voice sample' : `${personality.voice_provider} TTS`}.
              {personality.has_voice_sample && ' Synthesis may take 5-10 seconds on CPU.'}
            </p>
          </div>
        </div>

        {/* Footer */}
        <div className="sticky bottom-0 bg-gray-50 dark:bg-gray-900/50 border-t border-gray-200 dark:border-gray-700 px-6 py-4 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-md hover:bg-gray-50 dark:hover:bg-gray-600 transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

export default VoiceTestModal;
