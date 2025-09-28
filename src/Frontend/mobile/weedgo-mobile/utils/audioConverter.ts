/**
 * Audio Converter Utilities
 * Converts audio data to PCM Float32 format for WebSocket streaming
 */

/**
 * Convert WAV/PCM16 audio to Float32 PCM
 * @param base64Audio - Base64 encoded audio data
 * @param skipHeader - Whether to skip WAV header (for incremental chunks)
 * @returns Base64 encoded Float32 PCM data
 */
export function convertToFloat32PCM(base64Audio: string, skipHeader: boolean = true): string {
  try {
    // Decode base64 to binary
    const binaryString = atob(base64Audio);
    const bytes = new Uint8Array(binaryString.length);
    for (let i = 0; i < binaryString.length; i++) {
      bytes[i] = binaryString.charCodeAt(i);
    }

    // Skip WAV header if present (first 44 bytes typically)
    let offset = 0;

    if (skipHeader) {
      // Check for RIFF header
      if (bytes[0] === 0x52 && bytes[1] === 0x49 && bytes[2] === 0x46 && bytes[3] === 0x46) {
        // This is a WAV file, skip the header
        offset = 44; // Standard WAV header size

        // Find the data chunk
        for (let i = 36; i < bytes.length - 8; i++) {
          if (bytes[i] === 0x64 && bytes[i+1] === 0x61 &&
              bytes[i+2] === 0x74 && bytes[i+3] === 0x61) {
            offset = i + 8; // Skip "data" + size
            break;
          }
        }
      }
    }

    // Ensure offset is aligned to 2 bytes for Int16Array
    if (offset % 2 !== 0) {
      offset += 1;
    }

    // Calculate the number of samples (each sample is 2 bytes)
    const remainingBytes = bytes.length - offset;
    const sampleCount = Math.floor(remainingBytes / 2);

    // Return empty if no samples
    if (sampleCount <= 0) {
      return '';
    }

    // Convert PCM16 to Float32
    const pcm16Data = new Int16Array(sampleCount);
    const dataView = new DataView(bytes.buffer);

    // Read PCM16 samples manually to avoid alignment issues
    for (let i = 0; i < sampleCount; i++) {
      const byteIndex = offset + (i * 2);
      if (byteIndex + 1 < bytes.length) {
        // Read as little-endian Int16
        pcm16Data[i] = dataView.getInt16(byteIndex, true);
      }
    }

    const float32Data = new Float32Array(sampleCount);
    for (let i = 0; i < sampleCount; i++) {
      // Convert from Int16 range (-32768 to 32767) to Float32 range (-1.0 to 1.0)
      float32Data[i] = pcm16Data[i] / 32768.0;
    }

    // Convert Float32Array to base64
    const float32Bytes = new Uint8Array(float32Data.buffer);
    let binary = '';
    for (let i = 0; i < float32Bytes.length; i++) {
      binary += String.fromCharCode(float32Bytes[i]);
    }

    return btoa(binary);
  } catch (error) {
    console.error('[AUDIO] Conversion error:', error);
    // Return empty string on error
    return '';
  }
}

/**
 * Extract raw PCM from audio file data
 * @param audioData - Base64 encoded audio file
 * @param sampleRate - Expected sample rate (default 16000)
 * @returns Object with PCM data and metadata
 */
export function extractPCMData(audioData: string, sampleRate: number = 16000) {
  try {
    // For mobile recording, audio might be in different formats
    // This is a simplified extraction

    const float32PCM = convertToFloat32PCM(audioData);

    return {
      data: float32PCM,
      sampleRate,
      channels: 1,
      format: 'float32',
    };
  } catch (error) {
    console.error('[AUDIO] PCM extraction error:', error);
    return {
      data: audioData,
      sampleRate,
      channels: 1,
      format: 'unknown',
    };
  }
}

/**
 * Create silence buffer for testing
 * @param durationMs - Duration in milliseconds
 * @param sampleRate - Sample rate
 * @returns Base64 encoded silence
 */
export function createSilenceBuffer(durationMs: number, sampleRate: number = 16000): string {
  const samples = Math.floor((durationMs / 1000) * sampleRate);
  const float32Data = new Float32Array(samples);

  // Fill with silence (zeros)
  for (let i = 0; i < samples; i++) {
    float32Data[i] = 0;
  }

  // Convert to base64
  const bytes = new Uint8Array(float32Data.buffer);
  let binary = '';
  for (let i = 0; i < bytes.length; i++) {
    binary += String.fromCharCode(bytes[i]);
  }

  return btoa(binary);
}