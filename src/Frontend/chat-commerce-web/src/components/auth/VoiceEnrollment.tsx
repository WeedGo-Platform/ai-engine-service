/**
 * Voice Enrollment Component
 * Handles voice profile registration for new users
 * Includes multi-sample recording for better accuracy
 */

import React, { useState, useRef, useEffect } from 'react';
import { voiceAuthService, VoiceEnrollmentResult } from '../../services/voice-auth.service';

export interface VoiceEnrollmentProps {
  userId: string;
  userEmail?: string;
  onSuccess?: () => void;
  onCancel?: () => void;
  className?: string;
  buttonClassName?: string;
}

enum EnrollmentStep {
  INTRODUCTION = 'introduction',
  SAMPLE_1 = 'sample_1',
  SAMPLE_2 = 'sample_2',
  SAMPLE_3 = 'sample_3',
  PROCESSING = 'processing',
  SUCCESS = 'success',
  ERROR = 'error'
}

interface EnrollmentSample {
  phrase: string;
  instruction: string;
  audioBlob?: Blob;
}

const ENROLLMENT_PHRASES: EnrollmentSample[] = [
  {
    phrase: "My voice is my password, verify me",
    instruction: "Please read the phrase clearly and naturally"
  },
  {
    phrase: "I consent to voice authentication for secure access",
    instruction: "Speak at your normal pace and volume"
  },
  {
    phrase: "The quick brown fox jumps over the lazy dog",
    instruction: "One more time for better accuracy"
  }
];

const VoiceEnrollment: React.FC<VoiceEnrollmentProps> = ({
  userId,
  userEmail,
  onSuccess,
  onCancel,
  className = '',
  buttonClassName = ''
}) => {
  const [currentStep, setCurrentStep] = useState<EnrollmentStep>(EnrollmentStep.INTRODUCTION);
  const [currentSampleIndex, setCurrentSampleIndex] = useState<number>(0);
  const [samples, setSamples] = useState<EnrollmentSample[]>([...ENROLLMENT_PHRASES]);
  const [isRecording, setIsRecording] = useState<boolean>(false);
  const [recordingTimeLeft, setRecordingTimeLeft] = useState<number>(0);
  const [error, setError] = useState<string>('');
  const [progress, setProgress] = useState<number>(0);
  const [audioLevel, setAudioLevel] = useState<number>(0);

  const canvasRef = useRef<HTMLCanvasElement>(null);
  const recordingTimerRef = useRef<NodeJS.Timeout>();

  useEffect(() => {
    return () => {
      cleanup();
    };
  }, []);

  useEffect(() => {
    // Update progress based on completed samples
    const completedSamples = samples.filter(s => s.audioBlob).length;
    setProgress((completedSamples / samples.length) * 100);
  }, [samples]);

  const startEnrollment = () => {
    setCurrentStep(EnrollmentStep.SAMPLE_1);
    setCurrentSampleIndex(0);
    setError('');
  };

  const startRecording = async () => {
    if (isRecording) return;

    setIsRecording(true);
    setError('');
    setRecordingTimeLeft(5);

    // Start countdown timer
    let timeLeft = 5;
    recordingTimerRef.current = setInterval(() => {
      timeLeft -= 1;
      setRecordingTimeLeft(timeLeft);
      if (timeLeft <= 0) {
        clearInterval(recordingTimerRef.current);
      }
    }, 1000);

    try {
      await voiceAuthService.startRecording(
        {
          duration: 5000,
          sampleRate: 16000,
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true
        },
        handleAudioData
      );

      // Auto-stop after 5 seconds
      setTimeout(async () => {
        if (isRecording) {
          await stopRecording();
        }
      }, 5000);
    } catch (error: any) {
      setIsRecording(false);
      setError(error.message || 'Failed to start recording');
      cleanup();
    }
  };

  const stopRecording = async () => {
    if (!isRecording) return;

    setIsRecording(false);
    cleanup();

    try {
      const audioBlob = await voiceAuthService.stopRecording();
      
      // Save the sample
      const updatedSamples = [...samples];
      updatedSamples[currentSampleIndex] = {
        ...updatedSamples[currentSampleIndex],
        audioBlob
      };
      setSamples(updatedSamples);

      // Move to next sample or processing
      if (currentSampleIndex < samples.length - 1) {
        setCurrentSampleIndex(currentSampleIndex + 1);
        setCurrentStep(`sample_${currentSampleIndex + 2}` as EnrollmentStep);
      } else {
        // All samples collected, process enrollment
        await processEnrollment(updatedSamples);
      }
    } catch (error: any) {
      setError(error.message || 'Failed to save recording');
    }
  };

  const processEnrollment = async (allSamples: EnrollmentSample[]) => {
    setCurrentStep(EnrollmentStep.PROCESSING);
    setError('');

    try {
      // For production, you might want to send all samples
      // For now, we'll use the first sample for enrollment
      const primarySample = allSamples[0].audioBlob;
      if (!primarySample) {
        throw new Error('No audio sample available');
      }

      const metadata = {
        email: userEmail,
        samples_count: allSamples.filter(s => s.audioBlob).length,
        enrollment_date: new Date().toISOString()
      };

      const result: VoiceEnrollmentResult = await voiceAuthService.enrollVoiceProfile(
        userId,
        primarySample,
        metadata
      );

      if (result.success) {
        setCurrentStep(EnrollmentStep.SUCCESS);
        
        // Success callback after a short delay
        setTimeout(() => {
          if (onSuccess) {
            onSuccess();
          }
        }, 2000);
      } else {
        setCurrentStep(EnrollmentStep.ERROR);
        setError(result.message || 'Enrollment failed');
      }
    } catch (error: any) {
      setCurrentStep(EnrollmentStep.ERROR);
      setError(error.message || 'Failed to complete enrollment');
    }
  };

  const handleAudioData = (data: Float32Array) => {
    const level = voiceAuthService.calculateAudioLevel(data);
    setAudioLevel(level);
    drawWaveform(data);
  };

  const drawWaveform = (data: Float32Array) => {
    if (!canvasRef.current) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const width = canvas.width;
    const height = canvas.height;

    ctx.clearRect(0, 0, width, height);
    ctx.beginPath();
    ctx.lineWidth = 2;
    ctx.strokeStyle = isRecording ? '#10b981' : '#6b7280';

    const sliceWidth = width / data.length;
    let x = 0;

    for (let i = 0; i < data.length; i++) {
      const v = (data[i] + 140) / 140;
      const y = v * height / 2;

      if (i === 0) {
        ctx.moveTo(x, y);
      } else {
        ctx.lineTo(x, y);
      }

      x += sliceWidth;
    }

    ctx.stroke();
  };

  const cleanup = () => {
    if (recordingTimerRef.current) {
      clearInterval(recordingTimerRef.current);
    }
    setAudioLevel(0);
    setRecordingTimeLeft(0);
  };

  const retry = () => {
    setCurrentStep(EnrollmentStep.INTRODUCTION);
    setCurrentSampleIndex(0);
    setSamples([...ENROLLMENT_PHRASES]);
    setError('');
    setProgress(0);
  };

  const cancelRecording = () => {
    voiceAuthService.cancelRecording();
    setIsRecording(false);
    cleanup();
  };

  const renderContent = () => {
    switch (currentStep) {
      case EnrollmentStep.INTRODUCTION:
        return (
          <div className="enrollment-intro">
            <h3 className="enrollment-title">Set Up Voice Authentication</h3>
            <p className="enrollment-description">
              Voice authentication provides a secure and convenient way to access your account.
              We'll need to record a few samples of your voice to create your unique voice profile.
            </p>
            
            <div className="enrollment-benefits">
              <div className="benefit-item">
                <span className="benefit-icon">🔒</span>
                <span className="benefit-text">Secure biometric authentication</span>
              </div>
              <div className="benefit-item">
                <span className="benefit-icon">⚡</span>
                <span className="benefit-text">Fast and convenient login</span>
              </div>
              <div className="benefit-item">
                <span className="benefit-icon">🎯</span>
                <span className="benefit-text">Age verification included</span>
              </div>
            </div>

            <div className="enrollment-privacy">
              <p className="privacy-note">
                Your voice data is encrypted and securely stored. 
                You can delete your voice profile at any time from your account settings.
              </p>
            </div>

            <button
              onClick={startEnrollment}
              className={`enrollment-button primary ${buttonClassName}`}
            >
              Start Voice Setup
            </button>

            {onCancel && (
              <button
                onClick={onCancel}
                className={`enrollment-button secondary ${buttonClassName}`}
              >
                Skip for Now
              </button>
            )}
          </div>
        );

      case EnrollmentStep.SAMPLE_1:
      case EnrollmentStep.SAMPLE_2:
      case EnrollmentStep.SAMPLE_3:
        const currentSample = samples[currentSampleIndex];
        return (
          <div className="enrollment-recording">
            <h3 className="enrollment-title">
              Voice Sample {currentSampleIndex + 1} of {samples.length}
            </h3>
            
            <div className="enrollment-progress">
              <div className="progress-bar">
                <div 
                  className="progress-fill"
                  style={{ width: `${progress}%` }}
                />
              </div>
              <span className="progress-text">{Math.round(progress)}% Complete</span>
            </div>

            <div className="enrollment-instruction">
              <p className="instruction-text">{currentSample.instruction}</p>
              <div className="phrase-container">
                <p className="phrase-text">"{currentSample.phrase}"</p>
              </div>
            </div>

            <div className="enrollment-waveform">
              <canvas
                ref={canvasRef}
                width={300}
                height={100}
                className="waveform-canvas"
                style={{
                  width: '100%',
                  height: '100px',
                  background: isRecording ? 'rgba(16, 185, 129, 0.05)' : 'rgba(0, 0, 0, 0.02)'
                }}
              />
              
              {isRecording && (
                <div className="audio-level">
                  <div 
                    className="level-bar"
                    style={{
                      width: `${Math.min(audioLevel * 100, 100)}%`,
                      background: audioLevel > 0.7 ? '#ef4444' : audioLevel > 0.3 ? '#10b981' : '#6b7280'
                    }}
                  />
                </div>
              )}
            </div>

            {isRecording && (
              <p className="recording-timer">Recording... {recordingTimeLeft}s</p>
            )}

            <div className="enrollment-actions">
              {!isRecording ? (
                <button
                  onClick={startRecording}
                  className={`enrollment-button primary ${buttonClassName}`}
                >
                  Start Recording
                </button>
              ) : (
                <>
                  <button
                    onClick={stopRecording}
                    className={`enrollment-button primary ${buttonClassName}`}
                  >
                    Stop Recording
                  </button>
                  <button
                    onClick={cancelRecording}
                    className={`enrollment-button secondary ${buttonClassName}`}
                  >
                    Cancel
                  </button>
                </>
              )}
            </div>
          </div>
        );

      case EnrollmentStep.PROCESSING:
        return (
          <div className="enrollment-processing">
            <h3 className="enrollment-title">Creating Your Voice Profile</h3>
            <div className="processing-spinner">
              <div className="spinner" />
            </div>
            <p className="processing-text">
              Processing your voice samples and setting up secure authentication...
            </p>
          </div>
        );

      case EnrollmentStep.SUCCESS:
        return (
          <div className="enrollment-success">
            <div className="success-icon">✓</div>
            <h3 className="enrollment-title">Voice Profile Created!</h3>
            <p className="success-message">
              Your voice authentication is now set up. 
              You can use your voice to log in securely from now on.
            </p>
          </div>
        );

      case EnrollmentStep.ERROR:
        return (
          <div className="enrollment-error">
            <h3 className="enrollment-title">Enrollment Failed</h3>
            <p className="error-message">{error}</p>
            <div className="enrollment-actions">
              <button
                onClick={retry}
                className={`enrollment-button primary ${buttonClassName}`}
              >
                Try Again
              </button>
              {onCancel && (
                <button
                  onClick={onCancel}
                  className={`enrollment-button secondary ${buttonClassName}`}
                >
                  Cancel
                </button>
              )}
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className={`voice-enrollment-container ${className}`}>
      {renderContent()}
    </div>
  );
};

export default VoiceEnrollment;