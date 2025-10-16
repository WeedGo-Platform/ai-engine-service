import React, { useState, useRef, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Mic, MicOff, Volume2, VolumeX, Upload, Download, AlertCircle, CheckCircle } from 'lucide-react';

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
  const [apiEndpoint, setApiEndpoint] = useState('http://localhost:5024');
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
    <div className="p-6 max-w-4xl mx-auto">
      <h1 className="text-3xl font-bold mb-6">{t('tools:voiceApi.title')}</h1>

      {/* API Endpoint Configuration */}
      <div className="mb-6 p-4 bg-gray-50 rounded-lg">
        <label className="block text-sm font-medium mb-2">{t('tools:voiceApi.apiEndpoint')}</label>
        <input
          type="text"
          value={apiEndpoint}
          onChange={(e) => setApiEndpoint(e.target.value)}
          className="w-full px-3 py-2 border rounded-md"
          placeholder="http://localhost:5024"
        />
      </div>

      {/* Status Messages */}
      {error && (
        <div className="mb-4 p-4 bg-red-50 text-red-700 rounded-lg flex items-center">
          <AlertCircle className="mr-2" size={20} />
          {error}
        </div>
      )}

      {success && (
        <div className="mb-4 p-4 bg-green-50 text-green-700 rounded-lg flex items-center">
          <CheckCircle className="mr-2" size={20} />
          {success}
        </div>
      )}

      {/* Recording Section */}
      <div className="mb-8 p-6 bg-white border rounded-lg shadow-sm">
        <h2 className="text-xl font-semibold mb-4">{t('tools:voiceApi.recording.title')}</h2>

        <div className="flex items-center space-x-4 mb-4">
          <button
            onClick={isRecording ? stopRecording : startRecording}
            className={`px-6 py-3 rounded-lg font-medium transition-colors flex items-center ${
              isRecording
                ? 'bg-red-500 hover:bg-red-600 text-white'
                : 'bg-blue-500 hover:bg-blue-600 text-white'
            }`}
          >
            {isRecording ? (
              <>
                <MicOff className="mr-2" size={20} />
                {t('tools:voiceApi.recording.stop')}
              </>
            ) : (
              <>
                <Mic className="mr-2" size={20} />
                {t('tools:voiceApi.recording.start')}
              </>
            )}
          </button>

          {recordedAudio && (
            <button
              onClick={playRecordedAudio}
              className="px-4 py-2 bg-gray-200 hover:bg-gray-300 rounded-lg flex items-center"
            >
              <Volume2 className="mr-2" size={20} />
              {t('tools:voiceApi.recording.play')}
            </button>
          )}
        </div>

        {isRecording && (
          <div className="text-sm text-gray-600 animate-pulse">
            {t('tools:voiceApi.recording.inProgress')}
          </div>
        )}

        {recordedAudio && (
          <div className="text-sm text-green-600">
            {t('tools:voiceApi.recording.ready')}
          </div>
        )}
      </div>

      {/* Transcription Section */}
      <div className="mb-8 p-6 bg-white border rounded-lg shadow-sm">
        <h2 className="text-xl font-semibold mb-4">{t('tools:voiceApi.transcription.title')}</h2>

        <button
          onClick={testTranscription}
          disabled={!recordedAudio || isTranscribing}
          className={`px-6 py-3 rounded-lg font-medium transition-colors flex items-center ${
            !recordedAudio || isTranscribing
              ? 'bg-gray-300 cursor-not-allowed text-gray-500'
              : 'bg-purple-500 hover:bg-purple-600 text-white'
          }`}
        >
          <Upload className="mr-2" size={20} />
          {isTranscribing ? t('tools:voiceApi.transcription.buttonLoading') : t('tools:voiceApi.transcription.button')}
        </button>

        {transcription && (
          <div className="mt-4 p-4 bg-blue-50 rounded-lg">
            <h3 className="font-medium mb-2">{t('tools:voiceApi.transcription.result')}</h3>
            <p className="text-gray-700">{transcription}</p>
          </div>
        )}
      </div>

      {/* Synthesis Section */}
      <div className="mb-8 p-6 bg-white border rounded-lg shadow-sm">
        <h2 className="text-xl font-semibold mb-4">{t('tools:voiceApi.synthesis.title')}</h2>

        <div className="mb-4">
          <label className="block text-sm font-medium mb-2">{t('tools:voiceApi.synthesis.textLabel')}</label>
          <textarea
            value={synthesisText}
            onChange={(e) => setSynthesisText(e.target.value)}
            className="w-full px-3 py-2 border rounded-md"
            rows={3}
            placeholder={t('tools:voiceApi.synthesis.textPlaceholder')}
          />
        </div>

        <div className="mb-4">
          <label className="block text-sm font-medium mb-2">{t('tools:voiceApi.synthesis.voiceLabel')}</label>
          <select
            value={selectedVoice}
            onChange={(e) => setSelectedVoice(e.target.value)}
            className="px-3 py-2 border rounded-md"
          >
            {voices.map(voice => (
              <option key={typeof voice === 'string' ? voice : voice.id} value={typeof voice === 'string' ? voice : voice.id}>
                {typeof voice === 'string' ? voice : `${voice.name} (${voice.language}, ${voice.gender})`}
              </option>
            ))}
          </select>
        </div>

        <div className="flex items-center space-x-4">
          <button
            onClick={testSynthesis}
            disabled={!synthesisText.trim() || isSynthesizing}
            className={`px-6 py-3 rounded-lg font-medium transition-colors flex items-center ${
              !synthesisText.trim() || isSynthesizing
                ? 'bg-gray-300 cursor-not-allowed text-gray-500'
                : 'bg-green-500 hover:bg-green-600 text-white'
            }`}
          >
            <Download className="mr-2" size={20} />
            {isSynthesizing ? t('tools:voiceApi.synthesis.buttonLoading') : t('tools:voiceApi.synthesis.button')}
          </button>

          {synthesizedAudio && (
            <button
              onClick={playSynthesizedAudio}
              className="px-4 py-2 bg-gray-200 hover:bg-gray-300 rounded-lg flex items-center"
            >
              <Volume2 className="mr-2" size={20} />
              {t('tools:voiceApi.synthesis.play')}
            </button>
          )}
        </div>
      </div>

      {/* Audio Player (hidden) */}
      <audio ref={audioRef} className="hidden" />

      {/* Debug Info */}
      <div className="mt-8 p-4 bg-gray-100 rounded-lg">
        <h3 className="font-medium mb-2">{t('tools:voiceApi.debug.title')}</h3>
        <div className="text-sm text-gray-600 space-y-1">
          <p>{t('tools:voiceApi.debug.endpoint')}: {apiEndpoint}</p>
          <p>{t('tools:voiceApi.debug.transcription')}: {apiEndpoint}/api/voice/transcribe</p>
          <p>{t('tools:voiceApi.debug.synthesis')}: {apiEndpoint}/api/voice/synthesize</p>
          <p>{t('tools:voiceApi.debug.voices')}: {apiEndpoint}/api/voice/voices</p>
        </div>
      </div>
    </div>
  );
};

export default VoiceAPITest;