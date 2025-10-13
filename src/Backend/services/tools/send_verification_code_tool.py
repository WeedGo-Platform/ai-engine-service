"""
Send Verification Code Tool
Sends verification code via email (and optionally SMS) depending on verification tier
"""

import logging
from typing import Dict, Any

from services.tools.base import ITool, ToolResult
from services.verification_service import get_verification_service
from services.notification_service import get_notification_service

logger = logging.getLogger(__name__)


class SendVerificationCodeTool(ITool):
    """Tool for sending verification codes during signup"""

    def name(self) -> str:
        return "send_verification_code"

    async def execute(self, **kwargs) -> ToolResult:
        """
        Send verification code via email (and SMS if needed)

        Args:
            email (str): Email address (required)
            phone (str): Phone number (optional, required for manual_review)
            verification_tier (str): "auto_approved" or "manual_review" (required)
            store_name (str): Store name for personalized message (required)
            store_info (dict): Full store info from CRSA validation (required)

        Returns:
            ToolResult with verification_id and send status
        """
        try:
            # Extract parameters
            email = kwargs.get('email')
            phone = kwargs.get('phone')
            verification_tier = kwargs.get('verification_tier')
            store_name = kwargs.get('store_name')
            store_info = kwargs.get('store_info')

            # Validate inputs
            if not email:
                return ToolResult(
                    success=False,
                    error="Email address is required"
                )

            if not verification_tier:
                return ToolResult(
                    success=False,
                    error="Verification tier is required"
                )

            if verification_tier not in ["auto_approved", "manual_review"]:
                return ToolResult(
                    success=False,
                    error="Invalid verification tier. Must be 'auto_approved' or 'manual_review'"
                )

            if not store_name:
                return ToolResult(
                    success=False,
                    error="Store name is required"
                )

            if not store_info:
                return ToolResult(
                    success=False,
                    error="Store information is required"
                )

            # Check phone required for manual review
            if verification_tier == "manual_review" and not phone:
                return ToolResult(
                    success=False,
                    error="Phone number is required for manual review verification"
                )

            # Get services
            verification_service = get_verification_service()
            notification_service = get_notification_service()

            try:
                # Generate verification code
                code, verification_id = verification_service.generate_code(
                    email=email,
                    store_info=store_info,
                    verification_tier=verification_tier,
                    phone=phone,
                    code_length=6,
                    expiry_minutes=5
                )

                # Send email
                email_success, email_error = await notification_service.send_verification_email(
                    to_email=email,
                    code=code,
                    store_name=store_name,
                    verification_tier=verification_tier
                )

                if not email_success:
                    return ToolResult(
                        success=False,
                        error=f"Failed to send email: {email_error}"
                    )

                methods_used = ["email"]

                # Send SMS for manual review tier
                if verification_tier == "manual_review" and phone:
                    sms_success, sms_error = await notification_service.send_verification_sms(
                        to_phone=phone,
                        code=code,
                        store_name=store_name
                    )

                    if sms_success:
                        methods_used.append("sms")
                    else:
                        logger.warning(f"SMS send failed but continuing with email only: {sms_error}")

                logger.info(
                    f"Verification code sent to {email} "
                    f"(methods: {', '.join(methods_used)}, tier: {verification_tier})"
                )

                return ToolResult(
                    success=True,
                    data={
                        'code_sent': True,
                        'verification_id': verification_id,
                        'methods': methods_used,
                        'expires_in_seconds': 300,  # 5 minutes
                        'max_attempts': 3,
                        'email': email,
                        'phone': phone if verification_tier == "manual_review" else None,
                        'verification_tier': verification_tier
                    }
                )

            except ValueError as e:
                # Rate limit exceeded
                return ToolResult(
                    success=False,
                    error=str(e)
                )

        except Exception as e:
            logger.error(f"Error in send_verification_code: {e}", exc_info=True)
            return ToolResult(
                success=False,
                error=f"Failed to send verification code: {str(e)}"
            )
