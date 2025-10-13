"""
Verify Signup Code Tool
Verifies the code provided by user during signup flow
"""

import logging
from typing import Dict, Any

from services.tools.base import ITool, ToolResult
from services.verification_service import get_verification_service

logger = logging.getLogger(__name__)


class VerifySignupCodeTool(ITool):
    """Tool for verifying codes provided by users during signup"""

    def name(self) -> str:
        return "verify_signup_code"

    async def execute(self, **kwargs) -> ToolResult:
        """
        Verify the code provided by user

        Args:
            verification_id (str): Verification ID from send_verification_code (required)
            code (str): 6-digit code provided by user (required)
            email (str): Email address for double-check (required)
            session_id (str): Session ID for state persistence (optional)

        Returns:
            ToolResult with verification status and store information if successful
        """
        try:
            # Extract parameters
            verification_id = kwargs.get('verification_id')
            code = kwargs.get('code')
            email = kwargs.get('email')
            session_id = kwargs.get('session_id')

            # Validate inputs
            if not verification_id:
                return ToolResult(
                    success=False,
                    error="Verification ID is required"
                )

            if not code:
                return ToolResult(
                    success=False,
                    error="Verification code is required"
                )

            if not email:
                return ToolResult(
                    success=False,
                    error="Email address is required"
                )

            # Clean code (remove spaces, dashes)
            code = code.strip().replace(' ', '').replace('-', '')

            # Validate code format
            if not code.isdigit() or len(code) != 6:
                return ToolResult(
                    success=False,
                    error="Invalid code format. Code must be 6 digits."
                )

            # Get verification service
            verification_service = get_verification_service()

            # Verify code
            is_valid, error_message, verification_record = verification_service.verify_code(
                verification_id=verification_id,
                code=code,
                email=email
            )

            if not is_valid:
                logger.warning(
                    f"Code verification failed for {email}: {error_message}"
                )
                return ToolResult(
                    success=False,
                    error=error_message
                )

            # Success! Extract information
            if not verification_record:
                return ToolResult(
                    success=False,
                    error="Verification record not found"
                )

            logger.info(f"Code verified successfully for {email}")

            # Store code verification in signup state if session_id provided
            if session_id:
                try:
                    from services.signup_state_manager import get_signup_state_manager, SignupStep
                    state_manager = get_signup_state_manager()
                    state_manager.update_signup_state(
                        session_id=session_id,
                        step=SignupStep.CREATING_TENANT,
                        data={'code_verified': True}
                    )
                    logger.info(f"Stored code verification in state for session {session_id}")
                except Exception as e:
                    logger.warning(f"Failed to store code verification state: {e}")
                    # Don't fail the tool if state storage fails

            return ToolResult(
                success=True,
                data={
                    'is_valid': True,
                    'email': verification_record.email,
                    'phone': verification_record.phone,
                    'verification_tier': verification_record.verification_tier,
                    'store_info': verification_record.store_info,
                    'verification_id': verification_id,
                    'ready_for_tenant_creation': True
                }
            )

        except Exception as e:
            logger.error(f"Error in verify_signup_code: {e}", exc_info=True)
            return ToolResult(
                success=False,
                error=f"Verification error: {str(e)}"
            )
