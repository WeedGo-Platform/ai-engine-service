#!/usr/bin/env python3
import numpy as np
import wave

# Create a simple test audio file with a tone
sample_rate = 16000
duration = 2  # seconds
frequency = 440  # A4 note

# Generate sine wave
t = np.linspace(0, duration, int(sample_rate * duration))
audio = np.sin(2 * np.pi * frequency * t)

# Add some modulation to simulate speech patterns
modulation = np.sin(2 * np.pi * 5 * t) * 0.3
audio = audio * (1 + modulation)

# Convert to 16-bit integers
audio = (audio * 32767).astype(np.int16)

# Save as WAV file
with wave.open('/tmp/test_tone.wav', 'w') as wav_file:
    wav_file.setnchannels(1)  # Mono
    wav_file.setsampwidth(2)  # 16-bit
    wav_file.setframerate(sample_rate)
    wav_file.writeframes(audio.tobytes())

print("Created test audio file: /tmp/test_tone.wav")