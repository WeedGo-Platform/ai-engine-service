"""
CRSA Validation Tool for Signup Flow
Validates license number and determines verification tier based on email domain matching
"""

import logging
from typing import Dict, Any
from urllib.parse import urlparse
import re

from services.tools.base import ITool, ToolResult
from core.services.ontario_crsa_service import OntarioCRSAService
from core.repositories.ontario_crsa_repository import OntarioCRSARepository
import asyncpg
import os

logger = logging.getLogger(__name__)


class ValidateCRSASignupTool(ITool):
    """Tool for validating CRSA license and checking email domain match"""

    def __init__(self):
        self._db_pool: asyncpg.Pool | None = None

    def name(self) -> str:
        return "validate_crsa_signup"

    async def _get_db_pool(self) -> asyncpg.Pool:
        """Get or create database connection pool"""
        if self._db_pool is None:
            self._db_pool = await asyncpg.create_pool(
                host=os.getenv('DB_HOST', 'localhost'),
                port=int(os.getenv('DB_PORT', 5434)),
                user=os.getenv('DB_USER', 'weedgo'),
                password=os.getenv('DB_PASSWORD', 'your_password_here'),
                database=os.getenv('DB_NAME', 'ai_engine'),
                min_size=2,
                max_size=10
            )
        return self._db_pool

    def _extract_domain_from_website(self, website: str | None) -> str | None:
        """
        Extract domain from website URL

        Args:
            website: Website URL (e.g., "https://www.candreamcannabis.ca/")

        Returns:
            Domain (e.g., "candreamcannabis.ca") or None
        """
        if not website:
            return None

        try:
            parsed = urlparse(website)
            domain = parsed.netloc or parsed.path

            # Remove www. prefix
            if domain.startswith('www.'):
                domain = domain[4:]

            # Remove trailing slashes
            domain = domain.rstrip('/')

            return domain.lower()

        except Exception as e:
            logger.error(f"Error extracting domain from {website}: {e}")
            return None

    def _extract_domain_from_email(self, email: str) -> str:
        """
        Extract domain from email address

        Args:
            email: Email address (e.g., "contact@candreamcannabis.ca")

        Returns:
            Domain (e.g., "candreamcannabis.ca")
        """
        try:
            return email.split('@')[1].lower()
        except (IndexError, AttributeError):
            return ""

    def _check_domain_match(self, email: str, website: str | None) -> bool:
        """
        Check if email domain matches website domain

        Args:
            email: Email address
            website: Website URL from CRSA

        Returns:
            True if domains match, False otherwise
        """
        if not website:
            return False

        email_domain = self._extract_domain_from_email(email)
        website_domain = self._extract_domain_from_website(website)

        if not email_domain or not website_domain:
            return False

        # Exact match
        if email_domain == website_domain:
            return True

        # Check if they share a common base domain
        # e.g., candream.com matches candreamcannabis.com
        email_parts = email_domain.split('.')
        website_parts = website_domain.split('.')

        # Get the main domain (last 2 parts)
        if len(email_parts) >= 2 and len(website_parts) >= 2:
            email_main = '.'.join(email_parts[-2:])
            website_main = '.'.join(website_parts[-2:])

            # Check if one is a subdomain of the other
            if email_main == website_main:
                return True

        return False

    async def execute(self, **kwargs) -> ToolResult:
        """
        Execute CRSA validation and domain matching

        Args:
            license_number (str): CRSA license number (required)
            email (str): Business email to verify (required)
            phone (str): Business phone for SMS verification (optional)
            session_id (str): Session ID for state persistence (optional)

        Returns:
            ToolResult with validation result and store information
        """
        try:
            # Extract parameters
            license_number = kwargs.get('license_number')
            email = kwargs.get('email')
            phone = kwargs.get('phone')
            session_id = kwargs.get('session_id')

            # Validate inputs
            if not license_number:
                return ToolResult(
                    success=False,
                    error="License number is required"
                )

            if not email:
                return ToolResult(
                    success=False,
                    error="Email address is required"
                )

            # Validate email format
            email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_regex, email):
                return ToolResult(
                    success=False,
                    error="Invalid email address format"
                )

            # Clean license number (remove CRSA prefix if present)
            license_number = license_number.strip().upper()
            if license_number.startswith('CRSA'):
                license_number = license_number[4:]
            license_number = f"CRSA{license_number}"

            # Get database pool and create service
            pool = await self._get_db_pool()
            repository = OntarioCRSARepository(pool)
            service = OntarioCRSAService(repository)

            # Validate license
            validation = await service.validate_license(license_number)

            if not validation.is_valid:
                return ToolResult(
                    success=False,
                    error=validation.error_message or "License validation failed"
                )

            # Extract store information
            crsa_record = validation.crsa_record
            if not crsa_record:
                return ToolResult(
                    success=False,
                    error="Store information not found"
                )

            store_info = {
                'license_number': crsa_record.license_number,
                'store_name': crsa_record.store_name,
                'address': crsa_record.address,
                'municipality': crsa_record.municipality or crsa_record.first_nation,
                'store_status': crsa_record.store_application_status,
                'website': crsa_record.website,
                'crsa_id': str(crsa_record.id)
            }

            # Check domain match
            domain_match = self._check_domain_match(email, crsa_record.website)

            # Determine verification tier
            if domain_match:
                verification_tier = "auto_approved"
                tier_message = (
                    "Your email domain matches your business website. "
                    "Your account will be activated immediately after verification."
                )
            else:
                verification_tier = "manual_review"
                tier_message = (
                    "For security, your account will be reviewed by our team within 24 hours. "
                    "You'll receive an email once approved."
                )

            logger.info(
                f"CRSA validation successful for {license_number}. "
                f"Domain match: {domain_match}, Tier: {verification_tier}"
            )

            # Store validation results in signup state if session_id provided
            if session_id:
                try:
                    from services.signup_state_manager import get_signup_state_manager
                    state_manager = get_signup_state_manager()
                    state_manager.store_crsa_validation(
                        session_id=session_id,
                        store_info=store_info,
                        verification_tier=verification_tier,
                        domain_match=domain_match
                    )
                    logger.info(f"Stored CRSA validation in state for session {session_id}")
                except Exception as e:
                    logger.warning(f"Failed to store validation state: {e}")
                    # Don't fail the tool if state storage fails

            return ToolResult(
                success=True,
                data={
                    'is_valid': True,
                    'store_info': store_info,
                    'domain_match': domain_match,
                    'verification_tier': verification_tier,
                    'tier_message': tier_message,
                    'email': email,
                    'phone': phone,
                    'email_domain': self._extract_domain_from_email(email),
                    'website_domain': self._extract_domain_from_website(crsa_record.website)
                }
            )

        except Exception as e:
            logger.error(f"Error in validate_crsa_signup: {e}", exc_info=True)
            return ToolResult(
                success=False,
                error=f"Validation error: {str(e)}"
            )
