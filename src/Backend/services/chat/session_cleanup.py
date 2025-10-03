"""
Session Cleanup Manager for Chat Service.

Provides automatic cleanup of expired sessions to prevent memory leaks
in hybrid and in-memory storage configurations.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Set
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SessionCleanupConfig:
    """Configuration for session cleanup"""
    session_ttl_minutes: int = 60  # Time-to-live for inactive sessions
    cleanup_interval_seconds: int = 300  # Cleanup check interval (5 minutes)
    max_session_age_hours: int = 24  # Maximum age regardless of activity
    enable_cleanup: bool = True  # Master switch for cleanup


class SessionCleanupManager:
    """
    Manages automatic cleanup of expired chat sessions.

    Features:
    - TTL-based expiration for inactive sessions
    - Maximum age enforcement
    - Graceful shutdown with cleanup task management
    - Metrics tracking for monitoring
    """

    def __init__(
        self,
        chat_service,
        config: Optional[SessionCleanupConfig] = None
    ):
        """
        Initialize cleanup manager.

        Args:
            chat_service: ChatService instance to manage
            config: Cleanup configuration (uses defaults if not provided)
        """
        self.chat_service = chat_service
        self.config = config or SessionCleanupConfig()
        self._cleanup_task: Optional[asyncio.Task] = None
        self._running = False
        self._cleanup_count = 0
        self._last_cleanup = None
        logger.info(
            f"SessionCleanupManager initialized "
            f"(TTL: {self.config.session_ttl_minutes}m, "
            f"Interval: {self.config.cleanup_interval_seconds}s)"
        )

    async def start(self):
        """Start the background cleanup task"""
        if not self.config.enable_cleanup:
            logger.info("Session cleanup disabled by configuration")
            return

        if self._running:
            logger.warning("Cleanup manager already running")
            return

        self._running = True
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info("✅ Session cleanup task started")

    async def stop(self):
        """Stop the background cleanup task"""
        if not self._running:
            return

        self._running = False
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None

        logger.info(f"Session cleanup stopped (cleaned {self._cleanup_count} sessions total)")

    async def _cleanup_loop(self):
        """Main cleanup loop that runs periodically"""
        logger.info("Session cleanup loop started")

        while self._running:
            try:
                await asyncio.sleep(self.config.cleanup_interval_seconds)

                if not self._running:
                    break

                await self._perform_cleanup()

            except asyncio.CancelledError:
                logger.info("Cleanup loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}", exc_info=True)
                # Continue running despite errors
                await asyncio.sleep(60)  # Wait 1 minute before retrying

    async def _perform_cleanup(self):
        """Perform actual cleanup of expired sessions"""
        try:
            start_time = datetime.utcnow()
            expired_sessions = await self._find_expired_sessions()

            if not expired_sessions:
                logger.debug("No expired sessions found")
                self._last_cleanup = start_time
                return

            # Delete expired sessions
            deleted_count = 0
            for session_id in expired_sessions:
                try:
                    success = await self.chat_service.delete_session(session_id)
                    if success:
                        deleted_count += 1
                        logger.debug(f"Cleaned up expired session: {session_id}")
                except Exception as e:
                    logger.error(f"Failed to delete session {session_id}: {e}")

            # Update metrics
            self._cleanup_count += deleted_count
            self._last_cleanup = start_time
            cleanup_duration = (datetime.utcnow() - start_time).total_seconds()

            logger.info(
                f"Session cleanup completed: {deleted_count} expired sessions removed "
                f"in {cleanup_duration:.2f}s "
                f"(Total cleaned: {self._cleanup_count})"
            )

        except Exception as e:
            logger.error(f"Error performing cleanup: {e}", exc_info=True)

    async def _find_expired_sessions(self) -> Set[str]:
        """
        Find sessions that should be expired.

        Returns:
            Set of session IDs to be cleaned up
        """
        expired_sessions = set()
        now = datetime.utcnow()

        # Access internal sessions dict
        # Note: This assumes ChatService exposes _sessions or has a method to list sessions
        sessions = self.chat_service._sessions

        for session_id, session in sessions.items():
            # Check if session is already marked inactive
            if not session.is_active:
                expired_sessions.add(session_id)
                continue

            # Check TTL - session inactive for too long
            time_since_update = (now - session.updated_at).total_seconds() / 60
            if time_since_update > self.config.session_ttl_minutes:
                logger.debug(
                    f"Session {session_id} expired due to inactivity "
                    f"({time_since_update:.1f} minutes)"
                )
                expired_sessions.add(session_id)
                continue

            # Check maximum age
            session_age_hours = (now - session.created_at).total_seconds() / 3600
            if session_age_hours > self.config.max_session_age_hours:
                logger.debug(
                    f"Session {session_id} expired due to age "
                    f"({session_age_hours:.1f} hours)"
                )
                expired_sessions.add(session_id)

        return expired_sessions

    def get_metrics(self) -> Dict:
        """
        Get cleanup metrics for monitoring.

        Returns:
            Dict containing cleanup statistics
        """
        return {
            "running": self._running,
            "total_cleaned": self._cleanup_count,
            "last_cleanup": self._last_cleanup.isoformat() if self._last_cleanup else None,
            "current_session_count": len(self.chat_service._sessions),
            "config": {
                "session_ttl_minutes": self.config.session_ttl_minutes,
                "cleanup_interval_seconds": self.config.cleanup_interval_seconds,
                "max_session_age_hours": self.config.max_session_age_hours
            }
        }

    async def force_cleanup(self) -> int:
        """
        Force an immediate cleanup cycle.

        Returns:
            Number of sessions cleaned
        """
        logger.info("Forcing immediate cleanup")
        count_before = len(self.chat_service._sessions)
        await self._perform_cleanup()
        count_after = len(self.chat_service._sessions)
        return count_before - count_after
