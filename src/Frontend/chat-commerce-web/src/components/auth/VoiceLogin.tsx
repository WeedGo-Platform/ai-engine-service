/**
 * Voice Login Component
 * Provides voice-based authentication with visual feedback and accessibility features
 * Template-agnostic implementation that can be styled by each template
 */

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { voiceAuthService, VoiceAuthResult } from '../../services/voice-auth.service';
import { useAuth } from '../../contexts/AuthContext';

export interface VoiceLoginProps {
  onSuccess?: (user: any) => void;
  onCancel?: () => void;
  onEnrollRequired?: (email: string) => void;
  onRegister?: () => void;
  onClose?: () => void;
  className?: string;
  buttonClassName?: string;
  waveformClassName?: string;
  showAgeVerification?: boolean;
}

export enum VoiceLoginState {
  IDLE = 'idle',
  CHECKING_SUPPORT = 'checking_support',
  REQUESTING_PERMISSION = 'requesting_permission',
  READY = 'ready',
  COUNTDOWN = 'countdown',
  RECORDING = 'recording',
  PROCESSING = 'processing',
  SUCCESS = 'success',
  ERROR = 'error',
  ENROLLMENT_REQUIRED = 'enrollment_required',
  AGE_VERIFICATION_FAILED = 'age_verification_failed'
}

interface AudioVisualizationData {
  level: number;
  frequencies: Float32Array;
}

const VoiceLogin: React.FC<VoiceLoginProps> = ({
  onSuccess,
  onCancel,
  onEnrollRequired,
  onRegister,
  onClose,
  className = '',
  buttonClassName = '',
  waveformClassName = '',
  showAgeVerification = true
}) => {
  const { login } = useAuth();
  const [state, setState] = useState<VoiceLoginState>(VoiceLoginState.IDLE);
  const [error, setError] = useState<string>('');
  const [audioLevel, setAudioLevel] = useState<number>(0);
  const [recordingTimeLeft, setRecordingTimeLeft] = useState<number>(0);
  const [countdownTime, setCountdownTime] = useState<number>(3);
  const [isSupported, setIsSupported] = useState<boolean>(true);
  const [hasPermission, setHasPermission] = useState<boolean>(false);
  const [ageInfo, setAgeInfo] = useState<{ verified: boolean; estimated_age?: number } | null>(null);
  const [autoStartTriggered, setAutoStartTriggered] = useState<boolean>(false);
  const [transcript, setTranscript] = useState<string>('');
  const [interimTranscript, setInterimTranscript] = useState<string>('');
  const [silenceStart, setSilenceStart] = useState<number>(0);
  const [speechDetected, setSpeechDetected] = useState<boolean>(false);
  const [minRecordingTime, setMinRecordingTime] = useState<number>(2000); // Minimum 2 seconds recording
  
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationFrameRef = useRef<number>();
  const recordingTimerRef = useRef<NodeJS.Timeout>();
  const recognitionRef = useRef<any>(null);
  const silenceCheckRef = useRef<NodeJS.Timeout>();
  const recordingStartTime = useRef<number>(0);
  const stopRecordingRef = useRef<(() => void) | null>(null);
  const isStoppingRecording = useRef<boolean>(false);

  // Store stopRecording reference for use in callbacks
  useEffect(() => {
    stopRecordingRef.current = stopRecording;
  });

  useEffect(() => {
    checkBrowserSupport();
    // Auto-start when component mounts (user selected voice tab)
    if (!autoStartTriggered) {
      setAutoStartTriggered(true);
      setTimeout(() => {
        if (state === VoiceLoginState.IDLE || state === VoiceLoginState.READY) {
          handleAutoStart();
        }
      }, 500);
    }
    return () => {
      cleanup();
    };
  }, []);

  const checkBrowserSupport = async () => {
    setState(VoiceLoginState.CHECKING_SUPPORT);
    const supported = voiceAuthService.isSupported();
    setIsSupported(supported);

    if (!supported) {
      setState(VoiceLoginState.ERROR);
      setError('Voice authentication is not supported in this browser. Please use Chrome, Edge, or Safari.');
      return;
    }

    // Check if we already have permission
    try {
      const permissionStatus = await navigator.permissions.query({ name: 'microphone' as PermissionName });
      if (permissionStatus.state === 'granted') {
        setHasPermission(true);
        setState(VoiceLoginState.READY);
      } else {
        setState(VoiceLoginState.IDLE);
      }
    } catch {
      // Permissions API might not be available
      setState(VoiceLoginState.IDLE);
    }
  };

  const requestPermission = async () => {
    setState(VoiceLoginState.REQUESTING_PERMISSION);
    setError('');

    const granted = await voiceAuthService.requestMicrophonePermission();
    setHasPermission(granted);

    if (granted) {
      setState(VoiceLoginState.READY);
      // Immediately start countdown after permission granted
      startCountdownAndRecord();
    } else {
      setState(VoiceLoginState.ERROR);
      setError('Microphone permission is required for voice login. Please grant permission and try again.');
    }
  };

  const handleAutoStart = async () => {
    if (!hasPermission) {
      await requestPermission();
    } else {
      startCountdownAndRecord();
    }
  };

  const startCountdownAndRecord = () => {
    setState(VoiceLoginState.COUNTDOWN);
    setCountdownTime(3);
    
    let count = 3;
    const countdownInterval = setInterval(() => {
      count -= 1;
      setCountdownTime(count);
      
      if (count <= 0) {
        clearInterval(countdownInterval);
        startRecording();
      }
    }, 1000);
  };

  const startRecording = async () => {
    setState(VoiceLoginState.RECORDING);
    setError('');
    setRecordingTimeLeft(10);
    setTranscript('');
    setInterimTranscript('');
    isStoppingRecording.current = false; // Reset the flag
    setSilenceStart(0);
    setSpeechDetected(false);
    recordingStartTime.current = Date.now();

    // Start speech recognition for transcript
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      const SpeechRecognition = (window as any).webkitSpeechRecognition || (window as any).SpeechRecognition;
      recognitionRef.current = new SpeechRecognition();
      recognitionRef.current.continuous = true;
      recognitionRef.current.interimResults = true;
      recognitionRef.current.lang = 'en-US';

      recognitionRef.current.onresult = (event: any) => {
        let finalTranscript = '';
        let interimTranscript = '';

        for (let i = event.resultIndex; i < event.results.length; i++) {
          const transcript = event.results[i][0].transcript;
          if (event.results[i].isFinal) {
            finalTranscript += transcript + ' ';
          } else {
            interimTranscript += transcript;
          }
        }

        if (finalTranscript) {
          setTranscript((prev) => prev + finalTranscript);
          setSpeechDetected(true); // Mark that we've detected speech
        }
        setInterimTranscript(interimTranscript);
      };

      recognitionRef.current.onerror = (event: any) => {
        console.warn('Speech recognition error:', event.error);
      };

      try {
        recognitionRef.current.start();
      } catch (err) {
        console.warn('Speech recognition failed to start:', err);
      }
    }

    // Start countdown timer for maximum 10 seconds
    let timeLeft = 10;
    recordingTimerRef.current = setInterval(() => {
      timeLeft -= 1;
      setRecordingTimeLeft(timeLeft);
      if (timeLeft <= 0) {
        clearInterval(recordingTimerRef.current);
        // Force stop at 10 seconds even if still speaking
        if (state === VoiceLoginState.RECORDING) {
          stopRecording();
        }
      }
    }, 1000);

    try {
      await voiceAuthService.startRecording(
        {
          duration: 10000,
          sampleRate: 16000,
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true
        },
        handleAudioData
      );

      // Auto-stop after 30 seconds (max recording time)
      const maxRecordingTimer = setTimeout(() => {
        if (state === VoiceLoginState.RECORDING) {
          console.log('Max recording time reached, stopping...');
          stopRecording();
        }
      }, 30000);
      
      // Store timer reference for cleanup
      recordingTimerRef.current = maxRecordingTimer as any;
    } catch (error: any) {
      console.error('Failed to start recording:', error);
      setState(VoiceLoginState.ERROR);
      setError(error.message || 'Failed to start recording. Please check your microphone.');
      // Ensure microphone is disposed on error
      voiceAuthService.cancelRecording();
      cleanup();
    }
  };

  const stopRecording = async () => {
    if (state !== VoiceLoginState.RECORDING) return;
    
    // Prevent duplicate calls using a flag
    if (isStoppingRecording.current) return;
    isStoppingRecording.current = true;

    // Stop speech recognition
    if (recognitionRef.current) {
      try {
        recognitionRef.current.stop();
      } catch (err) {
        console.log('Speech recognition already stopped');
      }
      recognitionRef.current = null;
    }

    setState(VoiceLoginState.PROCESSING);

    try {
      const audioBlob = await voiceAuthService.stopRecording();
      cleanup(); // Clean up after successfully getting the blob
      await processAuthentication(audioBlob);
    } catch (error: any) {
      console.error('Error stopping recording:', error);
      // Ensure microphone is disposed on error
      voiceAuthService.cancelRecording();
      cleanup();
      
      // Check if it's the "No recording in progress" error and handle gracefully
      if (error.message?.includes('No recording in progress')) {
        setState(VoiceLoginState.ERROR);
        setError('Recording failed. Please ensure your microphone is working and try again.');
      } else {
        setState(VoiceLoginState.ERROR);
        setError(error.message || 'Failed to process recording. Please try again.');
      }
    } finally {
      // Reset the flag
      isStoppingRecording.current = false;
    }
  };

  const cancelRecording = () => {
    // Stop speech recognition
    if (recognitionRef.current) {
      recognitionRef.current.stop();
      recognitionRef.current = null;
    }
    voiceAuthService.cancelRecording();
    cleanup();
    setState(VoiceLoginState.READY);
    setError('');
    setTranscript('');
    setInterimTranscript('');
  };

  const processAuthentication = async (audioBlob: Blob) => {
    try {
      const result: VoiceAuthResult = await voiceAuthService.authenticateVoice(audioBlob);

      // Always show age info if available, regardless of auth success
      if (result.age_info) {
        setAgeInfo({
          verified: result.age_info.verified,
          estimated_age: result.age_info.estimated_age
        });
      }

      if (result.success && result.authenticated && result.user) {
        // Check age verification if required
        if (showAgeVerification && result.age_info && !result.age_info.verified) {
          setState(VoiceLoginState.AGE_VERIFICATION_FAILED);
          setError('Age verification failed. You must be 21 or older to access this service.');
          return;
        }

        // Login successful
        setState(VoiceLoginState.SUCCESS);
        
        // Store auth token and user info
        if (result.user) {
          await login({
            email: result.user.email,
            password: '' // Voice auth doesn't use password
          });
        }

        if (onSuccess) {
          onSuccess(result.user);
        }
      } else if (!result.authenticated && (result.message?.includes('not found') || result.message?.includes('No voice profile'))) {
        // Voice profile not enrolled
        setState(VoiceLoginState.ENROLLMENT_REQUIRED);
        setError('No voice profile found for this voice.');
        
        // Don't auto-trigger enrollment, let user choose
      } else {
        // Authentication failed - still show age if available
        setState(VoiceLoginState.ERROR);
        setError(result.message || 'Voice authentication failed. Please try again.');
      }
    } catch (error: any) {
      // Check if it's a network/API error
      if (error.message?.includes('404') || error.message?.includes('not found')) {
        setState(VoiceLoginState.ENROLLMENT_REQUIRED);
        setError('Voice profile not found.');
      } else {
        setState(VoiceLoginState.ERROR);
        setError('Voice authentication failed. Please try again.');
      }
    }
  };

  const handleAudioData = useCallback((data: Float32Array) => {
    const level = voiceAuthService.calculateAudioLevel(data);
    setAudioLevel(level);
    drawWaveform(data);
    
    // Voice Activity Detection
    if (state === VoiceLoginState.RECORDING) {
      const SILENCE_THRESHOLD = 0.02; // Adjust based on testing
      const SILENCE_DURATION = 3000; // 3 seconds of silence to stop
      
      if (level > SILENCE_THRESHOLD) {
        // Speech detected
        setSpeechDetected(true);
        setSilenceStart(0);
      } else if (speechDetected) {
        // Silence detected after speech
        if (silenceStart === 0) {
          setSilenceStart(Date.now());
        } else {
          const silenceDuration = Date.now() - silenceStart;
          const recordingDuration = Date.now() - recordingStartTime.current;
          
          // Auto-stop if:
          // 1. Minimum recording time has passed (2 seconds)
          // 2. Speech was detected
          // 3. Silence duration exceeds threshold
          if (recordingDuration > minRecordingTime && silenceDuration > SILENCE_DURATION) {
            // Set state to processing immediately to update UI
            setState(VoiceLoginState.PROCESSING);
            // Trigger stop recording in next tick to avoid circular dependency
            setTimeout(() => {
              stopRecordingRef.current?.();
            }, 0);
          }
        }
      }
    }
  }, [state, speechDetected, silenceStart, minRecordingTime]);

  const drawWaveform = (data: Float32Array) => {
    if (!canvasRef.current) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const width = canvas.width;
    const height = canvas.height;

    // Clear canvas
    ctx.clearRect(0, 0, width, height);

    // Draw waveform
    ctx.beginPath();
    ctx.lineWidth = 3;
    ctx.strokeStyle = state === VoiceLoginState.RECORDING ? '#10b981' : '#6b7280';

    const sliceWidth = width / data.length;
    let x = 0;

    for (let i = 0; i < data.length; i++) {
      const v = data[i] * 0.5 + 0.5; // Normalize differently for better visualization
      const y = v * height;

      if (i === 0) {
        ctx.moveTo(x, y);
      } else {
        ctx.lineTo(x, y);
      }

      x += sliceWidth;
    }

    ctx.stroke();

    // Add center line
    ctx.beginPath();
    ctx.strokeStyle = 'rgba(147, 51, 234, 0.2)';
    ctx.lineWidth = 1;
    ctx.moveTo(0, height / 2);
    ctx.lineTo(width, height / 2);
    ctx.stroke();
  };

  const cleanup = () => {
    if (recordingTimerRef.current) {
      clearTimeout(recordingTimerRef.current);
      clearInterval(recordingTimerRef.current);
      recordingTimerRef.current = null;
    }
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
      animationFrameRef.current = null;
    }
    if (recognitionRef.current) {
      try {
        recognitionRef.current.stop();
      } catch (err) {
        // Ignore errors when stopping
      }
      recognitionRef.current = null;
    }
    setAudioLevel(0);
    setRecordingTimeLeft(0);
    setSpeechDetected(false);
    setSilenceStart(0);
  };

  const retry = () => {
    setState(VoiceLoginState.READY);
    setError('');
    setAgeInfo(null);
    setTranscript('');
    setInterimTranscript('');
  };

  const getStatusMessage = (): string => {
    switch (state) {
      case VoiceLoginState.CHECKING_SUPPORT:
        return 'Checking browser support...';
      case VoiceLoginState.REQUESTING_PERMISSION:
        return 'Please allow microphone access...';
      case VoiceLoginState.READY:
        return 'Ready to authenticate with your voice';
      case VoiceLoginState.COUNTDOWN:
        return `Get ready to speak in ${countdownTime}...`;
      case VoiceLoginState.RECORDING:
        return speechDetected ? 
          `🎤 Recording... (stops after 3 seconds of silence)` :
          `🎤 Speak now: "My name is [your name] and I authorize this login" (${recordingTimeLeft}s)`;
      case VoiceLoginState.PROCESSING:
        return 'Auto-processing your voice authentication...';
      case VoiceLoginState.SUCCESS:
        return '✅ Voice authenticated successfully!';
      case VoiceLoginState.ERROR:
        return error || 'Authentication failed';
      case VoiceLoginState.ENROLLMENT_REQUIRED:
        return 'Voice profile not found';
      case VoiceLoginState.AGE_VERIFICATION_FAILED:
        return 'Age verification failed';
      default:
        return 'Voice authentication';
    }
  };

  const getButtonText = (): string => {
    switch (state) {
      case VoiceLoginState.IDLE:
        return hasPermission ? 'Start Voice Login' : 'Enable Voice Login';
      case VoiceLoginState.READY:
        return 'Start Recording';
      case VoiceLoginState.RECORDING:
        return 'Stop Recording';
      case VoiceLoginState.PROCESSING:
        return 'Processing...';
      case VoiceLoginState.SUCCESS:
        return 'Success!';
      case VoiceLoginState.ERROR:
      case VoiceLoginState.AGE_VERIFICATION_FAILED:
        return 'Try Again';
      case VoiceLoginState.ENROLLMENT_REQUIRED:
        return 'Try Again';
      default:
        return 'Voice Login';
    }
  };

  const handleButtonClick = () => {
    switch (state) {
      case VoiceLoginState.IDLE:
        if (!hasPermission) {
          requestPermission();
        } else {
          setState(VoiceLoginState.READY);
        }
        break;
      case VoiceLoginState.READY:
        startRecording();
        break;
      case VoiceLoginState.RECORDING:
        stopRecording();
        break;
      case VoiceLoginState.PROCESSING:
        // Do nothing - already processing
        break;
      case VoiceLoginState.ERROR:
      case VoiceLoginState.AGE_VERIFICATION_FAILED:
        retry();
        break;
      case VoiceLoginState.ENROLLMENT_REQUIRED:
        if (onEnrollRequired) {
          onEnrollRequired('');
        }
        break;
    }
  };

  const isButtonDisabled = (): boolean => {
    return state === VoiceLoginState.CHECKING_SUPPORT ||
           state === VoiceLoginState.REQUESTING_PERMISSION ||
           state === VoiceLoginState.PROCESSING ||
           state === VoiceLoginState.SUCCESS ||
           !isSupported;
  };

  return (
    <div className={`voice-login-container ${className}`} style={{ padding: '20px' }}>
      <div className="voice-login-header" style={{ textAlign: 'center', marginBottom: '20px' }}>
        <h3 className="voice-login-title" style={{ fontSize: '20px', fontWeight: 'bold', marginBottom: '8px' }}>Voice Authentication</h3>
        <p className="voice-login-subtitle" style={{ fontSize: '14px', color: '#666', marginBottom: '8px' }}>
          Use your voice to securely log in
        </p>
        {state === VoiceLoginState.READY && (
          <p style={{ fontSize: '12px', color: '#9333ea', fontStyle: 'italic' }}>
            💡 Tip: Say "My name is [your name] and I authorize this login"
          </p>
        )}
      </div>

      {/* Audio Waveform Visualization */}
      <div className={`voice-login-waveform ${waveformClassName}`} style={{ marginBottom: '20px', position: 'relative' }}>
        <canvas
          ref={canvasRef}
          width={300}
          height={100}
          className="voice-login-canvas"
          style={{
            width: '100%',
            height: '100px',
            background: state === VoiceLoginState.RECORDING ? 'rgba(16, 185, 129, 0.05)' : 'rgba(147, 51, 234, 0.02)',
            border: state === VoiceLoginState.RECORDING ? '3px solid #10b981' : '2px solid rgba(147, 51, 234, 0.2)',
            borderRadius: '8px',
            transition: 'all 0.3s ease',
            animation: state === VoiceLoginState.RECORDING ? 'pulse 2s infinite' : 'none'
          }}
        />
        {state === VoiceLoginState.COUNTDOWN && (
          <div style={{
            position: 'absolute',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            fontSize: '48px',
            fontWeight: 'bold',
            color: '#9333ea',
            animation: 'fadeInOut 1s'
          }}>
            {countdownTime}
          </div>
        )}
        
        {/* Audio Level Indicator */}
        {state === VoiceLoginState.RECORDING && (
          <div className="voice-login-level" style={{ 
            marginTop: '10px', 
            height: '6px', 
            background: 'rgba(0,0,0,0.1)', 
            borderRadius: '3px',
            overflow: 'hidden'
          }}>
            <div 
              className="voice-login-level-bar"
              style={{
                width: `${Math.min(audioLevel * 100, 100)}%`,
                height: '100%',
                background: audioLevel > 0.7 ? '#ef4444' : audioLevel > 0.3 ? '#10b981' : '#6b7280',
                transition: 'width 0.1s ease',
                borderRadius: '3px'
              }}
            />
          </div>
        )}
      </div>

      {/* Real-time Transcript Display */}
      {state === VoiceLoginState.RECORDING && (
        <div style={{
          marginTop: '15px',
          padding: '15px',
          background: 'rgba(147, 51, 234, 0.05)',
          border: '2px solid rgba(147, 51, 234, 0.2)',
          borderRadius: '8px',
          minHeight: '60px'
        }}>
          <div style={{
            fontSize: '12px',
            color: '#9333ea',
            marginBottom: '8px',
            fontWeight: 'bold',
            textTransform: 'uppercase',
            letterSpacing: '1px'
          }}>
            🎙️ Live Transcript:
          </div>
          <div style={{
            fontSize: '16px',
            color: '#333',
            minHeight: '24px',
            fontStyle: transcript || interimTranscript ? 'normal' : 'italic'
          }}>
            {transcript || ''}
            <span style={{ color: '#999' }}>{interimTranscript}</span>
            {!transcript && !interimTranscript && (
              <span style={{ color: '#999' }}>Listening... (speak clearly)</span>
            )}
          </div>
          {speechDetected && silenceStart > 0 && (
            <div style={{
              fontSize: '11px',
              color: '#666',
              marginTop: '5px',
              fontStyle: 'italic'
            }}>
              ⏸️ Detecting silence... will stop automatically
            </div>
          )}
        </div>
      )}

      {/* Status Message */}
      <div className="voice-login-status" style={{ marginBottom: '20px', textAlign: 'center' }}>
        <p className={`voice-login-message ${state === VoiceLoginState.ERROR ? 'error' : ''}`} 
           style={{ 
             fontSize: state === VoiceLoginState.RECORDING ? '16px' : '14px',
             fontWeight: state === VoiceLoginState.RECORDING ? 'bold' : 'normal',
             color: state === VoiceLoginState.ERROR ? '#ef4444' : 
                    state === VoiceLoginState.RECORDING ? '#10b981' : 
                    state === VoiceLoginState.SUCCESS ? '#10b981' : '#666',
             minHeight: '40px',
             padding: '10px',
             background: state === VoiceLoginState.RECORDING ? 'rgba(16, 185, 129, 0.1)' : 'transparent',
             borderRadius: '8px',
             transition: 'all 0.3s ease'
           }}>
          {getStatusMessage()}
        </p>
        
        {/* Age Verification Info - Always show if available */}
        {ageInfo && (
          <div className="voice-login-age-info" style={{
            marginTop: '10px',
            padding: '10px',
            background: ageInfo.verified ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)',
            border: `2px solid ${ageInfo.verified ? 'rgba(16, 185, 129, 0.3)' : 'rgba(239, 68, 68, 0.3)'}`,
            borderRadius: '8px'
          }}>
            <p className={`age-verification ${ageInfo.verified ? 'verified' : 'not-verified'}`} style={{
              margin: 0,
              color: ageInfo.verified ? '#10b981' : '#ef4444',
              fontWeight: 'bold',
              fontSize: '14px'
            }}>
              {ageInfo.verified ? '✓ Age verified' : '✗ Age verification failed'}
              {ageInfo.estimated_age && (
                <span style={{ fontWeight: 'normal', marginLeft: '8px' }}>
                  (Detected age range: {ageInfo.estimated_age})
                </span>
              )}
            </p>
          </div>
        )}
      </div>

      {/* Action Buttons */}
      <div className="voice-login-actions" style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
        {/* Show enrollment options when voice not found */}
        {state === VoiceLoginState.ENROLLMENT_REQUIRED && (
          <div style={{
            padding: '15px',
            background: 'rgba(255, 193, 7, 0.1)',
            border: '2px solid rgba(255, 193, 7, 0.3)',
            borderRadius: '8px',
            marginBottom: '10px'
          }}>
            <p style={{ fontSize: '14px', color: '#856404', marginBottom: '10px', fontWeight: 'bold' }}>
              🎯 Voice not recognized
            </p>
            <p style={{ fontSize: '13px', color: '#666', marginBottom: '15px' }}>
              Your voice profile wasn't found. You can:
            </p>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              <button
                onClick={() => {
                  if (onRegister) {
                    onClose();
                    onRegister();
                  }
                }}
                style={{
                  padding: '10px',
                  background: '#28a745',
                  color: 'white',
                  border: 'none',
                  borderRadius: '6px',
                  fontWeight: 'bold',
                  cursor: 'pointer'
                }}
              >
                🆕 Register New Account
              </button>
              <button
                onClick={() => {
                  if (onCancel) {
                    onCancel();
                  }
                }}
                style={{
                  padding: '10px',
                  background: '#007bff',
                  color: 'white',
                  border: 'none',
                  borderRadius: '6px',
                  fontWeight: 'bold',
                  cursor: 'pointer'
                }}
              >
                🔑 Login First, Then Setup Voice
              </button>
            </div>
          </div>
        )}

        <button
          onClick={handleButtonClick}
          disabled={isButtonDisabled()}
          className={buttonClassName || 'voice-login-button primary'}
          style={!buttonClassName ? {
            width: '100%',
            padding: '12px 20px',
            backgroundColor: isButtonDisabled() ? '#ccc' : state === VoiceLoginState.ENROLLMENT_REQUIRED ? '#6c757d' : '#9333ea',
            color: 'white',
            border: 'none',
            borderRadius: '8px',
            fontSize: '16px',
            fontWeight: 'bold',
            cursor: isButtonDisabled() ? 'not-allowed' : 'pointer',
            transition: 'all 0.3s'
          } : {}}
          aria-label={getButtonText()}
        >
          {getButtonText()}
        </button>

        {state === VoiceLoginState.RECORDING && (
          <button
            onClick={cancelRecording}
            className={`voice-login-button secondary ${buttonClassName}`}
            aria-label="Cancel recording"
          >
            Cancel
          </button>
        )}

        {onCancel && state !== VoiceLoginState.RECORDING && state !== VoiceLoginState.PROCESSING && (
          <button
            onClick={onCancel}
            className={`voice-login-button tertiary ${buttonClassName}`}
            aria-label="Use different login method"
          >
            Use Different Method
          </button>
        )}
      </div>

      {/* Accessibility Information */}
      <div className="voice-login-accessibility sr-only" role="status" aria-live="polite">
        {getStatusMessage()}
      </div>
      <style>
        {`
          @keyframes pulse {
            0% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.4); }
            70% { box-shadow: 0 0 0 10px rgba(16, 185, 129, 0); }
            100% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
          }
          @keyframes fadeInOut {
            0% { opacity: 0; transform: translate(-50%, -50%) scale(0.5); }
            50% { opacity: 1; transform: translate(-50%, -50%) scale(1.2); }
            100% { opacity: 1; transform: translate(-50%, -50%) scale(1); }
          }
        `}
      </style>
    </div>
  );
};

export default VoiceLogin;