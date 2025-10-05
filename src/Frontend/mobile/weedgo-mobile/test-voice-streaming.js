#!/usr/bin/env node

/**
 * Test script for voice streaming WebSocket
 * Verifies the backend /api/voice/ws/stream endpoint
 */

const WebSocket = require('ws');

// Use environment variable or config file
const WS_URL = process.env.EXPO_PUBLIC_VOICE_WS_URL || 'ws://10.0.0.169:5024/api/voice/ws/stream';

console.log('🎤 Voice Streaming Test Script');
console.log('================================');
console.log(`Connecting to: ${WS_URL}`);

const ws = new WebSocket(WS_URL);

let sessionId = null;
let messageCount = 0;

ws.on('open', () => {
  console.log('✅ WebSocket connected successfully');

  // Send test audio chunks
  console.log('\n📤 Sending test audio data...');

  // Simulate audio streaming
  const sendTestAudio = () => {
    // Create dummy PCM audio data (silence)
    const sampleRate = 16000;
    const chunkDuration = 0.25; // 250ms
    const samplesPerChunk = Math.floor(sampleRate * chunkDuration);

    // Create Float32Array of silence
    const audioData = new Float32Array(samplesPerChunk);

    // Convert to base64
    const buffer = Buffer.from(audioData.buffer);
    const base64Audio = buffer.toString('base64');

    // Send audio chunk
    ws.send(JSON.stringify({
      type: 'audio',
      data: base64Audio,
    }));

    messageCount++;
    console.log(`  Chunk ${messageCount} sent (${samplesPerChunk} samples)`);
  };

  // Send 10 chunks over 2.5 seconds
  let chunksSent = 0;
  const interval = setInterval(() => {
    if (chunksSent < 10) {
      sendTestAudio();
      chunksSent++;
    } else {
      clearInterval(interval);

      // Send end signal
      console.log('\n📤 Sending end signal...');
      ws.send(JSON.stringify({ type: 'end' }));

      // Close after a delay
      setTimeout(() => {
        ws.close();
      }, 2000);
    }
  }, 250);
});

ws.on('message', (data) => {
  try {
    const message = JSON.parse(data);
    console.log('\n📥 Received message:');
    console.log(`  Type: ${message.type}`);

    switch (message.type) {
      case 'status':
        console.log(`  Session ID: ${message.session_id || 'N/A'}`);
        console.log(`  Message: ${message.message}`);
        if (message.session_id) {
          sessionId = message.session_id;
        }
        break;

      case 'partial':
        console.log(`  Text: "${message.text}"`);
        console.log(`  Confidence: ${message.confidence || 'N/A'}`);
        console.log(`  Is Partial: ${message.is_partial !== false}`);
        break;

      case 'final':
        console.log(`  ✅ Final Text: "${message.text}"`);
        console.log(`  Confidence: ${message.confidence || 'N/A'}`);
        console.log(`  Reason: ${message.reason || 'N/A'}`);
        break;

      case 'error':
        console.log(`  ❌ Error: ${message.message || message.error}`);
        break;

      default:
        console.log(`  Data: ${JSON.stringify(message)}`);
    }
  } catch (error) {
    console.log('  Raw data:', data.toString());
  }
});

ws.on('close', () => {
  console.log('\n✅ WebSocket connection closed');
  console.log('\nTest Summary:');
  console.log(`  Session ID: ${sessionId || 'Not assigned'}`);
  console.log(`  Audio chunks sent: ${messageCount}`);
  console.log('\n✨ Test completed successfully!');
});

ws.on('error', (error) => {
  console.error('\n❌ WebSocket error:', error.message);
  console.error('\nMake sure the backend server is running on port 5024');
  console.error('Run: ./start_server.sh');
  process.exit(1);
});