import React, { useRef, useEffect, useCallback } from 'react';
import { AudioVisualizationData } from '../services/voiceRecording.service';

interface VoiceVisualizationProps {
  data: AudioVisualizationData | null;
  isRecording: boolean;
  width?: number;
  height?: number;
  waveColor?: string;
  backgroundColor?: string;
}

export const VoiceVisualization: React.FC<VoiceVisualizationProps> = ({
  data,
  isRecording,
  width = 300,
  height = 100,
  waveColor = '#22C55E',
  backgroundColor = '#1F2937'
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationIdRef = useRef<number>();

  const drawWaveform = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Clear canvas
    ctx.fillStyle = backgroundColor;
    ctx.fillRect(0, 0, width, height);

    if (!data || !isRecording) {
      // Draw idle state (flat line)
      ctx.strokeStyle = waveColor + '40'; // Add transparency
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.moveTo(0, height / 2);
      ctx.lineTo(width, height / 2);
      ctx.stroke();
      return;
    }

    // Draw waveform
    ctx.lineWidth = 2;
    ctx.strokeStyle = waveColor;
    ctx.beginPath();

    const sliceWidth = width / data.waveform.length;
    let x = 0;

    for (let i = 0; i < data.waveform.length; i++) {
      const v = data.waveform[i] / 128.0;
      const y = v * height / 2;

      if (i === 0) {
        ctx.moveTo(x, y);
      } else {
        ctx.lineTo(x, y);
      }

      x += sliceWidth;
    }

    ctx.lineTo(width, height / 2);
    ctx.stroke();

    // Draw volume indicator
    const volumeBarHeight = data.volume * height * 0.8;
    const volumeBarWidth = 4;
    const volumeBarX = width - 20;

    // Volume bar background
    ctx.fillStyle = waveColor + '20';
    ctx.fillRect(volumeBarX, 10, volumeBarWidth, height - 20);

    // Volume bar fill
    const gradient = ctx.createLinearGradient(0, height, 0, 0);
    gradient.addColorStop(0, waveColor + '40');
    gradient.addColorStop(1, waveColor);
    ctx.fillStyle = gradient;
    ctx.fillRect(
      volumeBarX,
      height - 10 - volumeBarHeight,
      volumeBarWidth,
      volumeBarHeight
    );
  }, [data, isRecording, width, height, waveColor, backgroundColor]);

  useEffect(() => {
    const animate = () => {
      drawWaveform();
      if (isRecording) {
        animationIdRef.current = requestAnimationFrame(animate);
      }
    };

    if (isRecording) {
      animate();
    } else {
      drawWaveform();
    }

    return () => {
      if (animationIdRef.current) {
        cancelAnimationFrame(animationIdRef.current);
      }
    };
  }, [isRecording, drawWaveform]);

  return (
    <div className="relative">
      <canvas
        ref={canvasRef}
        width={width}
        height={height}
        className="rounded-lg"
        style={{ backgroundColor }}
      />
      {isRecording && (
        <div className="absolute top-2 left-2">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse" />
            <span className="text-xs text-gray-400">Recording</span>
          </div>
        </div>
      )}
    </div>
  );
};