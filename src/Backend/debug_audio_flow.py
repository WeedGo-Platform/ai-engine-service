#!/usr/bin/env python3
"""Debug audio flow from API to VAD to understand why speech is not detected"""

import asyncio
import numpy as np
import wave
import io
import base64
import logging
from pathlib import Path
from core.voice.vad_handler import SileroVADHandler
from core.voice import VoicePipeline, PipelineMode

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def debug_audio_processing():
    """Debug the entire audio processing pipeline"""

    print("=" * 60)
    print("AUDIO FLOW DEBUGGING")
    print("=" * 60)

    # Initialize VAD
    vad = SileroVADHandler()
    if not await vad.initialize():
        print("Failed to initialize VAD")
        return
    print("✅ VAD initialized\n")

    # Test 1: Create a simple test audio with speech characteristics
    print("Test 1: Synthetic speech-like audio")
    print("-" * 40)

    # Create audio that mimics speech formants
    sample_rate = 16000
    duration = 2  # seconds
    t = np.linspace(0, duration, sample_rate * duration)

    # Speech-like signal with formants
    speech = np.zeros_like(t)
    # F1 (700 Hz), F2 (1220 Hz), F3 (2600 Hz) - typical for vowel 'a'
    for freq, amp in [(700, 0.5), (1220, 0.3), (2600, 0.2)]:
        speech += amp * np.sin(2 * np.pi * freq * t)

    # Add amplitude modulation (speech envelope)
    envelope = np.sin(2 * np.pi * 3 * t) * 0.3 + 0.7
    speech = speech * envelope

    # Add some noise to make it more realistic
    speech += np.random.randn(len(speech)) * 0.05

    # Normalize
    speech = speech / np.max(np.abs(speech)) * 0.8
    speech = speech.astype(np.float32)

    # Test with different thresholds
    for threshold in [0.001, 0.01, 0.05, 0.1]:
        result = await vad.detect(speech, threshold=threshold)
        print(f"  Threshold {threshold:5.3f}: has_speech={result.has_speech}, confidence={result.confidence:.3f}")

    # Get raw probability from model
    if vad.ort_session:
        # Process a window
        window = speech[:512]
        prob = vad._get_speech_probability(window)
        print(f"  Raw probability for first window: {prob:.4f}")

    # Test 2: Test with WAV file format (as sent from mobile app)
    print("\nTest 2: WAV file format (simulating mobile app)")
    print("-" * 40)

    # Create WAV file in memory
    wav_buffer = io.BytesIO()
    with wave.open(wav_buffer, 'wb') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)   # 16-bit
        wav_file.setframerate(16000)
        # Convert float to int16
        audio_int16 = (speech * 32767).astype(np.int16)
        wav_file.writeframes(audio_int16.tobytes())

    # Get WAV bytes (as would be sent from mobile)
    wav_bytes = wav_buffer.getvalue()
    print(f"  WAV file size: {len(wav_bytes)} bytes")
    print(f"  WAV header: {wav_bytes[:4]}")  # Should be b'RIFF'

    # Test VAD with WAV bytes
    result = await vad.detect(wav_bytes, threshold=0.01)
    print(f"  VAD result: has_speech={result.has_speech}, confidence={result.confidence:.3f}")

    # Test 3: Test full pipeline
    print("\nTest 3: Full pipeline test")
    print("-" * 40)

    pipeline = VoicePipeline()
    if await pipeline.initialize():
        print("  ✅ Pipeline initialized")

        # Test with MANUAL mode (bypassing VAD)
        result = await pipeline.process_audio(
            wav_bytes,
            mode=PipelineMode.MANUAL
        )
        print(f"  MANUAL mode result: {result}")

        # Test with AUTO_VAD mode
        result = await pipeline.process_audio(
            wav_bytes,
            mode=PipelineMode.AUTO_VAD
        )
        print(f"  AUTO_VAD mode result: {result}")

    # Test 4: Analyze audio characteristics
    print("\nTest 4: Audio characteristics analysis")
    print("-" * 40)

    # Convert WAV bytes back to numpy to verify
    audio_from_wav = vad._bytes_to_numpy(wav_bytes)

    print(f"  Audio shape: {audio_from_wav.shape}")
    print(f"  Audio dtype: {audio_from_wav.dtype}")
    print(f"  Audio range: [{audio_from_wav.min():.3f}, {audio_from_wav.max():.3f}]")
    print(f"  Audio mean: {audio_from_wav.mean():.3f}")
    print(f"  Audio std: {audio_from_wav.std():.3f}")
    print(f"  RMS energy: {np.sqrt(np.mean(audio_from_wav**2)):.3f}")

    # Check frequency content
    fft = np.fft.rfft(audio_from_wav)
    freqs = np.fft.rfftfreq(len(audio_from_wav), 1/16000)
    magnitude = np.abs(fft)

    # Find peak frequency
    peak_idx = np.argmax(magnitude[1:]) + 1  # Skip DC
    peak_freq = freqs[peak_idx]
    print(f"  Peak frequency: {peak_freq:.1f} Hz")

    # Check energy in speech band (300-3400 Hz)
    speech_band = (freqs >= 300) & (freqs <= 3400)
    speech_energy = np.sum(magnitude[speech_band]**2)
    total_energy = np.sum(magnitude**2)
    speech_ratio = speech_energy / total_energy if total_energy > 0 else 0
    print(f"  Speech band energy ratio: {speech_ratio:.3f}")

    # Test 5: Test with extremely low threshold
    print("\nTest 5: Testing with extremely low thresholds")
    print("-" * 40)

    # Temporarily set VAD to extremely sensitive
    original_threshold = vad.threshold
    vad.threshold = 0.0001  # Extremely sensitive

    result = await vad.detect(audio_from_wav)
    print(f"  Threshold 0.0001: has_speech={result.has_speech}, confidence={result.confidence:.3f}")

    # Check what the model outputs for each window
    print("\n  Window-by-window analysis:")
    window_size = 512
    hop_size = 160

    probabilities = []
    for i in range(0, min(len(audio_from_wav) - window_size, window_size * 5), hop_size):
        window = audio_from_wav[i:i + window_size]
        prob = vad._get_speech_probability(window)
        probabilities.append(prob)

    if probabilities:
        print(f"    Window probabilities: {[f'{p:.4f}' for p in probabilities[:10]]}")
        print(f"    Max probability: {max(probabilities):.4f}")
        print(f"    Mean probability: {np.mean(probabilities):.4f}")

    # Restore original threshold
    vad.threshold = original_threshold

    print("\n" + "=" * 60)
    print("DEBUG COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(debug_audio_processing())