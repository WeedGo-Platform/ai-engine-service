#!/usr/bin/env python3
"""
Test script for V5 Voice System
Tests all voice components: STT, TTS, VAD, and pipeline
"""
import asyncio
import sys
import logging
import numpy as np
import wave
import io
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.voice import (
    WhisperSTTHandler,
    OfflineTTSHandler,
    SileroVADHandler,
    VoicePipeline,
    PipelineMode
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def generate_test_audio(duration_sec: float = 1.0, sample_rate: int = 16000) -> np.ndarray:
    """Generate test audio with sine wave"""
    t = np.linspace(0, duration_sec, int(sample_rate * duration_sec))
    # Generate a 440Hz tone (A4 note)
    audio = np.sin(2 * np.pi * 440 * t) * 0.3
    # Add some noise to simulate speech-like signal
    noise = np.random.normal(0, 0.01, len(t))
    audio = audio + noise
    return audio.astype(np.float32)

def save_audio_to_wav(audio: np.ndarray, filename: str, sample_rate: int = 16000):
    """Save audio array to WAV file"""
    # Ensure audio is in the right format
    if audio.dtype == np.float32 or audio.dtype == np.float64:
        # Convert to 16-bit PCM
        audio_int16 = (audio * 32767).astype(np.int16)
    else:
        audio_int16 = audio
    
    with wave.open(filename, 'wb') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio_int16.tobytes())

async def test_whisper_stt():
    """Test Whisper Speech-to-Text"""
    logger.info("=" * 50)
    logger.info("Testing Whisper STT...")
    
    try:
        # Initialize STT
        stt = WhisperSTTHandler(model_name="base")
        if not await stt.initialize():
            logger.error("Failed to initialize Whisper STT")
            return False
        
        # Generate test audio (simple tone, won't have real speech)
        test_audio = generate_test_audio(duration_sec=2.0)
        
        # Test transcription
        logger.info("Transcribing test audio...")
        result = await stt.transcribe(test_audio)
        
        logger.info(f"✅ STT Test Results:")
        logger.info(f"   Text: '{result.text}' (empty expected for tone)")
        logger.info(f"   Confidence: {result.confidence:.2f}")
        logger.info(f"   Language: {result.language}")
        logger.info(f"   Processing time: {result.duration_ms:.1f}ms")
        
        # Test with actual speech would require a real audio file
        # For now, we just verify the system works
        
        await stt.cleanup()
        return True
        
    except Exception as e:
        logger.error(f"STT test failed: {e}")
        return False

async def test_offline_tts():
    """Test Offline Text-to-Speech"""
    logger.info("=" * 50)
    logger.info("Testing Offline TTS...")
    
    try:
        # Initialize TTS
        tts = OfflineTTSHandler()
        if not await tts.initialize():
            logger.error("Failed to initialize TTS")
            return False
        
        # Get available voices
        voices = await tts.get_available_voices()
        logger.info(f"Found {len(voices)} available voices")
        for i, voice in enumerate(voices[:3]):  # Show first 3
            logger.info(f"   Voice {i+1}: {voice.get('name', 'Unknown')}")
        
        # Test synthesis
        test_text = "Hello, this is a test of the V5 voice synthesis system."
        logger.info(f"Synthesizing: '{test_text}'")
        
        result = await tts.synthesize(test_text)
        
        logger.info(f"✅ TTS Test Results:")
        logger.info(f"   Audio size: {len(result.audio)} bytes")
        logger.info(f"   Sample rate: {result.sample_rate}Hz")
        logger.info(f"   Duration: {result.duration_ms:.1f}ms")
        logger.info(f"   Format: {result.format}")
        
        # Save the audio for manual verification
        output_file = "test_output_tts.wav"
        with open(output_file, 'wb') as f:
            f.write(result.audio)
        logger.info(f"   Saved to: {output_file}")
        
        await tts.cleanup()
        return True
        
    except Exception as e:
        logger.error(f"TTS test failed: {e}")
        return False

async def test_silero_vad():
    """Test Silero Voice Activity Detection"""
    logger.info("=" * 50)
    logger.info("Testing Silero VAD...")
    
    try:
        # Initialize VAD
        vad = SileroVADHandler()
        if not await vad.initialize():
            logger.error("Failed to initialize VAD")
            return False
        
        # Test with silence
        silence = np.zeros(16000, dtype=np.float32)  # 1 second of silence
        result_silence = await vad.detect(silence)
        
        logger.info("VAD Test - Silence:")
        logger.info(f"   Has speech: {result_silence.has_speech}")
        logger.info(f"   Confidence: {result_silence.confidence:.2f}")
        logger.info(f"   Energy level: {result_silence.energy_level:.4f}")
        
        # Test with tone (simulated speech)
        tone = generate_test_audio(duration_sec=1.0)
        result_tone = await vad.detect(tone)
        
        logger.info("VAD Test - Tone:")
        logger.info(f"   Has speech: {result_tone.has_speech}")
        logger.info(f"   Confidence: {result_tone.confidence:.2f}")
        logger.info(f"   Energy level: {result_tone.energy_level:.4f}")
        logger.info(f"   Speech segments: {result_tone.speech_segments}")
        
        logger.info("✅ VAD test completed successfully")
        
        await vad.cleanup()
        return True
        
    except Exception as e:
        logger.error(f"VAD test failed: {e}")
        return False

async def test_voice_pipeline():
    """Test complete voice pipeline"""
    logger.info("=" * 50)
    logger.info("Testing Voice Pipeline...")
    
    try:
        # Initialize pipeline
        pipeline = VoicePipeline(stt_model="base")
        if not await pipeline.initialize():
            logger.error("Failed to initialize voice pipeline")
            return False
        
        # Test audio processing with VAD
        test_audio = generate_test_audio(duration_sec=2.0)
        
        logger.info("Testing pipeline with AUTO_VAD mode...")
        result = await pipeline.process_audio(
            test_audio,
            mode=PipelineMode.AUTO_VAD
        )
        
        logger.info(f"Pipeline Results:")
        logger.info(f"   Session ID: {result['session_id']}")
        logger.info(f"   Has speech: {result['has_speech']}")
        logger.info(f"   Processing time: {result['processing_time_ms']:.1f}ms")
        
        if result.get('vad_result'):
            logger.info(f"   VAD confidence: {result['vad_result']['confidence']:.2f}")
        
        if result.get('transcription'):
            logger.info(f"   Transcription: '{result['transcription']['text']}'")
        
        # Test TTS through pipeline
        logger.info("\nTesting TTS through pipeline...")
        audio_response = await pipeline.synthesize_response(
            "This is a test of the complete voice pipeline system.",
            speed=1.0
        )
        
        logger.info(f"   Generated {len(audio_response)} bytes of audio")
        
        # Get metrics
        metrics = pipeline.get_metrics()
        logger.info("\nPipeline Metrics:")
        logger.info(f"   STT processed: {metrics['stt']['total_processed']}")
        logger.info(f"   TTS processed: {metrics['tts']['total_processed']}")
        logger.info(f"   VAD processed: {metrics['vad']['total_processed']}")
        
        logger.info("✅ Pipeline test completed successfully")
        
        await pipeline.cleanup()
        return True
        
    except Exception as e:
        logger.error(f"Pipeline test failed: {e}")
        return False

async def main():
    """Run all voice system tests"""
    logger.info("🎤 V5 Voice System Test Suite")
    logger.info("=" * 50)
    
    # Check if models exist
    models_dir = Path("models/voice")
    if not models_dir.exists():
        logger.error(f"Models directory not found: {models_dir}")
        logger.error("Please run the download scripts first!")
        return
    
    # Run tests
    tests = [
        ("Whisper STT", test_whisper_stt),
        ("Offline TTS", test_offline_tts),
        ("Silero VAD", test_silero_vad),
        ("Voice Pipeline", test_voice_pipeline)
    ]
    
    results = []
    for name, test_func in tests:
        try:
            success = await test_func()
            results.append((name, success))
        except Exception as e:
            logger.error(f"Test {name} crashed: {e}")
            results.append((name, False))
    
    # Summary
    logger.info("\n" + "=" * 50)
    logger.info("📊 Test Summary:")
    for name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        logger.info(f"   {name}: {status}")
    
    total = len(results)
    passed = sum(1 for _, s in results if s)
    logger.info(f"\n   Total: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("\n🎉 All tests passed! Voice system is fully functional.")
    else:
        logger.info("\n⚠️ Some tests failed. Please check the logs above.")

if __name__ == "__main__":
    asyncio.run(main())