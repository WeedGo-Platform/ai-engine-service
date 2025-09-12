"""
Silero Voice Activity Detection handler for V5
Detects speech segments in audio - completely offline
"""
import torch
import numpy as np
import asyncio
import logging
import time
from typing import Dict, Any, Optional, Union, List, Callable
from pathlib import Path
import onnxruntime as ort

from .base_handler import VADHandler, VADResult, AudioConfig, VoiceState

logger = logging.getLogger(__name__)

class SileroVADHandler(VADHandler):
    """Voice Activity Detection using Silero VAD"""
    
    def __init__(self, config: Optional[AudioConfig] = None):
        """Initialize VAD handler"""
        super().__init__(config)
        self.model = None
        self.model_path = Path("models/voice/silero/silero_vad.onnx")
        self.ort_session = None
        
        # VAD parameters
        self.threshold = 0.5
        self.min_speech_duration_ms = 250
        self.min_silence_duration_ms = 100
        self.speech_pad_ms = 30
        
    async def initialize(self) -> bool:
        """Initialize VAD model"""
        try:
            self.set_state(VoiceState.PROCESSING)
            
            # Check if model exists
            if not self.model_path.exists():
                logger.error(f"VAD model not found: {self.model_path}")
                self.set_state(VoiceState.ERROR)
                return False
            
            # Load ONNX model for better performance
            logger.info(f"Loading Silero VAD model from {self.model_path}")
            
            loop = asyncio.get_event_loop()
            self.ort_session = await loop.run_in_executor(
                None,
                self._load_model_sync
            )
            
            if self.ort_session:
                logger.info("✅ Silero VAD model loaded successfully")
                self.set_state(VoiceState.IDLE)
                return True
            else:
                # Fallback to PyTorch model
                self.model = await self._load_pytorch_model()
                if self.model:
                    logger.info("✅ Silero VAD PyTorch model loaded")
                    self.set_state(VoiceState.IDLE)
                    return True
                    
                self.set_state(VoiceState.ERROR)
                return False
                
        except Exception as e:
            logger.error(f"Failed to initialize VAD: {e}")
            self.set_state(VoiceState.ERROR)
            return False
    
    def _load_model_sync(self):
        """Load ONNX model synchronously"""
        try:
            import onnxruntime as ort
            # Create ONNX inference session
            sess_options = ort.SessionOptions()
            sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
            
            session = ort.InferenceSession(
                str(self.model_path),
                sess_options,
                providers=['CPUExecutionProvider']
            )
            return session
        except ImportError:
            logger.warning("onnxruntime not installed, will use PyTorch model")
            return None
        except Exception as e:
            logger.error(f"Error loading ONNX model: {e}")
            return None
    
    async def _load_pytorch_model(self):
        """Load PyTorch model as fallback"""
        try:
            model_path = self.model_path.with_suffix('.pt')
            if model_path.exists():
                loop = asyncio.get_event_loop()
                model = await loop.run_in_executor(
                    None,
                    torch.load,
                    str(model_path)
                )
                model.eval()
                return model
        except Exception as e:
            logger.error(f"Error loading PyTorch model: {e}")
        return None
    
    async def detect(
        self,
        audio: Union[np.ndarray, bytes],
        threshold: float = 0.5
    ) -> VADResult:
        """Detect voice activity in audio
        
        Args:
            audio: Audio data as numpy array or bytes
            threshold: Detection threshold (0.0-1.0)
            
        Returns:
            VADResult with detection results
        """
        start_time = time.time()
        
        try:
            self.set_state(VoiceState.PROCESSING)
            
            # Convert bytes to numpy if needed
            if isinstance(audio, bytes):
                audio = self._bytes_to_numpy(audio)
            
            # Preprocess audio for VAD
            audio = self._preprocess_audio_for_vad(audio)
            
            # Run VAD detection
            loop = asyncio.get_event_loop()
            speech_segments = await loop.run_in_executor(
                None,
                self._detect_speech_sync,
                audio,
                threshold
            )
            
            # Calculate metrics
            has_speech = len(speech_segments) > 0
            confidence = self._calculate_confidence(speech_segments, len(audio))
            energy_level = self._calculate_energy(audio)
            
            duration_ms = (time.time() - start_time) * 1000
            self.update_metrics(duration_ms, success=True)
            
            self.set_state(VoiceState.IDLE)
            
            return VADResult(
                has_speech=has_speech,
                confidence=confidence,
                speech_segments=speech_segments,
                energy_level=energy_level
            )
            
        except Exception as e:
            logger.error(f"VAD detection failed: {e}")
            duration_ms = (time.time() - start_time) * 1000
            self.update_metrics(duration_ms, success=False)
            self.set_state(VoiceState.ERROR)
            
            return VADResult(
                has_speech=False,
                confidence=0.0,
                speech_segments=[],
                energy_level=0.0
            )
    
    async def detect_stream(
        self,
        audio_stream: Any,
        callback: Optional[Callable] = None
    ) -> VADResult:
        """Detect voice activity in streaming audio
        
        Args:
            audio_stream: Async generator yielding audio chunks
            callback: Optional callback for each detection
            
        Returns:
            Final VADResult
        """
        all_segments = []
        total_audio_length = 0
        
        async for chunk in audio_stream:
            # Detect in this chunk
            result = await self.detect(chunk, self.threshold)
            
            # Adjust segment timestamps based on total audio processed
            adjusted_segments = [
                (start + total_audio_length, end + total_audio_length)
                for start, end in result.speech_segments
            ]
            
            all_segments.extend(adjusted_segments)
            total_audio_length += len(chunk)
            
            # Call callback if provided
            if callback and result.has_speech:
                await callback(result)
        
        # Merge nearby segments
        merged_segments = self._merge_segments(all_segments)
        
        return VADResult(
            has_speech=len(merged_segments) > 0,
            confidence=self._calculate_confidence(merged_segments, total_audio_length),
            speech_segments=merged_segments,
            energy_level=0.5  # Average energy
        )
    
    def _detect_speech_sync(self, audio: np.ndarray, threshold: float) -> List[tuple]:
        """Synchronously detect speech segments"""
        segments = []
        
        # Process audio in windows
        window_size = 512  # ~32ms at 16kHz
        hop_size = 160     # ~10ms at 16kHz
        
        in_speech = False
        speech_start = 0
        silence_samples = 0
        
        for i in range(0, len(audio) - window_size, hop_size):
            window = audio[i:i + window_size]
            
            # Get speech probability for this window
            prob = self._get_speech_probability(window)
            
            if prob > threshold:
                if not in_speech:
                    # Start of speech
                    in_speech = True
                    speech_start = i
                    silence_samples = 0
            else:
                if in_speech:
                    silence_samples += hop_size
                    
                    # Check if silence is long enough to end speech
                    silence_ms = (silence_samples / self.config.sample_rate) * 1000
                    if silence_ms > self.min_silence_duration_ms:
                        # End of speech
                        speech_end = i
                        
                        # Check minimum duration
                        duration_ms = ((speech_end - speech_start) / self.config.sample_rate) * 1000
                        if duration_ms >= self.min_speech_duration_ms:
                            # Convert to milliseconds
                            start_ms = (speech_start / self.config.sample_rate) * 1000
                            end_ms = (speech_end / self.config.sample_rate) * 1000
                            segments.append((start_ms, end_ms))
                        
                        in_speech = False
                        silence_samples = 0
        
        # Handle speech that extends to the end
        if in_speech:
            speech_end = len(audio)
            duration_ms = ((speech_end - speech_start) / self.config.sample_rate) * 1000
            if duration_ms >= self.min_speech_duration_ms:
                start_ms = (speech_start / self.config.sample_rate) * 1000
                end_ms = (speech_end / self.config.sample_rate) * 1000
                segments.append((start_ms, end_ms))
        
        return segments
    
    def _get_speech_probability(self, window: np.ndarray) -> float:
        """Get speech probability for audio window"""
        try:
            if self.ort_session:
                # Use ONNX model
                # Prepare input
                input_tensor = window.astype(np.float32).reshape(1, -1)
                
                # Run inference
                outputs = self.ort_session.run(
                    None,
                    {self.ort_session.get_inputs()[0].name: input_tensor}
                )
                
                return float(outputs[0][0])
                
            elif self.model:
                # Use PyTorch model
                with torch.no_grad():
                    input_tensor = torch.FloatTensor(window).unsqueeze(0)
                    output = self.model(input_tensor)
                    return float(output[0])
            else:
                # Fallback to energy-based detection
                return self._energy_based_vad(window)
                
        except Exception as e:
            logger.error(f"Error in speech detection: {e}")
            return 0.0
    
    def _energy_based_vad(self, window: np.ndarray) -> float:
        """Simple energy-based VAD as fallback"""
        energy = np.sum(window ** 2) / len(window)
        # Normalize to 0-1 range
        max_energy = 1.0  # Maximum possible energy for normalized audio
        return min(energy / max_energy, 1.0)
    
    def _preprocess_audio_for_vad(self, audio: np.ndarray) -> np.ndarray:
        """Preprocess audio for VAD"""
        # Ensure float32
        if audio.dtype != np.float32:
            audio = audio.astype(np.float32)
        
        # Normalize to [-1, 1]
        if np.abs(audio).max() > 1.0:
            audio = audio / 32768.0
        
        # Ensure 16kHz sample rate (simple resampling if needed)
        # This is a simplified approach - use librosa for better resampling
        if self.config.sample_rate != 16000:
            # Simple decimation/interpolation
            ratio = 16000 / self.config.sample_rate
            if ratio > 1:
                # Upsample
                audio = np.interp(
                    np.arange(0, len(audio) * ratio, ratio),
                    np.arange(len(audio)),
                    audio
                )
            else:
                # Downsample
                indices = np.arange(0, len(audio), 1/ratio).astype(int)
                audio = audio[indices]
        
        return audio
    
    def _bytes_to_numpy(self, audio_bytes: bytes) -> np.ndarray:
        """Convert audio bytes to numpy array"""
        audio = np.frombuffer(audio_bytes, dtype=np.int16)
        return audio.astype(np.float32) / 32768.0
    
    def _calculate_confidence(self, segments: List[tuple], total_length: int) -> float:
        """Calculate overall confidence based on speech segments"""
        if not segments or total_length == 0:
            return 0.0
        
        # Calculate speech ratio
        total_speech = sum(end - start for start, end in segments)
        speech_ratio = total_speech / (total_length / self.config.sample_rate * 1000)
        
        # Confidence is higher when speech is detected but not constant
        if speech_ratio < 0.1:
            return speech_ratio * 5  # Scale up for low speech
        elif speech_ratio > 0.9:
            return 0.9  # Probably noise if constant
        else:
            return min(speech_ratio * 1.2, 1.0)
    
    def _calculate_energy(self, audio: np.ndarray) -> float:
        """Calculate average energy level"""
        return float(np.sqrt(np.mean(audio ** 2)))
    
    def _merge_segments(self, segments: List[tuple], gap_ms: float = 300) -> List[tuple]:
        """Merge nearby speech segments"""
        if not segments:
            return []
        
        merged = []
        current_start, current_end = segments[0]
        
        for start, end in segments[1:]:
            if start - current_end <= gap_ms:
                # Merge segments
                current_end = end
            else:
                # Add current segment and start new one
                merged.append((current_start, current_end))
                current_start, current_end = start, end
        
        # Add final segment
        merged.append((current_start, current_end))
        
        return merged
    
    async def cleanup(self) -> None:
        """Clean up resources"""
        self.ort_session = None
        self.model = None
        self.set_state(VoiceState.IDLE)
        logger.info("VAD handler cleaned up")