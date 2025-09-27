/**
 * WebSocket Service Unit Tests
 * Tests for WebSocket connection and messaging
 */

import { WebSocketService } from '../services/websocket';

// Mock WebSocket
class MockWebSocket {
  readyState: number;
  url: string;
  onopen: ((event: Event) => void) | null = null;
  onclose: ((event: CloseEvent) => void) | null = null;
  onerror: ((event: Event) => void) | null = null;
  onmessage: ((event: MessageEvent) => void) | null = null;

  constructor(url: string) {
    this.url = url;
    this.readyState = WebSocket.CONNECTING;

    // Simulate connection after a delay
    setTimeout(() => {
      this.readyState = WebSocket.OPEN;
      if (this.onopen) {
        this.onopen(new Event('open'));
      }
    }, 0);
  }

  send(data: string) {
    if (this.readyState !== WebSocket.OPEN) {
      throw new Error('WebSocket is not open');
    }
  }

  close() {
    this.readyState = WebSocket.CLOSED;
    if (this.onclose) {
      this.onclose(new CloseEvent('close'));
    }
  }
}

// Replace global WebSocket
(global as any).WebSocket = MockWebSocket;

describe('WebSocketService', () => {
  let wsService: WebSocketService;

  beforeEach(() => {
    wsService = new WebSocketService('ws://localhost:5024/agi/ws');
    jest.clearAllTimers();
  });

  afterEach(() => {
    wsService.disconnect();
  });

  describe('Connection Management', () => {
    it('should establish connection to WebSocket server', (done) => {
      wsService.connect();

      wsService.on('connected', () => {
        expect(wsService.isConnected()).toBe(true);
        done();
      });
    });

    it('should disconnect from WebSocket server', (done) => {
      wsService.connect();

      wsService.on('connected', () => {
        wsService.disconnect();
        expect(wsService.isConnected()).toBe(false);
        done();
      });
    });

    it('should handle connection errors', (done) => {
      wsService.on('error', (error) => {
        expect(error).toBeDefined();
        done();
      });

      wsService.connect();

      // Simulate error
      const ws = (wsService as any).ws;
      if (ws && ws.onerror) {
        ws.onerror(new Event('error'));
      }
    });

    it('should automatically reconnect on disconnect', (done) => {
      jest.useFakeTimers();
      let connectionCount = 0;

      wsService.on('connected', () => {
        connectionCount++;
        if (connectionCount === 2) {
          expect(connectionCount).toBe(2);
          jest.useRealTimers();
          done();
        } else {
          // Simulate disconnect
          const ws = (wsService as any).ws;
          ws.close();
        }
      });

      wsService.connect();
      jest.advanceTimersByTime(5000);
    });

    it('should respect max reconnection attempts', () => {
      jest.useFakeTimers();
      const maxAttempts = 3;
      wsService = new WebSocketService('ws://localhost:5024', { maxReconnectAttempts: maxAttempts });

      let attemptCount = 0;
      wsService.on('reconnecting', () => {
        attemptCount++;
      });

      wsService.connect();

      // Simulate multiple disconnects
      for (let i = 0; i < maxAttempts + 1; i++) {
        const ws = (wsService as any).ws;
        if (ws) ws.close();
        jest.advanceTimersByTime(5000);
      }

      expect(attemptCount).toBeLessThanOrEqual(maxAttempts);
      jest.useRealTimers();
    });
  });

  describe('Message Handling', () => {
    it('should send messages when connected', (done) => {
      wsService.connect();

      wsService.on('connected', () => {
        const message = { type: 'test', data: 'hello' };
        const sent = wsService.send(message);
        expect(sent).toBe(true);
        done();
      });
    });

    it('should queue messages when not connected', () => {
      const message = { type: 'test', data: 'hello' };
      const sent = wsService.send(message);

      expect(sent).toBe(false);
      expect((wsService as any).messageQueue.length).toBe(1);
    });

    it('should send queued messages on connection', (done) => {
      const messages = [
        { type: 'test1', data: 'hello1' },
        { type: 'test2', data: 'hello2' }
      ];

      messages.forEach(msg => wsService.send(msg));
      expect((wsService as any).messageQueue.length).toBe(2);

      wsService.connect();

      wsService.on('connected', () => {
        setTimeout(() => {
          expect((wsService as any).messageQueue.length).toBe(0);
          done();
        }, 100);
      });
    });

    it('should parse incoming JSON messages', (done) => {
      const testMessage = { type: 'update', data: { id: 1, value: 'test' } };

      wsService.on('message', (message) => {
        expect(message).toEqual(testMessage);
        done();
      });

      wsService.connect();

      wsService.on('connected', () => {
        const ws = (wsService as any).ws;
        if (ws && ws.onmessage) {
          ws.onmessage(new MessageEvent('message', {
            data: JSON.stringify(testMessage)
          }));
        }
      });
    });

    it('should handle message parsing errors', (done) => {
      wsService.on('error', (error) => {
        expect(error).toContain('Failed to parse message');
        done();
      });

      wsService.connect();

      wsService.on('connected', () => {
        const ws = (wsService as any).ws;
        if (ws && ws.onmessage) {
          ws.onmessage(new MessageEvent('message', {
            data: 'invalid json'
          }));
        }
      });
    });
  });

  describe('Event Subscription', () => {
    it('should subscribe to specific message types', (done) => {
      const handler = jest.fn();
      wsService.subscribe('agent_update', handler);

      wsService.connect();

      wsService.on('connected', () => {
        const ws = (wsService as any).ws;
        if (ws && ws.onmessage) {
          ws.onmessage(new MessageEvent('message', {
            data: JSON.stringify({ type: 'agent_update', data: { id: 1 } })
          }));

          expect(handler).toHaveBeenCalledWith({ id: 1 });
          done();
        }
      });
    });

    it('should unsubscribe from message types', (done) => {
      const handler = jest.fn();
      const unsubscribe = wsService.subscribe('test', handler);

      wsService.connect();

      wsService.on('connected', () => {
        unsubscribe();

        const ws = (wsService as any).ws;
        if (ws && ws.onmessage) {
          ws.onmessage(new MessageEvent('message', {
            data: JSON.stringify({ type: 'test', data: {} })
          }));

          expect(handler).not.toHaveBeenCalled();
          done();
        }
      });
    });

    it('should handle multiple subscribers for same type', (done) => {
      const handler1 = jest.fn();
      const handler2 = jest.fn();

      wsService.subscribe('test', handler1);
      wsService.subscribe('test', handler2);

      wsService.connect();

      wsService.on('connected', () => {
        const ws = (wsService as any).ws;
        if (ws && ws.onmessage) {
          ws.onmessage(new MessageEvent('message', {
            data: JSON.stringify({ type: 'test', data: { value: 1 } })
          }));

          expect(handler1).toHaveBeenCalledWith({ value: 1 });
          expect(handler2).toHaveBeenCalledWith({ value: 1 });
          done();
        }
      });
    });
  });

  describe('Heartbeat', () => {
    it('should send heartbeat messages periodically', (done) => {
      jest.useFakeTimers();
      const sendSpy = jest.spyOn(wsService, 'send');

      wsService.connect();

      wsService.on('connected', () => {
        jest.advanceTimersByTime(30000);

        expect(sendSpy).toHaveBeenCalledWith({ type: 'ping' });
        jest.useRealTimers();
        done();
      });
    });

    it('should reconnect if heartbeat fails', (done) => {
      jest.useFakeTimers();
      let reconnectCalled = false;

      wsService.on('reconnecting', () => {
        reconnectCalled = true;
      });

      wsService.connect();

      wsService.on('connected', () => {
        // Simulate no pong response
        jest.advanceTimersByTime(60000);

        expect(reconnectCalled).toBe(true);
        jest.useRealTimers();
        done();
      });
    });
  });

  describe('Connection State', () => {
    it('should track connection state correctly', (done) => {
      expect(wsService.getConnectionState()).toBe('disconnected');

      wsService.connect();
      expect(wsService.getConnectionState()).toBe('connecting');

      wsService.on('connected', () => {
        expect(wsService.getConnectionState()).toBe('connected');

        wsService.disconnect();
        expect(wsService.getConnectionState()).toBe('disconnected');
        done();
      });
    });

    it('should provide connection statistics', (done) => {
      wsService.connect();

      wsService.on('connected', () => {
        const stats = wsService.getStats();

        expect(stats).toHaveProperty('connected');
        expect(stats).toHaveProperty('messagesSent');
        expect(stats).toHaveProperty('messagesReceived');
        expect(stats).toHaveProperty('connectionTime');
        expect(stats.connected).toBe(true);
        done();
      });
    });
  });

  describe('Error Recovery', () => {
    it('should handle send failures gracefully', (done) => {
      wsService.connect();

      wsService.on('connected', () => {
        // Close connection to simulate failure
        const ws = (wsService as any).ws;
        ws.readyState = WebSocket.CLOSED;

        const sent = wsService.send({ type: 'test' });
        expect(sent).toBe(false);
        done();
      });
    });

    it('should clear message queue on max size', () => {
      wsService = new WebSocketService('ws://localhost:5024', { maxQueueSize: 5 });

      for (let i = 0; i < 10; i++) {
        wsService.send({ type: 'test', id: i });
      }

      expect((wsService as any).messageQueue.length).toBeLessThanOrEqual(5);
    });
  });
});