import React, { useState, useRef, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Mic, MicOff, Volume2, VolumeX, Upload, Download, AlertCircle, CheckCircle } from 'lucide-react';
import { appConfig } from '../config/app.config';

const VoiceAPITest: React.FC = () => {
  const { t } = useTranslation(['tools', 'common']);

  // State management
  const [isRecording, setIsRecording] = useState(false);
  const [recordedAudio, setRecordedAudio] = useState<Blob | null>(null);
  const [transcription, setTranscription] = useState('');
  const [isTranscribing, setIsTranscribing] = useState(false);
  const [synthesisText, setSynthesisText] = useState('');
  const [isSynthesizing, setIsSynthesizing] = useState(false);
  const [synthesizedAudio, setSynthesizedAudio] = useState<string | null>(null);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [apiEndpoint, setApiEndpoint] = useState(appConfig.api.baseUrl);
  const [selectedVoice, setSelectedVoice] = useState('en-US-Standard-A');
  const [voices, setVoices] = useState<any[]>([]);

  // Refs
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  // Fetch available voices on mount
  useEffect(() => {
    fetchVoices();
  }, [apiEndpoint]);

  const fetchVoices = async () => {
    try {
      const response = await fetch(`${apiEndpoint}/api/voice/voices`);
      if (response.ok) {
        const data = await response.json();
        setVoices(data.voices || []);
        setSuccess(t('tools:voiceApi.messages.voicesFetched'));
        setTimeout(() => setSuccess(''), 3000);
      } else {
        setError(t('tools:voiceApi.messages.voicesFailed'));
      }
    } catch (err) {
      console.error('Error fetching voices:', err);
      setVoices(['en-US-Standard-A', 'en-US-Standard-B', 'en-GB-Standard-A']); // Fallback voices
    }
  };

  // Start recording
  const startRecording = async () => {
    setError('');
    setSuccess('');

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

      // Create MediaRecorder with webm format
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
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        setRecordedAudio(audioBlob);
        stream.getTracks().forEach(track => track.stop());
        setSuccess(t('tools:voiceApi.messages.recordingSaved'));
        setTimeout(() => setSuccess(''), 3000);
      };

      mediaRecorder.start(100); // Collect data every 100ms
      setIsRecording(true);
      setTranscription('');
    } catch (err) {
      setError(t('tools:voiceApi.messages.recordingFailed') + ': ' + (err as Error).message);
      console.error('Recording error:', err);
    }
  };

  // Stop recording
  const stopRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  // Test transcription endpoint
  const testTranscription = async () => {
    if (!recordedAudio) {
      setError(t('tools:voiceApi.transcription.noAudio'));
      return;
    }

    setIsTranscribing(true);
    setError('');
    setTranscription('');

    try {
      const formData = new FormData();
      formData.append('audio', recordedAudio, 'recording.webm');
      formData.append('language', 'en');
      formData.append('mode', 'auto_vad');

      console.log('Sending transcription request to:', `${apiEndpoint}/api/voice/transcribe`);

      const response = await fetch(`${apiEndpoint}/api/voice/transcribe`, {
        method: 'POST',
        body: formData
      });

      const result = await response.json();
      console.log('Transcription response:', result);

      if (response.ok && result.status === 'success') {
        setTranscription(result.result?.text || t('tools:voiceApi.transcription.noTranscription'));
        setSuccess(t('tools:voiceApi.transcription.success'));
        setTimeout(() => setSuccess(''), 3000);
      } else {
        setError(result.error || t('tools:voiceApi.messages.transcriptionError'));
      }
    } catch (err) {
      setError(t('tools:voiceApi.messages.transcriptionError') + ': ' + (err as Error).message);
      console.error('Transcription error:', err);
    } finally {
      setIsTranscribing(false);
    }
  };

  // Test synthesis endpoint
  const testSynthesis = async () => {
    if (!synthesisText.trim()) {
      setError(t('tools:voiceApi.synthesis.noText'));
      return;
    }

    setIsSynthesizing(true);
    setError('');
    setSynthesizedAudio(null);

    try {
      const formData = new FormData();
      formData.append('text', synthesisText);
      formData.append('voice', selectedVoice);
      formData.append('speed', '1.0');
      formData.append('format', 'wav');

      console.log('Sending synthesis request to:', `${apiEndpoint}/api/voice/synthesize`);

      const response = await fetch(`${apiEndpoint}/api/voice/synthesize`, {
        method: 'POST',
        body: formData
      });

      if (response.ok) {
        const audioBlob = await response.blob();
        const audioUrl = URL.createObjectURL(audioBlob);
        setSynthesizedAudio(audioUrl);
        setSuccess(t('tools:voiceApi.synthesis.success'));
        setTimeout(() => setSuccess(''), 3000);
      } else {
        const error = await response.text();
        setError(t('tools:voiceApi.synthesis.failed') + ': ' + error);
      }
    } catch (err) {
      setError(t('tools:voiceApi.messages.synthesisError') + ': ' + (err as Error).message);
      console.error('Synthesis error:', err);
    } finally {
      setIsSynthesizing(false);
    }
  };

  // Play synthesized audio
  const playSynthesizedAudio = () => {
    if (synthesizedAudio && audioRef.current) {
      audioRef.current.src = synthesizedAudio;
      audioRef.current.play();
    }
  };

  // Play recorded audio
  const playRecordedAudio = () => {
    if (recordedAudio) {
      const audioUrl = URL.createObjectURL(recordedAudio);
      if (audioRef.current) {
        audioRef.current.src = audioUrl;
        audioRef.current.play();
      }
    }
  };

  return (
    <div className="p-3 sm:p-4 lg:p-6 max-w-4xl mx-auto">
      <h1 className="text-xl sm:text-2xl lg:text-3xl font-bold mb-4 sm:mb-6 text-gray-900 dark:text-white transition-colors">{t('tools:voiceApi.title')}</h1>

      {/* API Endpoint Configuration */}
      <div className="mb-4 sm:mb-6 p-3 sm:p-4 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg transition-colors">
        <label className="block text-sm font-medium mb-2 text-gray-700 dark:text-gray-300">{t('tools:voiceApi.apiEndpoint')}</label>
        <input
          type="text"
          value={apiEndpoint}
          onChange={(e) => setApiEndpoint(e.target.value)}
          className="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white rounded-md focus:ring-2 focus:ring-primary-500 dark:focus:ring-primary-400 focus:border-primary-500 dark:focus:border-primary-400 transition-colors text-sm"
          placeholder="API URL from environment"
        />
      </div>

      {/* Status Messages */}
      {error && (
        <div className="mb-4 p-3 sm:p-4 bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-300 border border-red-200 dark:border-red-700 rounded-lg flex items-center transition-colors">
          <AlertCircle className="mr-2 flex-shrink-0" size={20} />
          <span className="text-sm sm:text-base">{error}</span>
        </div>
      )}

      {success && (
        <div className="mb-4 p-3 sm:p-4 bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-300 border border-green-200 dark:border-green-700 rounded-lg flex items-center transition-colors">
          <CheckCircle className="mr-2 flex-shrink-0" size={20} />
          <span className="text-sm sm:text-base">{success}</span>
        </div>
      )}

      {/* Recording Section */}
      <div className="mb-6 sm:mb-8 p-4 sm:p-6 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-sm transition-colors">
        <h2 className="text-lg sm:text-xl font-semibold mb-3 sm:mb-4 text-gray-900 dark:text-white">{t('tools:voiceApi.recording.title')}</h2>

        <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3 sm:gap-4 mb-4">
          <button
            onClick={isRecording ? stopRecording : startRecording}
            className={`w-full sm:w-auto px-4 sm:px-6 py-2.5 sm:py-3 rounded-lg font-medium transition-all active:scale-95 touch-manipulation flex items-center justify-center gap-2 ${
              isRecording
                ? 'bg-red-500 dark:bg-red-600 hover:bg-red-600 dark:hover:bg-red-700 text-white'
                : 'bg-blue-500 dark:bg-blue-600 hover:bg-blue-600 dark:hover:bg-blue-700 text-white'
            }`}
          >
            {isRecording ? (
              <>
                <MicOff className="flex-shrink-0" size={20} />
                <span className="text-sm sm:text-base">{t('tools:voiceApi.recording.stop')}</span>
              </>
            ) : (
              <>
                <Mic className="flex-shrink-0" size={20} />
                <span className="text-sm sm:text-base">{t('tools:voiceApi.recording.start')}</span>
              </>
            )}
          </button>

          {recordedAudio && (
            <button
              onClick={playRecordedAudio}
              className="w-full sm:w-auto px-4 py-2.5 bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 text-gray-900 dark:text-white rounded-lg flex items-center justify-center gap-2 transition-all active:scale-95 touch-manipulation"
            >
              <Volume2 className="flex-shrink-0" size={20} />
              <span className="text-sm sm:text-base">{t('tools:voiceApi.recording.play')}</span>
            </button>
          )}
        </div>

        {isRecording && (
          <div className="text-sm text-gray-600 dark:text-gray-300 animate-pulse">
            {t('tools:voiceApi.recording.inProgress')}
          </div>
        )}

        {recordedAudio && (
          <div className="text-sm text-green-600 dark:text-green-400">
            {t('tools:voiceApi.recording.ready')}
          </div>
        )}
      </div>

      {/* Transcription Section */}
      <div className="mb-6 sm:mb-8 p-4 sm:p-6 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-sm transition-colors">
        <h2 className="text-lg sm:text-xl font-semibold mb-3 sm:mb-4 text-gray-900 dark:text-white">{t('tools:voiceApi.transcription.title')}</h2>

        <button
          onClick={testTranscription}
          disabled={!recordedAudio || isTranscribing}
          className={`w-full sm:w-auto px-4 sm:px-6 py-2.5 sm:py-3 rounded-lg font-medium transition-all active:scale-95 touch-manipulation flex items-center justify-center gap-2 ${
            !recordedAudio || isTranscribing
              ? 'bg-gray-300 dark:bg-gray-600 cursor-not-allowed text-gray-500 dark:text-gray-400'
              : 'bg-purple-500 dark:bg-purple-600 hover:bg-purple-600 dark:hover:bg-purple-700 text-white'
          }`}
        >
          <Upload className="flex-shrink-0" size={20} />
          <span className="text-sm sm:text-base">{isTranscribing ? t('tools:voiceApi.transcription.buttonLoading') : t('tools:voiceApi.transcription.button')}</span>
        </button>

        {transcription && (
          <div className="mt-4 p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-700 rounded-lg transition-colors">
            <h3 className="font-medium mb-2 text-gray-900 dark:text-white">{t('tools:voiceApi.transcription.result')}</h3>
            <p className="text-gray-700 dark:text-gray-300 text-sm sm:text-base">{transcription}</p>
          </div>
        )}
      </div>

      {/* Synthesis Section */}
      <div className="mb-6 sm:mb-8 p-4 sm:p-6 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-sm transition-colors">
        <h2 className="text-lg sm:text-xl font-semibold mb-3 sm:mb-4 text-gray-900 dark:text-white">{t('tools:voiceApi.synthesis.title')}</h2>

        <div className="mb-4">
          <label className="block text-sm font-medium mb-2 text-gray-700 dark:text-gray-300">{t('tools:voiceApi.synthesis.textLabel')}</label>
          <textarea
            value={synthesisText}
            onChange={(e) => setSynthesisText(e.target.value)}
            className="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white rounded-md focus:ring-2 focus:ring-primary-500 dark:focus:ring-primary-400 focus:border-primary-500 dark:focus:border-primary-400 transition-colors text-sm"
            rows={3}
            placeholder={t('tools:voiceApi.synthesis.textPlaceholder')}
          />
        </div>

        <div className="mb-4">
          <label className="block text-sm font-medium mb-2 text-gray-700 dark:text-gray-300">{t('tools:voiceApi.synthesis.voiceLabel')}</label>
          <select
            value={selectedVoice}
            onChange={(e) => setSelectedVoice(e.target.value)}
            className="w-full sm:w-auto px-3 py-2 border border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white rounded-md focus:ring-2 focus:ring-primary-500 dark:focus:ring-primary-400 focus:border-primary-500 dark:focus:border-primary-400 transition-colors text-sm"
          >
            {voices.map(voice => (
              <option key={typeof voice === 'string' ? voice : voice.id} value={typeof voice === 'string' ? voice : voice.id}>
                {typeof voice === 'string' ? voice : `${voice.name} (${voice.language}, ${voice.gender})`}
              </option>
            ))}
          </select>
        </div>

        <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3 sm:gap-4">
          <button
            onClick={testSynthesis}
            disabled={!synthesisText.trim() || isSynthesizing}
            className={`w-full sm:w-auto px-4 sm:px-6 py-2.5 sm:py-3 rounded-lg font-medium transition-all active:scale-95 touch-manipulation flex items-center justify-center gap-2 ${
              !synthesisText.trim() || isSynthesizing
                ? 'bg-gray-300 dark:bg-gray-600 cursor-not-allowed text-gray-500 dark:text-gray-400'
                : 'bg-green-500 dark:bg-green-600 hover:bg-green-600 dark:hover:bg-green-700 text-white'
            }`}
          >
            <Download className="flex-shrink-0" size={20} />
            <span className="text-sm sm:text-base">{isSynthesizing ? t('tools:voiceApi.synthesis.buttonLoading') : t('tools:voiceApi.synthesis.button')}</span>
          </button>

          {synthesizedAudio && (
            <button
              onClick={playSynthesizedAudio}
              className="w-full sm:w-auto px-4 py-2.5 bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 text-gray-900 dark:text-white rounded-lg flex items-center justify-center gap-2 transition-all active:scale-95 touch-manipulation"
            >
              <Volume2 className="flex-shrink-0" size={20} />
              <span className="text-sm sm:text-base">{t('tools:voiceApi.synthesis.play')}</span>
            </button>
          )}
        </div>
      </div>

      {/* Audio Player (hidden) */}
      <audio ref={audioRef} className="hidden" />

      {/* Debug Info */}
      <div className="mt-6 sm:mt-8 p-3 sm:p-4 bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg transition-colors">
        <h3 className="font-medium mb-2 text-gray-900 dark:text-white">{t('tools:voiceApi.debug.title')}</h3>
        <div className="text-xs sm:text-sm text-gray-600 dark:text-gray-300 space-y-1 break-all">
          <p><strong>{t('tools:voiceApi.debug.endpoint')}:</strong> {apiEndpoint}</p>
          <p><strong>{t('tools:voiceApi.debug.transcription')}:</strong> {apiEndpoint}/api/voice/transcribe</p>
          <p><strong>{t('tools:voiceApi.debug.synthesis')}:</strong> {apiEndpoint}/api/voice/synthesize</p>
          <p><strong>{t('tools:voiceApi.debug.voices')}:</strong> {apiEndpoint}/api/voice/voices</p>
        </div>
      </div>
    </div>
  );
};

export default VoiceAPITest;