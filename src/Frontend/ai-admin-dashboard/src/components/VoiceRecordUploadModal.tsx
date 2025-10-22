import React, { useState, useRef, useEffect } from 'react';
import {
  X,
  Mic,
  Square,
  Play,
  Pause,
  Upload,
  FileAudio,
  Volume2,
  CheckCircle,
  Loader2,
  RotateCcw
} from 'lucide-react';
import toast from 'react-hot-toast';

interface VoiceRecordUploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  personalityId: string;
  personalityName: string;
  onUploadComplete: () => void;
  token?: string;
}

const SAMPLE_SCRIPTS = [
  "Hello! Welcome to WeedGo. How can I help you find the perfect product today?",
  "Thank you for choosing us. I'm here to assist you with any questions about our cannabis products.",
  "Our store offers a wide selection of premium quality products. What are you looking for today?",
  "I can help you understand the differences between indica, sativa, and hybrid strains.",
  "Let me know if you need recommendations based on your preferences and experience level."
];

const VoiceRecordUploadModal: React.FC<VoiceRecordUploadModalProps> = ({
  isOpen,
  onClose,
  personalityId,
  personalityName,
  onUploadComplete,
  token
}) => {
  const [mode, setMode] = useState<'choice' | 'record' | 'upload'>('choice');
  const [isRecording, setIsRecording] = useState(false);
  const [recordedBlob, setRecordedBlob] = useState<Blob | null>(null);
  const [recordedURL, setRecordedURL] = useState<string | null>(null);
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isTesting, setIsTesting] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [currentScript, setCurrentScript] = useState(SAMPLE_SCRIPTS[0]);
  
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    if (!isOpen) {
      cleanup();
    }
  }, [isOpen]);

  const cleanup = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
    }
    if (timerRef.current) {
      clearInterval(timerRef.current);
    }
    if (recordedURL) {
      URL.revokeObjectURL(recordedURL);
    }
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current = null;
    }
    setIsRecording(false);
    setRecordedBlob(null);
    setRecordedURL(null);
    setUploadFile(null);
    setIsPlaying(false);
    setRecordingTime(0);
    audioChunksRef.current = [];
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          sampleRate: 24000
        }
      });
      
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus'
      });
      
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = () => {
        const blob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        setRecordedBlob(blob);
        const url = URL.createObjectURL(blob);
        setRecordedURL(url);
        
        // Stop all tracks
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorder.start();
      setIsRecording(true);
      setRecordingTime(0);

      // Start timer
      timerRef.current = setInterval(() => {
        setRecordingTime(prev => prev + 1);
      }, 1000);

    } catch (error) {
      console.error('Error accessing microphone:', error);
      toast.error('Failed to access microphone. Please check permissions.');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    }
  };

  const playRecording = () => {
    if (!recordedURL) return;

    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current = null;
    }

    const audio = new Audio(recordedURL);
    audioRef.current = audio;

    audio.onplay = () => setIsPlaying(true);
    audio.onended = () => {
      setIsPlaying(false);
      audioRef.current = null;
    };
    audio.onerror = () => {
      setIsPlaying(false);
      toast.error('Failed to play recording');
    };

    audio.play();
  };

  const pauseRecording = () => {
    if (audioRef.current) {
      audioRef.current.pause();
      setIsPlaying(false);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      if (!file.type.startsWith('audio/')) {
        toast.error('Please select an audio file');
        return;
      }
      if (file.size > 10 * 1024 * 1024) {
        toast.error('File size must be less than 10MB');
        return;
      }
      setUploadFile(file);
    }
  };

  const testVoice = async () => {
    setIsTesting(true);
    
    // Show initial loading message
    const loadingToast = toast.loading('🎙️ Synthesizing voice with personality...', {
      duration: Infinity
    });
    
    try {
      const response = await fetch('http://localhost:5024/api/voice-synthesis/synthesize', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': token ? `Bearer ${token}` : ''
        },
        body: JSON.stringify({
          text: currentScript,
          personality_id: personalityId,
          language: 'en',
          speed: 1.0,
          quality: 'high'
        })
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Server error: ${response.status}`);
      }

      // Dismiss loading, show processing
      toast.dismiss(loadingToast);
      toast.loading('🔊 Preparing audio playback...', { duration: 500 });

      const blob = await response.blob();
      
      // Check if we got valid audio
      if (blob.size < 1000) {
        throw new Error('Voice synthesis returned empty audio. Voice sample may not be loaded.');
      }

      const audioURL = URL.createObjectURL(blob);
      const audio = new Audio(audioURL);
      
      // Handle audio playback events
      audio.onloadedmetadata = () => {
        toast.dismiss();
        toast.success(`🔊 Playing voice (${Math.round(audio.duration)}s)`, { duration: 2000 });
      };
      
      audio.onerror = () => {
        URL.revokeObjectURL(audioURL);
        toast.error('Failed to play audio. Invalid audio format.');
      };
      
      audio.onended = () => {
        URL.revokeObjectURL(audioURL);
        toast.success('✅ Playback complete', { duration: 2000 });
      };
      
      await audio.play().catch(() => {
        throw new Error('Browser blocked audio playback. Click to play manually.');
      });
      
    } catch (error) {
      console.error('Error testing voice:', error);
      toast.dismiss(loadingToast);
      
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
      
      if (errorMessage.includes('Voice sample may not be loaded')) {
        toast.error('⚠️ No voice sample found. Please upload a voice sample first.', { duration: 4000 });
      } else if (errorMessage.includes('blocked audio')) {
        toast.error('🔇 Browser blocked audio. Click the play button.', { duration: 3000 });
      } else if (errorMessage.includes('500') || errorMessage.includes('503')) {
        toast.error('❌ Voice synthesis service error. Check backend logs.', { duration: 4000 });
      } else {
        toast.error(`❌ ${errorMessage}`, { duration: 4000 });
      }
    } finally {
      setIsTesting(false);
    }
  };

  const uploadVoice = async () => {
    const fileToUpload = recordedBlob || uploadFile;
    if (!fileToUpload) {
      toast.error('No audio file to upload');
      return;
    }

    setIsUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', fileToUpload, `${personalityId}.wav`);

      const response = await fetch(
        `http://localhost:5024/api/voice-providers/voice-samples/upload?personality_id=${personalityId}`,
        {
          method: 'POST',
          headers: {
            'Authorization': token ? `Bearer ${token}` : ''
          },
          body: formData
        }
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Upload failed');
      }

      toast.success('✅ Voice sample uploaded successfully!');
      onUploadComplete();
      onClose();
    } catch (error) {
      console.error('Error uploading voice:', error);
      toast.error(error instanceof Error ? error.message : 'Failed to upload voice sample');
    } finally {
      setIsUploading(false);
    }
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
          <div>
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Voice Sample</h2>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
              {personalityName}
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
          >
            <X className="h-5 w-5 text-gray-500" />
          </button>
        </div>

        <div className="p-6">
          {/* Mode Selection */}
          {mode === 'choice' && (
            <div className="space-y-4">
              <p className="text-gray-700 dark:text-gray-300 mb-6">
                Choose how you'd like to provide a voice sample for this personality:
              </p>
              
              <button
                onClick={() => setMode('record')}
                className="w-full p-6 border-2 border-gray-300 dark:border-gray-600 rounded-xl hover:border-indigo-500 dark:hover:border-indigo-400 hover:bg-indigo-50 dark:hover:bg-indigo-900/20 transition-all group"
              >
                <div className="flex items-center gap-4">
                  <div className="p-4 bg-red-100 dark:bg-red-900/30 rounded-full group-hover:bg-red-200 dark:group-hover:bg-red-900/50 transition-colors">
                    <Mic className="h-8 w-8 text-red-600 dark:text-red-400" />
                  </div>
                  <div className="text-left flex-1">
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-1">
                      Record from Microphone
                    </h3>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      Read a sample script and record directly from your microphone
                    </p>
                  </div>
                </div>
              </button>

              <button
                onClick={() => setMode('upload')}
                className="w-full p-6 border-2 border-gray-300 dark:border-gray-600 rounded-xl hover:border-indigo-500 dark:hover:border-indigo-400 hover:bg-indigo-50 dark:hover:bg-indigo-900/20 transition-all group"
              >
                <div className="flex items-center gap-4">
                  <div className="p-4 bg-blue-100 dark:bg-blue-900/30 rounded-full group-hover:bg-blue-200 dark:group-hover:bg-blue-900/50 transition-colors">
                    <Upload className="h-8 w-8 text-blue-600 dark:text-blue-400" />
                  </div>
                  <div className="text-left flex-1">
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-1">
                      Upload Audio File
                    </h3>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      Upload an existing audio file (WAV, MP3, etc.)
                    </p>
                  </div>
                </div>
              </button>
            </div>
          )}

          {/* Recording Mode */}
          {mode === 'record' && (
            <div className="space-y-6">
              <button
                onClick={() => {
                  setMode('choice');
                  cleanup();
                }}
                className="text-sm text-indigo-600 dark:text-indigo-400 hover:underline flex items-center gap-1"
              >
                ← Back to options
              </button>

              {/* Sample Script */}
              <div className="bg-gray-50 dark:bg-gray-900/50 rounded-lg p-4">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="font-semibold text-gray-900 dark:text-white flex items-center gap-2">
                    <FileAudio className="h-4 w-4" />
                    Sample Script
                  </h3>
                  <button
                    onClick={() => {
                      const newIndex = (SAMPLE_SCRIPTS.indexOf(currentScript) + 1) % SAMPLE_SCRIPTS.length;
                      setCurrentScript(SAMPLE_SCRIPTS[newIndex]);
                    }}
                    className="text-xs text-indigo-600 dark:text-indigo-400 hover:underline flex items-center gap-1"
                  >
                    <RotateCcw className="h-3 w-3" />
                    Next script
                  </button>
                </div>
                <p className="text-gray-700 dark:text-gray-300 leading-relaxed italic">
                  "{currentScript}"
                </p>
                <div className="mt-3 p-3 bg-blue-50 dark:bg-blue-900/20 rounded border border-blue-200 dark:border-blue-800">
                  <p className="text-xs text-blue-800 dark:text-blue-300">
                    💡 <strong>Tip:</strong> Speak clearly and naturally. Record 10-20 seconds for best results.
                  </p>
                </div>
              </div>

              {/* Recording Controls */}
              <div className="flex flex-col items-center gap-4">
                {!recordedBlob ? (
                  <>
                    <button
                      onClick={isRecording ? stopRecording : startRecording}
                      disabled={isUploading}
                      className={`p-8 rounded-full transition-all ${
                        isRecording
                          ? 'bg-red-500 hover:bg-red-600 animate-pulse'
                          : 'bg-indigo-600 hover:bg-indigo-700'
                      } disabled:opacity-50`}
                    >
                      {isRecording ? (
                        <Square className="h-12 w-12 text-white" />
                      ) : (
                        <Mic className="h-12 w-12 text-white" />
                      )}
                    </button>
                    <div className="text-center">
                      <p className="text-lg font-semibold text-gray-900 dark:text-white">
                        {isRecording ? 'Recording...' : 'Click to Start Recording'}
                      </p>
                      {isRecording && (
                        <p className="text-2xl font-mono text-red-600 dark:text-red-400 mt-2">
                          {formatTime(recordingTime)}
                        </p>
                      )}
                    </div>
                  </>
                ) : (
                  <>
                    <div className="flex items-center gap-4">
                      <CheckCircle className="h-8 w-8 text-green-600 dark:text-green-400" />
                      <div>
                        <p className="font-semibold text-gray-900 dark:text-white">
                          Recording Complete
                        </p>
                        <p className="text-sm text-gray-600 dark:text-gray-400">
                          Duration: {formatTime(recordingTime)}
                        </p>
                      </div>
                    </div>

                    <div className="flex gap-3">
                      <button
                        onClick={isPlaying ? pauseRecording : playRecording}
                        className="px-6 py-3 bg-green-600 hover:bg-green-700 text-white rounded-lg flex items-center gap-2 transition-colors"
                      >
                        {isPlaying ? (
                          <>
                            <Pause className="h-5 w-5" />
                            Pause
                          </>
                        ) : (
                          <>
                            <Play className="h-5 w-5" />
                            Play
                          </>
                        )}
                      </button>
                      <button
                        onClick={() => {
                          cleanup();
                        }}
                        className="px-6 py-3 bg-gray-600 hover:bg-gray-700 text-white rounded-lg flex items-center gap-2 transition-colors"
                      >
                        <RotateCcw className="h-5 w-5" />
                        Re-record
                      </button>
                    </div>
                  </>
                )}
              </div>
            </div>
          )}

          {/* Upload Mode */}
          {mode === 'upload' && (
            <div className="space-y-6">
              <button
                onClick={() => {
                  setMode('choice');
                  cleanup();
                }}
                className="text-sm text-indigo-600 dark:text-indigo-400 hover:underline flex items-center gap-1"
              >
                ← Back to options
              </button>

              <div className="border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-xl p-8 text-center">
                <Upload className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <label className="cursor-pointer">
                  <input
                    type="file"
                    accept="audio/*"
                    onChange={handleFileSelect}
                    className="hidden"
                  />
                  <span className="text-indigo-600 dark:text-indigo-400 hover:underline font-semibold">
                    Click to upload
                  </span>
                  <span className="text-gray-600 dark:text-gray-400"> or drag and drop</span>
                </label>
                <p className="text-sm text-gray-500 dark:text-gray-400 mt-2">
                  WAV, MP3, or WebM (max 10MB)
                </p>
              </div>

              {uploadFile && (
                <div className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-900/50 rounded-lg">
                  <div className="flex items-center gap-3">
                    <FileAudio className="h-8 w-8 text-indigo-600 dark:text-indigo-400" />
                    <div>
                      <p className="font-semibold text-gray-900 dark:text-white">
                        {uploadFile.name}
                      </p>
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        {(uploadFile.size / 1024 / 1024).toFixed(2)} MB
                      </p>
                    </div>
                  </div>
                  <button
                    onClick={() => setUploadFile(null)}
                    className="p-2 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-lg transition-colors"
                  >
                    <X className="h-5 w-5 text-gray-500" />
                  </button>
                </div>
              )}
            </div>
          )}

          {/* Actions */}
          {mode !== 'choice' && (
            <div className="space-y-4 mt-6 pt-6 border-t border-gray-200 dark:border-gray-700">
              {/* Test Voice Section with Visual Feedback */}
              <div className="space-y-3">
                <button
                  onClick={testVoice}
                  disabled={isTesting || isUploading}
                  className={`w-full px-6 py-4 rounded-lg flex items-center justify-center gap-3 transition-all font-semibold ${
                    isTesting 
                      ? 'bg-purple-500 text-white cursor-wait animate-pulse' 
                      : 'bg-purple-600 hover:bg-purple-700 text-white hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed'
                  }`}
                >
                  {isTesting ? (
                    <>
                      <Loader2 className="h-6 w-6 animate-spin" />
                      <div className="flex flex-col items-start">
                        <span>Synthesizing Voice...</span>
                        <span className="text-xs text-purple-200">This may take a few seconds</span>
                      </div>
                    </>
                  ) : (
                    <>
                      <Volume2 className="h-6 w-6" />
                      <div className="flex flex-col items-start">
                        <span>Test Voice with Current Sample</span>
                        <span className="text-xs text-purple-200">Preview how this personality sounds</span>
                      </div>
                    </>
                  )}
                </button>
                
                {isTesting && (
                  <div className="bg-purple-50 dark:bg-purple-900/20 border border-purple-200 dark:border-purple-800 rounded-lg p-4">
                    <div className="flex items-center gap-3 text-sm">
                      <div className="flex gap-1">
                        <div className="h-2 w-2 bg-purple-600 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                        <div className="h-2 w-2 bg-purple-600 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                        <div className="h-2 w-2 bg-purple-600 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                      </div>
                      <span className="text-purple-900 dark:text-purple-100 font-medium">
                        Processing voice synthesis... Please wait
                      </span>
                    </div>
                  </div>
                )}
              </div>

              {/* Upload Voice Button */}
              <button
                onClick={uploadVoice}
                disabled={!recordedBlob && !uploadFile || isUploading}
                className={`w-full px-6 py-4 rounded-lg flex items-center justify-center gap-3 transition-all font-semibold ${
                  isUploading
                    ? 'bg-indigo-500 text-white cursor-wait'
                    : 'bg-indigo-600 hover:bg-indigo-700 text-white hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed'
                }`}
              >
                {isUploading ? (
                  <>
                    <Loader2 className="h-6 w-6 animate-spin" />
                    <div className="flex flex-col items-start">
                      <span>Uploading Voice Sample...</span>
                      <span className="text-xs text-indigo-200">Converting and processing audio</span>
                    </div>
                  </>
                ) : (
                  <>
                    <Upload className="h-6 w-6" />
                    <div className="flex flex-col items-start">
                      <span>Upload Voice Sample</span>
                      <span className="text-xs text-indigo-200">Save this voice for the personality</span>
                    </div>
                  </>
                )}
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default VoiceRecordUploadModal;
