"""
Create Tenant Signup Tool
Creates tenant account after successful code verification and links with CRSA
"""

import logging
import secrets
from typing import Dict, Any
from uuid import uuid4, UUID
from datetime import datetime, timedelta
import os
import asyncpg

from services.tools.base import ITool, ToolResult
from services.verification_service import get_verification_service
from services.notification_service import get_notification_service
from core.services.tenant_service import TenantService
from core.services.ontario_crsa_service import OntarioCRSAService
from core.repositories.tenant_repository import TenantRepository
from core.repositories.subscription_repository import SubscriptionRepository
from core.repositories.ontario_crsa_repository import OntarioCRSARepository
from core.domain.models import SubscriptionTier

logger = logging.getLogger(__name__)


class CreateTenantSignupTool(ITool):
    """Tool for creating tenant account after successful verification"""

    def __init__(self):
        self._db_pool: asyncpg.Pool | None = None
        # Password setup tokens (in-memory for now, should be Redis in production)
        self._password_tokens: Dict[str, Dict[str, Any]] = {}

    def name(self) -> str:
        return "create_tenant_signup"

    async def _get_db_pool(self) -> asyncpg.Pool:
        """Get or create database connection pool"""
        if self._db_pool is None:
            self._db_pool = await asyncpg.create_pool(
                host=os.getenv('DB_HOST', 'localhost'),
                port=int(os.getenv('DB_PORT', 5434)),
                user=os.getenv('DB_USER', 'weedgo'),
                password=os.getenv('DB_PASSWORD', 'weedgo123'),
                database=os.getenv('DB_NAME', 'ai_engine'),
                min_size=2,
                max_size=10
            )
        return self._db_pool

    def _generate_password_setup_token(self, tenant_id: UUID, email: str) -> tuple[str, str]:
        """
        Generate a secure password setup token

        Returns:
            tuple of (token, setup_link)
        """
        # Generate secure random token
        token = secrets.token_urlsafe(32)

        # Store token with expiry (24 hours)
        expires_at = datetime.utcnow() + timedelta(hours=24)

        self._password_tokens[token] = {
            'tenant_id': str(tenant_id),
            'email': email,
            'created_at': datetime.utcnow(),
            'expires_at': expires_at,
            'used': False
        }

        # Generate setup link (should be configured based on environment)
        base_url = os.getenv('FRONTEND_URL', 'https://admin.weedgo.com')
        setup_link = f"{base_url}/setup-password?token={token}"

        return token, setup_link

    def _generate_tenant_code(self, store_name: str, license_number: str) -> str:
        """
        Generate unique tenant code from store name and license

        Args:
            store_name: Store name from CRSA
            license_number: CRSA license number

        Returns:
            Tenant code (e.g., "candream_1202256")
        """
        # Clean store name
        clean_name = ''.join(c.lower() if c.isalnum() else '_' for c in store_name)
        clean_name = clean_name.strip('_')

        # Get license digits
        license_digits = ''.join(c for c in license_number if c.isdigit())

        # Combine and truncate
        code = f"{clean_name}_{license_digits}"
        if len(code) > 50:
            code = code[:50]

        return code

    async def execute(self, **kwargs) -> ToolResult:
        """
        Create tenant account after successful verification

        Args:
            verification_id (str): Verified verification ID (required)
            email (str): Email address (required)
            phone (str): Phone number (optional)
            contact_name (str): Contact person name (required)
            contact_role (str): Contact person role (required)
            session_id (str): Session ID for state persistence (optional)

        Returns:
            ToolResult with tenant_id and password setup information
        """
        try:
            # Extract parameters
            verification_id = kwargs.get('verification_id')
            email = kwargs.get('email')
            phone = kwargs.get('phone')
            contact_name = kwargs.get('contact_name')
            contact_role = kwargs.get('contact_role')
            session_id = kwargs.get('session_id')

            # Validate inputs
            if not verification_id:
                return ToolResult(
                    success=False,
                    error="Verification ID is required"
                )

            if not email:
                return ToolResult(
                    success=False,
                    error="Email address is required"
                )

            if not contact_name:
                return ToolResult(
                    success=False,
                    error="Contact name is required"
                )

            if not contact_role:
                return ToolResult(
                    success=False,
                    error="Contact role is required"
                )

            # Get and verify the verification record
            verification_service = get_verification_service()
            verification_info = verification_service.get_verification_info(verification_id)

            if not verification_info:
                return ToolResult(
                    success=False,
                    error="Invalid or expired verification. Please start signup again."
                )

            if verification_info['is_expired']:
                return ToolResult(
                    success=False,
                    error="Verification has expired. Please start signup again."
                )

            # Extract store info
            store_info = verification_info['store_info']
            verification_tier = verification_info['verification_tier']

            # Get database pool and create services
            pool = await self._get_db_pool()
            tenant_repo = TenantRepository(pool)
            subscription_repo = SubscriptionRepository(pool)
            tenant_service = TenantService(tenant_repo, subscription_repo)

            crsa_repo = OntarioCRSARepository(pool)
            crsa_service = OntarioCRSAService(crsa_repo)

            # Generate tenant code
            tenant_code = self._generate_tenant_code(
                store_info['store_name'],
                store_info['license_number']
            )

            # Check if tenant code already exists
            existing_tenant = await tenant_service.get_tenant_by_code(tenant_code)
            if existing_tenant:
                # Append random suffix
                tenant_code = f"{tenant_code}_{secrets.token_hex(4)}"

            # Determine initial subscription tier (always start with FREE)
            subscription_tier = SubscriptionTier.COMMUNITY_AND_NEW_BUSINESS

            # Parse address from CRSA
            address = {
                'street': store_info['address'],
                'city': store_info['municipality'] or '',
                'province': 'Ontario',  # All CRSA records are Ontario
                'postal_code': '',  # Not provided in CRSA data
                'country': 'Canada'
            }

            # Create tenant
            tenant = await tenant_service.create_tenant(
                name=store_info['store_name'],
                code=tenant_code,
                contact_email=email,
                subscription_tier=subscription_tier,
                company_name=store_info['store_name'],
                address=address,
                contact_phone=phone,
                website=store_info.get('website'),
                settings={
                    'crsa_license': store_info['license_number'],
                    'verification_tier': verification_tier,
                    'signup_contact': {
                        'name': contact_name,
                        'role': contact_role,
                        'email': email,
                        'phone': phone
                    },
                    'signup_date': datetime.utcnow().isoformat(),
                    'needs_manual_review': verification_tier == "manual_review"
                }
            )

            # Link CRSA record to tenant
            try:
                await crsa_service.link_to_tenant(
                    license_number=store_info['license_number'],
                    tenant_id=tenant.id
                )
                logger.info(
                    f"Linked CRSA license {store_info['license_number']} to tenant {tenant.id}"
                )
            except Exception as e:
                logger.error(f"Failed to link CRSA to tenant: {e}")
                # Don't fail the whole signup, but log the error
                # Admin can manually link later

            # Generate password setup token
            token, setup_link = self._generate_password_setup_token(tenant.id, email)

            # Send password setup email
            notification_service = get_notification_service()
            email_success, email_error = await notification_service.send_password_setup_email(
                to_email=email,
                store_name=store_info['store_name'],
                setup_link=setup_link,
                tenant_id=str(tenant.id)
            )

            if not email_success:
                logger.error(f"Failed to send password setup email: {email_error}")
                # Don't fail signup, but note the issue

            # Mark verification as complete
            verification_service.mark_verified(verification_id)

            logger.info(
                f"Created tenant {tenant.id} for {store_info['store_name']} "
                f"(tier: {verification_tier}, email: {email})"
            )

            # Determine account status
            if verification_tier == "auto_approved":
                account_status = "active"
                status_message = (
                    "Your account is active! Check your email for the password setup link."
                )
            else:
                account_status = "pending_review"
                status_message = (
                    "Your account is pending review. Our team will verify your information "
                    "within 24 hours. You'll receive an email once approved."
                )

            # Store tenant creation in signup state if session_id provided
            if session_id:
                try:
                    from services.signup_state_manager import get_signup_state_manager
                    state_manager = get_signup_state_manager()
                    state_manager.store_tenant_creation(
                        session_id=session_id,
                        tenant_id=str(tenant.id),
                        tenant_code=tenant.code,
                        account_status=account_status
                    )
                    logger.info(f"Stored tenant creation in state for session {session_id}")
                except Exception as e:
                    logger.warning(f"Failed to store tenant creation state: {e}")
                    # Don't fail the tool if state storage fails

            return ToolResult(
                success=True,
                data={
                    'tenant_id': str(tenant.id),
                    'tenant_code': tenant.code,
                    'store_name': store_info['store_name'],
                    'license_number': store_info['license_number'],
                    'account_status': account_status,
                    'verification_tier': verification_tier,
                    'status_message': status_message,
                    'email': email,
                    'password_setup_link': setup_link,  # For testing/dev
                    'password_setup_sent': email_success,
                    'needs_manual_review': verification_tier == "manual_review",
                    'subscription_tier': subscription_tier.value,
                    'contact_name': contact_name,
                    'contact_role': contact_role
                }
            )

        except ValueError as e:
            # Business logic errors (duplicate code, etc.)
            logger.error(f"Business logic error in create_tenant_signup: {e}")
            return ToolResult(
                success=False,
                error=str(e)
            )
        except Exception as e:
            logger.error(f"Error in create_tenant_signup: {e}", exc_info=True)
            return ToolResult(
                success=False,
                error=f"Failed to create account: {str(e)}"
            )
