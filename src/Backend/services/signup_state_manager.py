"""
Signup State Manager
Manages signup flow state persistence in chat context
Handles recovery from interrupted signups
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class SignupStep(str, Enum):
    """Signup flow steps"""
    NOT_STARTED = "not_started"
    COLLECTING_INFO = "collecting_info"
    VALIDATING_CRSA = "validating_crsa"
    SENDING_CODE = "sending_code"
    VERIFYING_CODE = "verifying_code"
    CREATING_TENANT = "creating_tenant"
    COMPLETED = "completed"
    FAILED = "failed"


class SignupStateManager:
    """
    Manages signup state persistence across chat sessions
    Integrates with ContextManager for state storage
    """

    def __init__(self, context_manager):
        """
        Initialize signup state manager

        Args:
            context_manager: ContextManager instance for state persistence
        """
        self.context_manager = context_manager
        logger.info("SignupStateManager initialized")

    def get_signup_state(self, session_id: str) -> Dict[str, Any]:
        """
        Get current signup state for a session

        Args:
            session_id: Session identifier

        Returns:
            Signup state dictionary
        """
        try:
            context = self.context_manager.get_context(session_id)
            signup_state = context.get('signup_state', {})

            # Check if state has expired (30 minutes timeout)
            if signup_state and 'last_updated' in signup_state:
                last_updated = datetime.fromisoformat(signup_state['last_updated'])
                if datetime.utcnow() - last_updated > timedelta(minutes=30):
                    logger.info(f"Signup state expired for session {session_id}, resetting")
                    return self._create_empty_state()

            return signup_state if signup_state else self._create_empty_state()

        except Exception as e:
            logger.error(f"Error getting signup state for session {session_id}: {e}")
            return self._create_empty_state()

    def update_signup_state(
        self,
        session_id: str,
        step: SignupStep,
        data: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Update signup state for a session

        Args:
            session_id: Session identifier
            step: Current signup step
            data: Additional state data to merge
        """
        try:
            current_state = self.get_signup_state(session_id)

            # Update step and timestamp
            current_state['current_step'] = step.value
            current_state['last_updated'] = datetime.utcnow().isoformat()

            # Merge additional data
            if data:
                for key, value in data.items():
                    current_state[key] = value

            # Track step history
            if 'step_history' not in current_state:
                current_state['step_history'] = []

            current_state['step_history'].append({
                'step': step.value,
                'timestamp': datetime.utcnow().isoformat()
            })

            # Update context
            self.context_manager.update_context(session_id, {'signup_state': current_state})

            logger.info(f"Updated signup state for session {session_id}: step={step.value}")

        except Exception as e:
            logger.error(f"Error updating signup state for session {session_id}: {e}")

    def store_collected_info(
        self,
        session_id: str,
        contact_name: Optional[str] = None,
        contact_role: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        license_number: Optional[str] = None
    ) -> None:
        """
        Store collected user information in signup state

        Args:
            session_id: Session identifier
            contact_name: User's full name
            contact_role: User's role at dispensary
            email: User's email address
            phone: User's phone number (optional)
            license_number: CRSA license number
        """
        try:
            info = {}
            if contact_name:
                info['contact_name'] = contact_name
            if contact_role:
                info['contact_role'] = contact_role
            if email:
                info['email'] = email
            if phone:
                info['phone'] = phone
            if license_number:
                info['license_number'] = license_number

            self.update_signup_state(
                session_id,
                SignupStep.COLLECTING_INFO,
                {'collected_info': info}
            )

            logger.info(f"Stored collected info for session {session_id}")

        except Exception as e:
            logger.error(f"Error storing collected info for session {session_id}: {e}")

    def store_crsa_validation(
        self,
        session_id: str,
        store_info: Dict[str, Any],
        verification_tier: str,
        domain_match: bool
    ) -> None:
        """
        Store CRSA validation results in signup state

        Args:
            session_id: Session identifier
            store_info: Store information from CRSA validation
            verification_tier: "auto_approved" or "manual_review"
            domain_match: Whether email domain matched website
        """
        try:
            self.update_signup_state(
                session_id,
                SignupStep.VALIDATING_CRSA,
                {
                    'store_info': store_info,
                    'verification_tier': verification_tier,
                    'domain_match': domain_match,
                    'crsa_validated': True
                }
            )

            logger.info(f"Stored CRSA validation for session {session_id}: tier={verification_tier}")

        except Exception as e:
            logger.error(f"Error storing CRSA validation for session {session_id}: {e}")

    def store_verification_id(
        self,
        session_id: str,
        verification_id: str,
        methods: list[str]
    ) -> None:
        """
        Store verification ID and methods in signup state

        Args:
            session_id: Session identifier
            verification_id: Verification ID from send_verification_code
            methods: List of verification methods used (e.g., ["email", "sms"])
        """
        try:
            self.update_signup_state(
                session_id,
                SignupStep.VERIFYING_CODE,
                {
                    'verification_id': verification_id,
                    'verification_methods': methods,
                    'code_sent_at': datetime.utcnow().isoformat()
                }
            )

            logger.info(f"Stored verification ID for session {session_id}")

        except Exception as e:
            logger.error(f"Error storing verification ID for session {session_id}: {e}")

    def store_tenant_creation(
        self,
        session_id: str,
        tenant_id: str,
        tenant_code: str,
        account_status: str
    ) -> None:
        """
        Store tenant creation results in signup state

        Args:
            session_id: Session identifier
            tenant_id: Created tenant ID
            tenant_code: Tenant code
            account_status: "active" or "pending_review"
        """
        try:
            self.update_signup_state(
                session_id,
                SignupStep.COMPLETED,
                {
                    'tenant_id': tenant_id,
                    'tenant_code': tenant_code,
                    'account_status': account_status,
                    'completed_at': datetime.utcnow().isoformat()
                }
            )

            logger.info(f"Stored tenant creation for session {session_id}: tenant_id={tenant_id}")

        except Exception as e:
            logger.error(f"Error storing tenant creation for session {session_id}: {e}")

    def mark_failed(
        self,
        session_id: str,
        error_message: str,
        failed_step: SignupStep
    ) -> None:
        """
        Mark signup as failed with error information

        Args:
            session_id: Session identifier
            error_message: Error message describing failure
            failed_step: Step where failure occurred
        """
        try:
            self.update_signup_state(
                session_id,
                SignupStep.FAILED,
                {
                    'error_message': error_message,
                    'failed_step': failed_step.value,
                    'failed_at': datetime.utcnow().isoformat()
                }
            )

            logger.warning(f"Marked signup as failed for session {session_id}: {error_message}")

        except Exception as e:
            logger.error(f"Error marking signup as failed for session {session_id}: {e}")

    def can_recover_from_interruption(self, session_id: str) -> bool:
        """
        Check if signup can be recovered from interruption

        Args:
            session_id: Session identifier

        Returns:
            True if signup can be recovered, False otherwise
        """
        try:
            state = self.get_signup_state(session_id)
            current_step = state.get('current_step')

            # Can't recover if not started or already completed/failed
            if not current_step or current_step in [
                SignupStep.NOT_STARTED.value,
                SignupStep.COMPLETED.value,
                SignupStep.FAILED.value
            ]:
                return False

            # Can recover if we have the minimum required data
            if current_step == SignupStep.COLLECTING_INFO.value:
                # Need at least email and license number to continue
                info = state.get('collected_info', {})
                return bool(info.get('email') and info.get('license_number'))

            elif current_step == SignupStep.VALIDATING_CRSA.value:
                # Need validation results
                return state.get('crsa_validated', False)

            elif current_step == SignupStep.VERIFYING_CODE.value:
                # Need verification ID
                return bool(state.get('verification_id'))

            elif current_step == SignupStep.CREATING_TENANT.value:
                # Need verified code
                return bool(state.get('code_verified'))

            return False

        except Exception as e:
            logger.error(f"Error checking recovery for session {session_id}: {e}")
            return False

    def get_recovery_info(self, session_id: str) -> Dict[str, Any]:
        """
        Get information needed to recover an interrupted signup

        Args:
            session_id: Session identifier

        Returns:
            Dictionary with recovery information
        """
        try:
            state = self.get_signup_state(session_id)

            if not self.can_recover_from_interruption(session_id):
                return {'can_recover': False}

            current_step = state.get('current_step')

            return {
                'can_recover': True,
                'current_step': current_step,
                'collected_info': state.get('collected_info', {}),
                'store_info': state.get('store_info', {}),
                'verification_tier': state.get('verification_tier'),
                'verification_id': state.get('verification_id'),
                'last_updated': state.get('last_updated'),
                'next_action': self._get_next_action(current_step)
            }

        except Exception as e:
            logger.error(f"Error getting recovery info for session {session_id}: {e}")
            return {'can_recover': False, 'error': str(e)}

    def clear_signup_state(self, session_id: str) -> None:
        """
        Clear signup state for a session

        Args:
            session_id: Session identifier
        """
        try:
            self.context_manager.update_context(session_id, {'signup_state': {}})
            logger.info(f"Cleared signup state for session {session_id}")

        except Exception as e:
            logger.error(f"Error clearing signup state for session {session_id}: {e}")

    def _create_empty_state(self) -> Dict[str, Any]:
        """Create an empty signup state"""
        return {
            'current_step': SignupStep.NOT_STARTED.value,
            'last_updated': datetime.utcnow().isoformat(),
            'step_history': [],
            'collected_info': {},
            'store_info': {},
            'verification_tier': None,
            'verification_id': None,
            'tenant_id': None
        }

    def _get_next_action(self, current_step: str) -> str:
        """Get next action description based on current step"""
        next_actions = {
            SignupStep.COLLECTING_INFO.value: "Validate CRSA license",
            SignupStep.VALIDATING_CRSA.value: "Send verification code",
            SignupStep.VERIFYING_CODE.value: "Verify code provided by user",
            SignupStep.CREATING_TENANT.value: "Complete tenant creation"
        }
        return next_actions.get(current_step, "Unknown")


# Global singleton instance
_signup_state_manager: Optional[SignupStateManager] = None


def get_signup_state_manager(context_manager=None) -> SignupStateManager:
    """Get or create signup state manager singleton"""
    global _signup_state_manager

    if _signup_state_manager is None:
        if context_manager is None:
            # Import here to avoid circular dependency
            from services.context_manager import ContextManager
            context_manager = ContextManager()

        _signup_state_manager = SignupStateManager(context_manager)

    return _signup_state_manager
