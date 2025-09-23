/**
 * Secure logging utility that sanitizes sensitive data and only logs in development
 */

import { removeSensitiveFields } from './security';

type LogLevel = 'debug' | 'info' | 'warn' | 'error';

interface LoggerConfig {
  enabled: boolean;
  level: LogLevel;
  sanitize: boolean;
}

class Logger {
  private config: LoggerConfig = {
    enabled: import.meta.env.DEV,
    level: 'debug',
    sanitize: true
  };

  private shouldLog(level: LogLevel): boolean {
    if (!this.config.enabled) return false;

    const levels: LogLevel[] = ['debug', 'info', 'warn', 'error'];
    const currentLevelIndex = levels.indexOf(this.config.level);
    const requestedLevelIndex = levels.indexOf(level);

    return requestedLevelIndex >= currentLevelIndex;
  }

  private sanitizeData(data: any): any {
    if (!this.config.sanitize) return data;

    if (typeof data === 'object' && data !== null) {
      return removeSensitiveFields(data);
    }

    // Mask potential sensitive strings
    if (typeof data === 'string') {
      // Don't log tokens or keys
      if (data.includes('Bearer ') || data.includes('token') || data.includes('key')) {
        return '[REDACTED]';
      }
    }

    return data;
  }

  private log(level: LogLevel, message: string, ...args: any[]): void {
    if (!this.shouldLog(level)) return;

    const sanitizedArgs = args.map(arg => this.sanitizeData(arg));
    const timestamp = new Date().toISOString();
    const prefix = `[${timestamp}] [${level.toUpperCase()}]`;

    switch (level) {
      case 'debug':
        console.log(prefix, message, ...sanitizedArgs);
        break;
      case 'info':
        console.info(prefix, message, ...sanitizedArgs);
        break;
      case 'warn':
        console.warn(prefix, message, ...sanitizedArgs);
        break;
      case 'error':
        console.error(prefix, message, ...sanitizedArgs);
        break;
    }
  }

  debug(message: string, ...args: any[]): void {
    this.log('debug', message, ...args);
  }

  info(message: string, ...args: any[]): void {
    this.log('info', message, ...args);
  }

  warn(message: string, ...args: any[]): void {
    this.log('warn', message, ...args);
  }

  error(message: string, ...args: any[]): void {
    this.log('error', message, ...args);
  }

  // Group related logs
  group(label: string): void {
    if (this.config.enabled) {
      console.group(label);
    }
  }

  groupEnd(): void {
    if (this.config.enabled) {
      console.groupEnd();
    }
  }

  // Timing utilities
  time(label: string): void {
    if (this.config.enabled) {
      console.time(label);
    }
  }

  timeEnd(label: string): void {
    if (this.config.enabled) {
      console.timeEnd(label);
    }
  }

  // Configure logger
  configure(config: Partial<LoggerConfig>): void {
    this.config = { ...this.config, ...config };
  }
}

// Export singleton instance
export const logger = new Logger();

// Export default for convenience
export default logger;