import React, { useEffect, useRef } from 'react';
import { AudioVisualizationData } from '../../services/voiceRecording.service';

interface VoiceVisualizationProps {
  data: AudioVisualizationData | null;
  isRecording: boolean;
  mode?: 'waveform' | 'frequency' | 'circle';
  height?: number;
  className?: string;
}

/**
 * Voice Visualization Component
 * Displays real-time audio visualization during recording
 */
export const VoiceVisualization: React.FC<VoiceVisualizationProps> = ({
  data,
  isRecording,
  mode = 'waveform',
  height = 60,
  className = ''
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationRef = useRef<number>();

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Set canvas size
    canvas.width = canvas.offsetWidth * window.devicePixelRatio;
    canvas.height = height * window.devicePixelRatio;
    ctx.scale(window.devicePixelRatio, window.devicePixelRatio);

    const draw = () => {
      ctx.clearRect(0, 0, canvas.offsetWidth, height);

      if (!isRecording || !data) {
        // Draw idle state
        drawIdleState(ctx, canvas.offsetWidth, height);
      } else {
        // Draw visualization based on mode
        switch (mode) {
          case 'frequency':
            drawFrequencyBars(ctx, data, canvas.offsetWidth, height);
            break;
          case 'circle':
            drawCircularVisualization(ctx, data, canvas.offsetWidth, height);
            break;
          case 'waveform':
          default:
            drawWaveform(ctx, data, canvas.offsetWidth, height);
            break;
        }
      }

      animationRef.current = requestAnimationFrame(draw);
    };

    draw();

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [data, isRecording, mode, height]);

  return (
    <canvas
      ref={canvasRef}
      className={`w-full ${className}`}
      style={{ height: `${height}px` }}
    />
  );
};

// Visualization drawing functions
function drawWaveform(
  ctx: CanvasRenderingContext2D,
  data: AudioVisualizationData,
  width: number,
  height: number
): void {
  const { waveform, volume } = data;
  const centerY = height / 2;
  const amplitude = Math.min(volume * height * 0.8, height * 0.4);

  // Set style
  ctx.strokeStyle = `rgba(59, 130, 246, ${0.6 + volume * 0.4})`;
  ctx.lineWidth = 2;
  ctx.lineCap = 'round';

  // Draw waveform
  ctx.beginPath();
  const sliceWidth = width / waveform.length;

  for (let i = 0; i < waveform.length; i++) {
    const x = i * sliceWidth;
    const y = centerY + waveform[i] * amplitude;

    if (i === 0) {
      ctx.moveTo(x, y);
    } else {
      ctx.lineTo(x, y);
    }
  }

  ctx.stroke();

  // Draw center line
  ctx.strokeStyle = 'rgba(156, 163, 175, 0.2)';
  ctx.lineWidth = 1;
  ctx.setLineDash([5, 5]);
  ctx.beginPath();
  ctx.moveTo(0, centerY);
  ctx.lineTo(width, centerY);
  ctx.stroke();
  ctx.setLineDash([]);
}

function drawFrequencyBars(
  ctx: CanvasRenderingContext2D,
  data: AudioVisualizationData,
  width: number,
  height: number
): void {
  const { frequency } = data;
  const barWidth = width / frequency.length;
  const barGap = 2;

  // Create gradient
  const gradient = ctx.createLinearGradient(0, height, 0, 0);
  gradient.addColorStop(0, 'rgba(59, 130, 246, 0.3)');
  gradient.addColorStop(0.5, 'rgba(59, 130, 246, 0.6)');
  gradient.addColorStop(1, 'rgba(147, 51, 234, 0.8)');

  ctx.fillStyle = gradient;

  // Draw frequency bars
  for (let i = 0; i < frequency.length; i++) {
    const barHeight = frequency[i] * height * 0.8;
    const x = i * barWidth;
    const y = height - barHeight;

    // Draw bar with rounded top
    ctx.beginPath();
    ctx.roundRect(x + barGap / 2, y, barWidth - barGap, barHeight, [2, 2, 0, 0]);
    ctx.fill();
  }
}

function drawCircularVisualization(
  ctx: CanvasRenderingContext2D,
  data: AudioVisualizationData,
  width: number,
  height: number
): void {
  const { frequency, volume } = data;
  const centerX = width / 2;
  const centerY = height / 2;
  const baseRadius = Math.min(width, height) * 0.2;
  const maxRadius = Math.min(width, height) * 0.4;

  // Draw central circle
  const pulseRadius = baseRadius + volume * 20;
  ctx.beginPath();
  ctx.arc(centerX, centerY, pulseRadius, 0, Math.PI * 2);
  ctx.fillStyle = `rgba(59, 130, 246, ${0.2 + volume * 0.3})`;
  ctx.fill();

  // Draw frequency rays
  const angleStep = (Math.PI * 2) / frequency.length;
  ctx.strokeStyle = 'rgba(147, 51, 234, 0.6)';
  ctx.lineWidth = 2;

  for (let i = 0; i < frequency.length; i++) {
    const angle = i * angleStep - Math.PI / 2;
    const rayLength = baseRadius + frequency[i] * (maxRadius - baseRadius);

    ctx.beginPath();
    ctx.moveTo(
      centerX + Math.cos(angle) * baseRadius,
      centerY + Math.sin(angle) * baseRadius
    );
    ctx.lineTo(
      centerX + Math.cos(angle) * rayLength,
      centerY + Math.sin(angle) * rayLength
    );
    ctx.stroke();
  }
}

function drawIdleState(
  ctx: CanvasRenderingContext2D,
  width: number,
  height: number
): void {
  const centerY = height / 2;
  const numPoints = 50;
  const amplitude = 2;

  ctx.strokeStyle = 'rgba(156, 163, 175, 0.3)';
  ctx.lineWidth = 1;

  // Draw a subtle sine wave for idle state
  ctx.beginPath();
  for (let i = 0; i <= numPoints; i++) {
    const x = (i / numPoints) * width;
    const y = centerY + Math.sin((i / numPoints) * Math.PI * 4) * amplitude;

    if (i === 0) {
      ctx.moveTo(x, y);
    } else {
      ctx.lineTo(x, y);
    }
  }
  ctx.stroke();
}

// Add roundRect polyfill for browsers that don't support it
if (!CanvasRenderingContext2D.prototype.roundRect) {
  CanvasRenderingContext2D.prototype.roundRect = function(
    x: number,
    y: number,
    width: number,
    height: number,
    radii: number | number[]
  ) {
    const radius = typeof radii === 'number' ? [radii, radii, radii, radii] : radii;
    this.beginPath();
    this.moveTo(x + radius[0], y);
    this.lineTo(x + width - radius[1], y);
    this.quadraticCurveTo(x + width, y, x + width, y + radius[1]);
    this.lineTo(x + width, y + height - radius[2]);
    this.quadraticCurveTo(x + width, y + height, x + width - radius[2], y + height);
    this.lineTo(x + radius[3], y + height);
    this.quadraticCurveTo(x, y + height, x, y + height - radius[3]);
    this.lineTo(x, y + radius[0]);
    this.quadraticCurveTo(x, y, x + radius[0], y);
    this.closePath();
  };
}

export default VoiceVisualization;