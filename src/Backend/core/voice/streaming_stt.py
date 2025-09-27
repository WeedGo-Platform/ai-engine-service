"""
Streaming Speech-to-Text with Partial Results
Integrates Whisper for real-time transcription
"""
import asyncio
import numpy as np
import time
import logging
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from collections import deque
import threading
import queue

try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    logging.warning("Whisper not available for streaming STT")

from .base_handler import STTHandler, STTResult, AudioConfig, VoiceState

logger = logging.getLogger(__name__)

@dataclass
class StreamingConfig:
    """Configuration for streaming STT"""
    model_size: str = "base"  # tiny, base, small, medium, large
    language: Optional[str] = None  # Auto-detect if None
    buffer_duration_ms: int = 1000  # Buffer before processing
    overlap_duration_ms: int = 200  # Overlap between chunks
    partial_interval_ms: int = 300  # How often to emit partials
    enable_vad: bool = True  # Use VAD to optimize processing
    temperature: float = 0.0  # Deterministic decoding
    compression_ratio_threshold: float = 2.4
    logprob_threshold: float = -1.0
    no_speech_threshold: float = 0.6
    
@dataclass
class TranscriptSegment:
    """A segment of transcribed audio"""
    text: str
    start_time: float
    end_time: float
    confidence: float = 1.0
    is_final: bool = False
    language: Optional[str] = None
    
class StreamingSTTHandler(STTHandler):
    """Streaming STT with real-time partial results"""
    
    def __init__(self, config: Optional[StreamingConfig] = None):
        super().__init__(AudioConfig())
        self.stream_config = config or StreamingConfig()
        self.model = None
        self.audio_buffer = deque(maxlen=100)  # Circular buffer
        self.transcript_buffer: List[TranscriptSegment] = []
        self.processing_thread: Optional[threading.Thread] = None
        self.should_stop = threading.Event()
        self.audio_queue = queue.Queue()
        self.result_queue = queue.Queue()
        self.last_partial_time = 0
        self.session_start_time = 0
        
        # Callbacks
        self.on_partial: Optional[Callable] = None
        self.on_final: Optional[Callable] = None
        
    async def initialize(self) -> bool:
        """Load Whisper model for streaming"""
        try:
            self.set_state(VoiceState.PROCESSING)
            
            if not WHISPER_AVAILABLE:
                logger.error("Whisper not available")
                self.set_state(VoiceState.ERROR)
                return False
            
            # Load model in background
            loop = asyncio.get_event_loop()
            self.model = await loop.run_in_executor(
                None,
                whisper.load_model,
                self.stream_config.model_size
            )
            
            # Start processing thread
            self.processing_thread = threading.Thread(
                target=self._processing_loop,
                daemon=True
            )
            self.processing_thread.start()
            
            self.model_name = f"whisper-{self.stream_config.model_size}"
            logger.info(f"Loaded Whisper model: {self.model_name}")
            
            self.set_state(VoiceState.IDLE)
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize streaming STT: {e}")
            self.set_state(VoiceState.ERROR)
            return False
    
    async def transcribe_stream(
        self,
        audio_stream: asyncio.Queue,
        language: Optional[str] = None
    ) -> AsyncGenerator[STTResult, None]:
        """Transcribe streaming audio with partial results"""
        
        self.session_start_time = time.time()
        accumulated_audio = []
        last_final_end = 0
        
        try:
            while True:
                # Get audio chunk from stream
                audio_chunk = await audio_stream.get()
                
                if audio_chunk is None:  # End of stream
                    break
                
                # Add to buffer
                accumulated_audio.append(audio_chunk)
                self.audio_queue.put(audio_chunk)
                
                # Check if we should process
                total_duration = len(np.concatenate(accumulated_audio)) / self.config.sample_rate * 1000
                
                if total_duration >= self.stream_config.buffer_duration_ms:
                    # Process accumulated audio
                    full_audio = np.concatenate(accumulated_audio)
                    
                    # Get partial result
                    partial_result = await self._process_audio_chunk(
                        full_audio,
                        language=language or self.stream_config.language,
                        is_final=False
                    )
                    
                    if partial_result and partial_result.text:
                        yield partial_result
                    
                    # Keep overlap for context
                    overlap_samples = int(
                        self.stream_config.overlap_duration_ms * 
                        self.config.sample_rate / 1000
                    )
                    
                    if len(full_audio) > overlap_samples:
                        accumulated_audio = [full_audio[-overlap_samples:]]
                    
        finally:
            # Process any remaining audio
            if accumulated_audio:
                full_audio = np.concatenate(accumulated_audio)
                final_result = await self._process_audio_chunk(
                    full_audio,
                    language=language or self.stream_config.language,
                    is_final=True
                )
                if final_result:
                    yield final_result
    
    async def process_audio_chunk(
        self,
        audio_chunk: bytes,
        session_id: str
    ) -> Optional[Dict[str, Any]]:
        """Process a single audio chunk and return transcript"""
        
        # Convert to numpy
        audio_np = np.frombuffer(audio_chunk, dtype=np.int16).astype(np.float32) / 32768.0
        
        # Add to processing queue
        self.audio_queue.put(audio_np)
        
        # Check for results
        try:
            result = self.result_queue.get_nowait()
            return {
                'session_id': session_id,
                'partial': result.get('partial', ''),
                'is_final': result.get('is_final', False),
                'confidence': result.get('confidence', 0.0),
                'language': result.get('language'),
                'timestamp': time.time()
            }
        except queue.Empty:
            return None
    
    async def _process_audio_chunk(
        self,
        audio: np.ndarray,
        language: Optional[str] = None,
        is_final: bool = False
    ) -> Optional[STTResult]:
        """Process audio chunk with Whisper"""
        
        if self.model is None:
            return None
        
        try:
            start_time = time.time()
            
            # Run Whisper transcription
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self._transcribe_with_whisper,
                audio,
                language
            )
            
            if result and result['text']:
                # Create STTResult
                stt_result = STTResult(
                    text=result['text'].strip(),
                    language=result.get('language', language),
                    confidence=self._calculate_confidence(result),
                    segments=self._extract_segments(result),
                    is_final=is_final
                )
                
                # Update metrics
                duration_ms = (time.time() - start_time) * 1000
                self.update_metrics(duration_ms, success=True)
                
                return stt_result
            
            return None
            
        except Exception as e:
            logger.error(f"Error processing audio chunk: {e}")
            return None
    
    def _transcribe_with_whisper(
        self,
        audio: np.ndarray,
        language: Optional[str] = None
    ) -> Dict[str, Any]:
        """Run Whisper transcription (blocking)"""
        
        # Whisper expects float32 audio
        if audio.dtype != np.float32:
            audio = audio.astype(np.float32)
        
        # Ensure audio is normalized
        if np.abs(audio).max() > 1.0:
            audio = audio / np.abs(audio).max()
        
        # Transcribe
        options = {
            'language': language,
            'temperature': self.stream_config.temperature,
            'compression_ratio_threshold': self.stream_config.compression_ratio_threshold,
            'logprob_threshold': self.stream_config.logprob_threshold,
            'no_speech_threshold': self.stream_config.no_speech_threshold,
            'fp16': False,  # Use FP32 for better accuracy
            'verbose': False
        }
        
        result = self.model.transcribe(audio, **options)
        return result
    
    def _processing_loop(self) -> None:
        """Background thread for continuous processing"""
        
        accumulated_audio = []
        last_process_time = time.time()
        
        while not self.should_stop.is_set():
            try:
                # Get audio from queue with timeout
                try:
                    audio_chunk = self.audio_queue.get(timeout=0.1)
                    accumulated_audio.append(audio_chunk)
                except queue.Empty:
                    pass
                
                # Check if we should process
                current_time = time.time()
                time_since_last = (current_time - last_process_time) * 1000
                
                if accumulated_audio and time_since_last >= self.stream_config.partial_interval_ms:
                    # Combine accumulated audio
                    full_audio = np.concatenate(accumulated_audio)
                    
                    # Process with Whisper
                    result = self._transcribe_with_whisper(full_audio)
                    
                    if result and result.get('text'):
                        # Put result in queue
                        self.result_queue.put({
                            'partial': result['text'].strip(),
                            'is_final': False,
                            'confidence': self._calculate_confidence(result),
                            'language': result.get('language')
                        })
                    
                    # Reset for next partial
                    last_process_time = current_time
                    
                    # Keep some audio for context
                    overlap_samples = int(
                        self.stream_config.overlap_duration_ms * 
                        self.config.sample_rate / 1000
                    )
                    if len(full_audio) > overlap_samples:
                        accumulated_audio = [full_audio[-overlap_samples:]]
                    else:
                        accumulated_audio = [full_audio]
                        
            except Exception as e:
                logger.error(f"Error in processing loop: {e}")
    
    def _calculate_confidence(self, result: Dict[str, Any]) -> float:
        """Calculate confidence score from Whisper result"""
        
        # Use no_speech_prob as inverse confidence
        no_speech_prob = result.get('no_speech_prob', 0.0)
        confidence = 1.0 - no_speech_prob
        
        # Adjust based on compression ratio (lower is better)
        segments = result.get('segments', [])
        if segments:
            avg_compression = np.mean([
                s.get('compression_ratio', 1.0) 
                for s in segments
            ])
            # Penalize high compression ratios
            if avg_compression > 2.0:
                confidence *= 0.8
        
        return min(max(confidence, 0.0), 1.0)
    
    def _extract_segments(self, result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract segments from Whisper result"""
        
        segments = []
        for seg in result.get('segments', []):
            segments.append({
                'text': seg.get('text', '').strip(),
                'start': seg.get('start', 0.0),
                'end': seg.get('end', 0.0),
                'confidence': 1.0 - seg.get('no_speech_prob', 0.0)
            })
        return segments
    
    async def cleanup(self) -> None:
        """Clean up resources"""
        
        # Stop processing thread
        if self.processing_thread:
            self.should_stop.set()
            self.processing_thread.join(timeout=1.0)
        
        # Clear buffers
        self.audio_buffer.clear()
        self.transcript_buffer.clear()
        
        # Clear queues
        while not self.audio_queue.empty():
            self.audio_queue.get()
        while not self.result_queue.empty():
            self.result_queue.get()
        
        self.model = None
        logger.info("Streaming STT cleaned up")