import React from 'react';
import ChatWidgetV2 from '../ChatWidgetV2';

/**
 * Example implementation of the enhanced ChatWidget with voice capabilities
 *
 * This example demonstrates all available props and configuration options
 */
const ChatWidgetExample: React.FC = () => {
  return (
    <div>
      {/* Basic Usage */}
      <ChatWidgetV2 />

      {/* Advanced Usage with All Props */}
      <ChatWidgetV2
        wsUrl="ws://your-api-url/chat/ws"
        defaultOpen={false}
        position="bottom-right"
        theme="auto"
        enableVoice={true}
        maxMessages={100}
      />

      {/* Mobile-Optimized Version */}
      <ChatWidgetV2
        defaultOpen={true}
        position="bottom-left"
        enableVoice={true}
        maxMessages={50}
      />
    </div>
  );
};

/**
 * Integration Guide
 *
 * 1. Import the ChatWidget:
 *    import ChatWidgetV2 from '@/components/ChatWidgetV2';
 *
 * 2. Add to your app layout:
 *    <ChatWidgetV2 enableVoice={true} />
 *
 * 3. Ensure WebSocket server is running on the specified port
 *
 * 4. For voice features, HTTPS is required in production
 *
 * Props:
 * - wsUrl: WebSocket endpoint URL (configured via environment variables)
 * - defaultOpen: Whether chat starts open (default: false)
 * - position: Corner position (default: bottom-right)
 * - theme: Color theme - light/dark/auto (default: auto)
 * - enableVoice: Enable voice recording (default: true)
 * - maxMessages: Maximum messages to keep in memory (default: 100)
 *
 * Voice Requirements:
 * - Browser must support MediaRecorder API
 * - User must grant microphone permission
 * - HTTPS required for production
 *
 * Features:
 * - Real-time WebSocket communication
 * - Voice recording with visual feedback
 * - Automatic transcription
 * - Token counting and tracking
 * - Responsive design (mobile-friendly)
 * - Dark mode support
 * - Drag and resize capabilities (desktop)
 * - Message history with timestamps
 * - Connection status indicators
 * - Typing indicators with activity animations
 * - Auto-reconnection on disconnect
 *
 * Accessibility:
 * - Full keyboard navigation
 * - ARIA labels for all interactive elements
 * - Screen reader compatible
 * - High contrast mode support
 * - Focus management
 *
 * Performance:
 * - Message virtualization for long conversations
 * - Efficient re-rendering with React.memo
 * - Debounced resize handlers
 * - Optimized animation frames for voice visualization
 * - Automatic cleanup of resources
 */

export default ChatWidgetExample;