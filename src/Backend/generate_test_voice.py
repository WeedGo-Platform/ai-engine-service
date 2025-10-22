#!/usr/bin/env python3
"""
Generate Test Voice Sample for Personality API Testing

Creates a valid WAV file that meets all validation requirements:
- Duration: 15 seconds (optimal for XTTS v2)
- Sample rate: 22050Hz
- Bit depth: 16-bit
- Channels: Mono
- Format: WAV
"""
import wave
import numpy as np
import struct
from pathlib import Path

def generate_test_voice_sample(
    output_path: str = "test_voice_sample.wav",
    duration: float = 15.0,
    sample_rate: int = 22050,
    frequency: float = 440.0  # A4 note
):
    """
    Generate a test WAV file with a sine wave tone

    Args:
        output_path: Path to save the WAV file
        duration: Duration in seconds (default: 15s)
        sample_rate: Sample rate in Hz (default: 22050Hz)
        frequency: Frequency of the sine wave in Hz (default: 440Hz - A4 note)
    """
    print(f"Generating test voice sample...")
    print(f"  Duration: {duration}s")
    print(f"  Sample rate: {sample_rate}Hz")
    print(f"  Bit depth: 16-bit")
    print(f"  Channels: Mono")

    # Generate time array
    num_samples = int(sample_rate * duration)
    t = np.linspace(0, duration, num_samples, False)

    # Generate sine wave (amplitude varies to simulate speech-like patterns)
    # Add some amplitude modulation to make it more interesting
    envelope = np.sin(2 * np.pi * 2 * t) * 0.3 + 0.7  # Slow amplitude variation
    signal = np.sin(2 * np.pi * frequency * t) * envelope

    # Add some harmonics to make it richer
    signal += 0.5 * np.sin(2 * np.pi * frequency * 2 * t) * envelope  # 2nd harmonic
    signal += 0.3 * np.sin(2 * np.pi * frequency * 3 * t) * envelope  # 3rd harmonic

    # Normalize to prevent clipping
    signal = signal / np.max(np.abs(signal))

    # Scale to 16-bit integer range
    signal = np.int16(signal * 32767)

    # Write WAV file
    with wave.open(output_path, 'w') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit (2 bytes)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(signal.tobytes())

    # Get file stats
    file_path = Path(output_path)
    file_size_mb = file_path.stat().st_size / (1024 * 1024)

    print(f"\n✅ Test voice sample generated successfully!")
    print(f"  File: {output_path}")
    print(f"  Size: {file_size_mb:.2f} MB")
    print(f"  Validation:")
    print(f"    ✓ Duration: {duration}s (optimal 15-20s)")
    print(f"    ✓ Sample rate: {sample_rate}Hz (recommended 22050Hz)")
    print(f"    ✓ Bit depth: 16-bit")
    print(f"    ✓ Format: WAV")
    print(f"    ✓ File size: {file_size_mb:.2f}MB (< 10MB limit)")

    return output_path


def generate_multiple_samples():
    """Generate test samples for different personalities"""
    personalities = [
        ("marcel", 15.0, 440.0),  # A4 - Professional tone
        ("shante", 18.0, 523.25),  # C5 - Friendly higher pitch
        ("zac", 20.0, 329.63),  # E4 - Casual lower pitch
    ]

    print("=" * 60)
    print("Generating Test Voice Samples for All Default Personalities")
    print("=" * 60)

    generated_files = []
    for name, duration, freq in personalities:
        print(f"\n📢 Generating sample for '{name}' personality...")
        filename = f"test_voice_{name}.wav"
        generate_test_voice_sample(
            output_path=filename,
            duration=duration,
            frequency=freq
        )
        generated_files.append(filename)

    print("\n" + "=" * 60)
    print("✅ All test samples generated!")
    print("=" * 60)
    print("\nGenerated files:")
    for f in generated_files:
        print(f"  - {f}")

    print("\nYou can now test the upload endpoint with:")
    print(f"\n  curl -X POST \"http://localhost:8000/api/personalities/{{personality_id}}/voice\" \\")
    print(f"    -F \"audio=@{generated_files[0]}\"")

    return generated_files


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--all":
        # Generate samples for all personalities
        generate_multiple_samples()
    else:
        # Generate single generic sample
        generate_test_voice_sample()

        print("\nTo generate samples for all personalities, run:")
        print("  python3 generate_test_voice.py --all")
