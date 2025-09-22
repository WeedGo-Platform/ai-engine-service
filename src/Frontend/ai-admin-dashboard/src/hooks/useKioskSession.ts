import { useState, useEffect, useCallback } from 'react';
import { v4 as uuidv4 } from 'uuid';

interface KioskSession {
  sessionId: string;
  customerId?: string;
  language: string;
  startTime: Date;
  lastActivity: Date;
  isGuest: boolean;
}

const SESSION_KEY = 'kiosk_session';
const SESSION_TIMEOUT = 30 * 60 * 1000; // 30 minutes

export function useKioskSession() {
  const [session, setSession] = useState<KioskSession | null>(null);

  // Initialize or restore session
  const initializeSession = useCallback((customerId?: string, language = 'en') => {
    const newSession: KioskSession = {
      sessionId: uuidv4(),
      customerId,
      language,
      startTime: new Date(),
      lastActivity: new Date(),
      isGuest: !customerId,
    };

    setSession(newSession);
    localStorage.setItem(SESSION_KEY, JSON.stringify(newSession));
    return newSession;
  }, []);

  // Update session activity
  const updateActivity = useCallback(() => {
    if (session) {
      const updatedSession = {
        ...session,
        lastActivity: new Date(),
      };
      setSession(updatedSession);
      localStorage.setItem(SESSION_KEY, JSON.stringify(updatedSession));
    }
  }, [session]);

  // Clear session
  const clearSession = useCallback(() => {
    setSession(null);
    localStorage.removeItem(SESSION_KEY);
  }, []);

  // Check session validity
  const isSessionValid = useCallback(() => {
    if (!session) return false;

    const now = new Date();
    const lastActivity = new Date(session.lastActivity);
    const timeSinceActivity = now.getTime() - lastActivity.getTime();

    return timeSinceActivity < SESSION_TIMEOUT;
  }, [session]);

  // Restore session on mount
  useEffect(() => {
    const storedSession = localStorage.getItem(SESSION_KEY);
    if (storedSession) {
      try {
        const parsedSession = JSON.parse(storedSession);
        const sessionObj = {
          ...parsedSession,
          startTime: new Date(parsedSession.startTime),
          lastActivity: new Date(parsedSession.lastActivity),
        };

        // Check if session is still valid
        const now = new Date();
        const timeSinceActivity = now.getTime() - sessionObj.lastActivity.getTime();

        if (timeSinceActivity < SESSION_TIMEOUT) {
          setSession(sessionObj);
        } else {
          // Session expired, clear it
          clearSession();
        }
      } catch (error) {
        console.error('Failed to restore kiosk session:', error);
        clearSession();
      }
    }
  }, [clearSession]);

  // Auto-clear session on timeout
  useEffect(() => {
    if (!session) return;

    const checkTimeout = setInterval(() => {
      if (!isSessionValid()) {
        clearSession();
      }
    }, 60000); // Check every minute

    return () => clearInterval(checkTimeout);
  }, [session, isSessionValid, clearSession]);

  return {
    session,
    initializeSession,
    updateActivity,
    clearSession,
    isSessionValid,
  };
}