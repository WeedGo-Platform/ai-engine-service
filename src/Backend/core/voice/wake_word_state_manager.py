"""
Wake Word State Management System for V5
Manages the state of wake word detection sessions and persists configuration
Following SOLID principles and clean architecture patterns
"""
import asyncio
import logging
import json
import time
from typing import Dict, Any, Optional, List, Callable, Set
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta
from pathlib import Path
from enum import Enum
import uuid
from collections import deque

from .wake_word_handler import WakeWordModel, WakeWordConfig, WakeWordDetection

logger = logging.getLogger(__name__)


class WakeWordSessionState(Enum):
    """States for wake word detection session"""
    IDLE = "idle"
    LISTENING_FOR_WAKE_WORD = "listening_for_wake_word"
    WAKE_WORD_DETECTED = "wake_word_detected"
    LISTENING_FOR_COMMAND = "listening_for_command"
    PROCESSING_COMMAND = "processing_command"
    COOLDOWN = "cooldown"
    ERROR = "error"
    SUSPENDED = "suspended"


@dataclass
class WakeWordSession:
    """Represents a wake word detection session"""
    session_id: str
    device_id: Optional[str]
    user_id: Optional[str]
    state: WakeWordSessionState
    created_at: datetime
    updated_at: datetime
    wake_word_count: int = 0
    command_count: int = 0
    false_positive_count: int = 0
    last_wake_word: Optional[str] = None
    last_wake_time: Optional[datetime] = None
    last_command: Optional[str] = None
    last_command_time: Optional[datetime] = None
    config: Optional[WakeWordConfig] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary for serialization"""
        return {
            "session_id": self.session_id,
            "device_id": self.device_id,
            "user_id": self.user_id,
            "state": self.state.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "wake_word_count": self.wake_word_count,
            "command_count": self.command_count,
            "false_positive_count": self.false_positive_count,
            "last_wake_word": self.last_wake_word,
            "last_wake_time": self.last_wake_time.isoformat() if self.last_wake_time else None,
            "last_command": self.last_command,
            "last_command_time": self.last_command_time.isoformat() if self.last_command_time else None,
            "config": asdict(self.config) if self.config else None,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WakeWordSession':
        """Create session from dictionary"""
        # Parse dates
        created_at = datetime.fromisoformat(data["created_at"])
        updated_at = datetime.fromisoformat(data["updated_at"])
        last_wake_time = None
        if data.get("last_wake_time"):
            last_wake_time = datetime.fromisoformat(data["last_wake_time"])
        last_command_time = None
        if data.get("last_command_time"):
            last_command_time = datetime.fromisoformat(data["last_command_time"])

        # Parse config
        config = None
        if data.get("config"):
            config_data = data["config"]
            models = [WakeWordModel(m) for m in config_data.get("models", [])]
            config = WakeWordConfig(
                models=models,
                threshold=config_data.get("threshold", 0.5),
                sensitivity=config_data.get("sensitivity", 0.5)
            )

        return cls(
            session_id=data["session_id"],
            device_id=data.get("device_id"),
            user_id=data.get("user_id"),
            state=WakeWordSessionState(data["state"]),
            created_at=created_at,
            updated_at=updated_at,
            wake_word_count=data.get("wake_word_count", 0),
            command_count=data.get("command_count", 0),
            false_positive_count=data.get("false_positive_count", 0),
            last_wake_word=data.get("last_wake_word"),
            last_wake_time=last_wake_time,
            last_command=data.get("last_command"),
            last_command_time=last_command_time,
            config=config,
            metadata=data.get("metadata", {})
        )


@dataclass
class StateTransition:
    """Represents a state transition"""
    from_state: WakeWordSessionState
    to_state: WakeWordSessionState
    timestamp: datetime
    trigger: str
    data: Optional[Dict[str, Any]] = None


class WakeWordStateManager:
    """Manages wake word detection states and sessions"""

    def __init__(self, config_dir: Optional[Path] = None):
        """Initialize state manager

        Args:
            config_dir: Directory for persisting state and config
        """
        self.config_dir = config_dir or Path("config/voice/wake_word")
        self.config_dir.mkdir(parents=True, exist_ok=True)

        # Active sessions
        self.sessions: Dict[str, WakeWordSession] = {}

        # State transition history (limited size per session)
        self.transition_history: Dict[str, deque] = {}
        self.max_history_size = 100

        # State transition callbacks
        self.transition_callbacks: Dict[WakeWordSessionState, List[Callable]] = {}

        # Privacy mode
        self.privacy_mode = False
        self.privacy_indicators: Set[str] = set()

        # Load persisted state
        self._load_state()

        # Cleanup task
        self.cleanup_task: Optional[asyncio.Task] = None

    def _load_state(self) -> None:
        """Load persisted state from disk"""
        state_file = self.config_dir / "state.json"
        if state_file.exists():
            try:
                with open(state_file, 'r') as f:
                    data = json.load(f)

                # Load sessions
                for session_data in data.get("sessions", []):
                    session = WakeWordSession.from_dict(session_data)
                    self.sessions[session.session_id] = session

                # Load privacy settings
                self.privacy_mode = data.get("privacy_mode", False)
                self.privacy_indicators = set(data.get("privacy_indicators", []))

                logger.info(f"Loaded {len(self.sessions)} sessions from state file")

            except Exception as e:
                logger.error(f"Failed to load state: {e}")

    def _save_state(self) -> None:
        """Persist current state to disk"""
        try:
            state_file = self.config_dir / "state.json"

            # Prepare data
            data = {
                "sessions": [s.to_dict() for s in self.sessions.values()],
                "privacy_mode": self.privacy_mode,
                "privacy_indicators": list(self.privacy_indicators),
                "saved_at": datetime.now().isoformat()
            }

            # Write atomically
            temp_file = state_file.with_suffix(".tmp")
            with open(temp_file, 'w') as f:
                json.dump(data, f, indent=2)
            temp_file.replace(state_file)

            logger.debug("State saved successfully")

        except Exception as e:
            logger.error(f"Failed to save state: {e}")

    async def create_session(
        self,
        device_id: Optional[str] = None,
        user_id: Optional[str] = None,
        config: Optional[WakeWordConfig] = None
    ) -> WakeWordSession:
        """Create a new wake word session

        Args:
            device_id: Device identifier
            user_id: User identifier
            config: Wake word configuration

        Returns:
            Created session
        """
        session_id = str(uuid.uuid4())
        now = datetime.now()

        session = WakeWordSession(
            session_id=session_id,
            device_id=device_id,
            user_id=user_id,
            state=WakeWordSessionState.IDLE,
            created_at=now,
            updated_at=now,
            config=config
        )

        self.sessions[session_id] = session
        self.transition_history[session_id] = deque(maxlen=self.max_history_size)

        # Save state
        self._save_state()

        logger.info(f"Created session: {session_id}")
        return session

    async def transition_state(
        self,
        session_id: str,
        new_state: WakeWordSessionState,
        trigger: str,
        data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Transition session to new state

        Args:
            session_id: Session identifier
            new_state: Target state
            trigger: What triggered the transition
            data: Additional transition data

        Returns:
            Success status
        """
        if session_id not in self.sessions:
            logger.error(f"Session not found: {session_id}")
            return False

        session = self.sessions[session_id]
        old_state = session.state

        # Validate transition
        if not self._is_valid_transition(old_state, new_state):
            logger.warning(f"Invalid transition: {old_state.value} -> {new_state.value}")
            return False

        # Update session
        session.state = new_state
        session.updated_at = datetime.now()

        # Record transition
        transition = StateTransition(
            from_state=old_state,
            to_state=new_state,
            timestamp=datetime.now(),
            trigger=trigger,
            data=data
        )
        self.transition_history[session_id].append(transition)

        # Trigger callbacks
        await self._trigger_callbacks(new_state, session, transition)

        # Save state
        self._save_state()

        logger.debug(f"Session {session_id}: {old_state.value} -> {new_state.value} (trigger: {trigger})")
        return True

    def _is_valid_transition(
        self,
        from_state: WakeWordSessionState,
        to_state: WakeWordSessionState
    ) -> bool:
        """Check if state transition is valid

        Args:
            from_state: Current state
            to_state: Target state

        Returns:
            Whether transition is valid
        """
        # Define valid transitions
        valid_transitions = {
            WakeWordSessionState.IDLE: [
                WakeWordSessionState.LISTENING_FOR_WAKE_WORD,
                WakeWordSessionState.SUSPENDED,
                WakeWordSessionState.ERROR
            ],
            WakeWordSessionState.LISTENING_FOR_WAKE_WORD: [
                WakeWordSessionState.WAKE_WORD_DETECTED,
                WakeWordSessionState.IDLE,
                WakeWordSessionState.SUSPENDED,
                WakeWordSessionState.ERROR
            ],
            WakeWordSessionState.WAKE_WORD_DETECTED: [
                WakeWordSessionState.LISTENING_FOR_COMMAND,
                WakeWordSessionState.COOLDOWN,
                WakeWordSessionState.LISTENING_FOR_WAKE_WORD,
                WakeWordSessionState.ERROR
            ],
            WakeWordSessionState.LISTENING_FOR_COMMAND: [
                WakeWordSessionState.PROCESSING_COMMAND,
                WakeWordSessionState.LISTENING_FOR_WAKE_WORD,
                WakeWordSessionState.COOLDOWN,
                WakeWordSessionState.ERROR
            ],
            WakeWordSessionState.PROCESSING_COMMAND: [
                WakeWordSessionState.LISTENING_FOR_WAKE_WORD,
                WakeWordSessionState.COOLDOWN,
                WakeWordSessionState.IDLE,
                WakeWordSessionState.ERROR
            ],
            WakeWordSessionState.COOLDOWN: [
                WakeWordSessionState.LISTENING_FOR_WAKE_WORD,
                WakeWordSessionState.IDLE
            ],
            WakeWordSessionState.ERROR: [
                WakeWordSessionState.IDLE,
                WakeWordSessionState.LISTENING_FOR_WAKE_WORD
            ],
            WakeWordSessionState.SUSPENDED: [
                WakeWordSessionState.IDLE,
                WakeWordSessionState.LISTENING_FOR_WAKE_WORD
            ]
        }

        return to_state in valid_transitions.get(from_state, [])

    async def _trigger_callbacks(
        self,
        state: WakeWordSessionState,
        session: WakeWordSession,
        transition: StateTransition
    ) -> None:
        """Trigger callbacks for state transition

        Args:
            state: New state
            session: Session that transitioned
            transition: Transition details
        """
        callbacks = self.transition_callbacks.get(state, [])
        for callback in callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(session, transition)
                else:
                    callback(session, transition)
            except Exception as e:
                logger.error(f"Callback error: {e}")

    def register_callback(
        self,
        state: WakeWordSessionState,
        callback: Callable
    ) -> None:
        """Register callback for state transitions

        Args:
            state: State to trigger callback
            callback: Function to call
        """
        if state not in self.transition_callbacks:
            self.transition_callbacks[state] = []
        self.transition_callbacks[state].append(callback)

    async def record_wake_word(
        self,
        session_id: str,
        detection: WakeWordDetection
    ) -> None:
        """Record wake word detection

        Args:
            session_id: Session identifier
            detection: Wake word detection result
        """
        if session_id not in self.sessions:
            return

        session = self.sessions[session_id]
        session.wake_word_count += 1
        session.last_wake_word = detection.wake_word
        session.last_wake_time = datetime.now()
        session.updated_at = datetime.now()

        # Save state
        self._save_state()

    async def record_command(
        self,
        session_id: str,
        command: str
    ) -> None:
        """Record command after wake word

        Args:
            session_id: Session identifier
            command: Command text
        """
        if session_id not in self.sessions:
            return

        session = self.sessions[session_id]
        session.command_count += 1
        session.last_command = command
        session.last_command_time = datetime.now()
        session.updated_at = datetime.now()

        # Save state
        self._save_state()

    def mark_false_positive(self, session_id: str) -> None:
        """Mark a false positive detection

        Args:
            session_id: Session identifier
        """
        if session_id in self.sessions:
            self.sessions[session_id].false_positive_count += 1
            self._save_state()

    def get_session(self, session_id: str) -> Optional[WakeWordSession]:
        """Get session by ID

        Args:
            session_id: Session identifier

        Returns:
            Session or None if not found
        """
        return self.sessions.get(session_id)

    def get_active_sessions(self) -> List[WakeWordSession]:
        """Get all active (non-idle) sessions

        Returns:
            List of active sessions
        """
        return [
            s for s in self.sessions.values()
            if s.state != WakeWordSessionState.IDLE
        ]

    def get_session_metrics(self, session_id: str) -> Dict[str, Any]:
        """Get metrics for a session

        Args:
            session_id: Session identifier

        Returns:
            Session metrics
        """
        session = self.sessions.get(session_id)
        if not session:
            return {}

        now = datetime.now()
        duration = (now - session.created_at).total_seconds()

        # Calculate metrics
        wake_word_rate = session.wake_word_count / max(duration / 3600, 1)  # Per hour
        command_rate = session.command_count / max(duration / 3600, 1)  # Per hour
        false_positive_rate = (
            session.false_positive_count / max(session.wake_word_count, 1)
            if session.wake_word_count > 0 else 0
        )

        return {
            "session_id": session_id,
            "state": session.state.value,
            "duration_seconds": duration,
            "wake_word_count": session.wake_word_count,
            "command_count": session.command_count,
            "false_positive_count": session.false_positive_count,
            "wake_word_rate_per_hour": wake_word_rate,
            "command_rate_per_hour": command_rate,
            "false_positive_rate": false_positive_rate,
            "last_activity": session.updated_at.isoformat()
        }

    def enable_privacy_mode(self, indicator: str) -> None:
        """Enable privacy mode with indicator

        Args:
            indicator: Privacy indicator (e.g., "microphone_muted")
        """
        self.privacy_mode = True
        self.privacy_indicators.add(indicator)

        # Suspend all active sessions
        for session in self.sessions.values():
            if session.state == WakeWordSessionState.LISTENING_FOR_WAKE_WORD:
                session.state = WakeWordSessionState.SUSPENDED

        self._save_state()
        logger.info(f"Privacy mode enabled: {indicator}")

    def disable_privacy_mode(self, indicator: str) -> None:
        """Disable privacy mode

        Args:
            indicator: Privacy indicator to remove
        """
        self.privacy_indicators.discard(indicator)

        # Disable privacy mode if no indicators remain
        if not self.privacy_indicators:
            self.privacy_mode = False

            # Resume suspended sessions
            for session in self.sessions.values():
                if session.state == WakeWordSessionState.SUSPENDED:
                    session.state = WakeWordSessionState.IDLE

            logger.info("Privacy mode disabled")

        self._save_state()

    def is_privacy_mode(self) -> bool:
        """Check if privacy mode is enabled

        Returns:
            Privacy mode status
        """
        return self.privacy_mode

    async def cleanup_old_sessions(self, max_age_hours: int = 24) -> int:
        """Clean up old inactive sessions

        Args:
            max_age_hours: Maximum age for inactive sessions

        Returns:
            Number of sessions cleaned up
        """
        now = datetime.now()
        cutoff = now - timedelta(hours=max_age_hours)
        removed = 0

        sessions_to_remove = []
        for session_id, session in self.sessions.items():
            # Remove old idle sessions
            if (session.state == WakeWordSessionState.IDLE and
                    session.updated_at < cutoff):
                sessions_to_remove.append(session_id)

        # Remove sessions
        for session_id in sessions_to_remove:
            del self.sessions[session_id]
            if session_id in self.transition_history:
                del self.transition_history[session_id]
            removed += 1

        if removed > 0:
            self._save_state()
            logger.info(f"Cleaned up {removed} old sessions")

        return removed

    async def start_cleanup_task(self, interval_hours: int = 1) -> None:
        """Start periodic cleanup task

        Args:
            interval_hours: Cleanup interval in hours
        """
        async def cleanup_loop():
            while True:
                try:
                    await asyncio.sleep(interval_hours * 3600)
                    await self.cleanup_old_sessions()
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Cleanup task error: {e}")

        self.cleanup_task = asyncio.create_task(cleanup_loop())

    def stop_cleanup_task(self) -> None:
        """Stop cleanup task"""
        if self.cleanup_task:
            self.cleanup_task.cancel()
            self.cleanup_task = None

    def get_global_metrics(self) -> Dict[str, Any]:
        """Get global metrics across all sessions

        Returns:
            Global metrics
        """
        total_wake_words = sum(s.wake_word_count for s in self.sessions.values())
        total_commands = sum(s.command_count for s in self.sessions.values())
        total_false_positives = sum(s.false_positive_count for s in self.sessions.values())

        active_sessions = self.get_active_sessions()

        return {
            "total_sessions": len(self.sessions),
            "active_sessions": len(active_sessions),
            "total_wake_words": total_wake_words,
            "total_commands": total_commands,
            "total_false_positives": total_false_positives,
            "privacy_mode": self.privacy_mode,
            "privacy_indicators": list(self.privacy_indicators)
        }