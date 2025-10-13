"""
Ontario CRSA Service - Business Logic Layer
Handles validation, search, and tenant linking for Ontario Cannabis Retail Store Authorization
"""

from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
import logging

from core.domain.models import OntarioCRSA, CRSAVerificationStatus
from core.repositories.interfaces import IOntarioCRSARepository

logger = logging.getLogger(__name__)


class ValidationResult:
    """Result of license validation"""

    def __init__(
        self,
        is_valid: bool,
        crsa_record: Optional[OntarioCRSA] = None,
        error_message: Optional[str] = None
    ):
        self.is_valid = is_valid
        self.crsa_record = crsa_record
        self.error_message = error_message


class OntarioCRSAService:
    """Service for Ontario CRSA validation and management"""

    def __init__(self, crsa_repository: IOntarioCRSARepository):
        self.crsa_repo = crsa_repository

    async def validate_license(self, license_number: str) -> ValidationResult:
        """
        Validate an Ontario cannabis retail license number

        Args:
            license_number: License number to validate

        Returns:
            ValidationResult with validation status and CRSA record if found
        """
        try:
            # Clean license number
            license_number = license_number.strip()

            if not license_number:
                return ValidationResult(
                    is_valid=False,
                    error_message="License number is required"
                )

            # Lookup in database
            crsa_record = await self.crsa_repo.get_by_license(license_number)

            if not crsa_record:
                return ValidationResult(
                    is_valid=False,
                    error_message=f"License number '{license_number}' not found in AGCO database. "
                                  f"Please verify the license number or contact support."
                )

            # Check if active
            if not crsa_record.is_active:
                return ValidationResult(
                    is_valid=False,
                    crsa_record=crsa_record,
                    error_message=f"License '{license_number}' is inactive in AGCO database"
                )

            # Check if authorized
            if not crsa_record.is_authorized():
                return ValidationResult(
                    is_valid=False,
                    crsa_record=crsa_record,
                    error_message=f"Store is not authorized to open. Current status: {crsa_record.store_application_status}"
                )

            # Check if already linked to a tenant
            if crsa_record.linked_tenant_id:
                return ValidationResult(
                    is_valid=False,
                    crsa_record=crsa_record,
                    error_message=f"License '{license_number}' is already registered to another tenant"
                )

            # Valid!
            logger.info(f"License '{license_number}' validated successfully for store '{crsa_record.store_name}'")
            return ValidationResult(
                is_valid=True,
                crsa_record=crsa_record
            )

        except Exception as e:
            logger.error(f"Error validating license {license_number}: {e}")
            return ValidationResult(
                is_valid=False,
                error_message="An error occurred during validation. Please try again."
            )

    async def get_store_info(self, license_number: str) -> Optional[OntarioCRSA]:
        """
        Get store information by license number

        Args:
            license_number: License number to lookup

        Returns:
            OntarioCRSA record if found, None otherwise
        """
        try:
            return await self.crsa_repo.get_by_license(license_number)
        except Exception as e:
            logger.error(f"Error getting store info for license {license_number}: {e}")
            return None

    async def search_stores(
        self,
        query: str,
        limit: int = 10,
        authorized_only: bool = True
    ) -> List[OntarioCRSA]:
        """
        Search for stores by name or address

        Args:
            query: Search term (store name or address)
            limit: Maximum number of results
            authorized_only: Only return authorized stores

        Returns:
            List of matching CRSA records
        """
        try:
            if not query or len(query.strip()) < 2:
                return []

            return await self.crsa_repo.search_stores(
                query=query.strip(),
                limit=limit,
                authorized_only=authorized_only
            )

        except Exception as e:
            logger.error(f"Error searching stores: {e}")
            return []

    async def list_available_stores(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> List[OntarioCRSA]:
        """
        List stores available for tenant signup

        Returns:
            List of authorized stores not yet linked to tenants
        """
        try:
            return await self.crsa_repo.list_available_for_signup(
                limit=limit,
                offset=offset
            )
        except Exception as e:
            logger.error(f"Error listing available stores: {e}")
            return []

    async def list_by_municipality(
        self,
        municipality: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[OntarioCRSA]:
        """
        List stores in a specific municipality

        Args:
            municipality: Municipality name
            limit: Maximum number of results
            offset: Pagination offset

        Returns:
            List of CRSA records in the municipality
        """
        try:
            return await self.crsa_repo.list_by_municipality(
                municipality=municipality,
                limit=limit,
                offset=offset
            )
        except Exception as e:
            logger.error(f"Error listing stores in {municipality}: {e}")
            return []

    async def link_to_tenant(
        self,
        license_number: str,
        tenant_id: UUID
    ) -> OntarioCRSA:
        """
        Link a CRSA record to a tenant during signup

        Args:
            license_number: License number to link
            tenant_id: Tenant ID to link to

        Returns:
            Updated CRSA record

        Raises:
            ValueError: If license is invalid or already linked
        """
        try:
            # Validate first
            validation = await self.validate_license(license_number)

            if not validation.is_valid:
                raise ValueError(validation.error_message or "License validation failed")

            # Link to tenant
            updated_record = await self.crsa_repo.mark_linked(license_number, tenant_id)

            logger.info(f"Linked license '{license_number}' to tenant {tenant_id}")
            return updated_record

        except Exception as e:
            logger.error(f"Error linking license {license_number} to tenant {tenant_id}: {e}")
            raise

    async def unlink_from_tenant(
        self,
        license_number: str,
        tenant_id: UUID
    ) -> OntarioCRSA:
        """
        Unlink a CRSA record from a tenant

        Args:
            license_number: License number to unlink
            tenant_id: Expected tenant ID (for verification)

        Returns:
            Updated CRSA record

        Raises:
            ValueError: If license is not found or not linked to expected tenant
        """
        try:
            # Get current record
            record = await self.crsa_repo.get_by_license(license_number)

            if not record:
                raise ValueError(f"License '{license_number}' not found")

            # Verify it's linked to the expected tenant
            if record.linked_tenant_id != tenant_id:
                raise ValueError(
                    f"License '{license_number}' is not linked to tenant {tenant_id}"
                )

            # Unlink
            updated_record = await self.crsa_repo.mark_unlinked(license_number)

            logger.info(f"Unlinked license '{license_number}' from tenant {tenant_id}")
            return updated_record

        except Exception as e:
            logger.error(f"Error unlinking license {license_number}: {e}")
            raise

    async def verify_license(
        self,
        license_number: str,
        verified_by_user_id: UUID
    ) -> OntarioCRSA:
        """
        Manually verify a license (admin action)

        Args:
            license_number: License number to verify
            verified_by_user_id: Admin user ID performing verification

        Returns:
            Updated CRSA record

        Raises:
            ValueError: If license is not found
        """
        try:
            # Check if exists
            record = await self.crsa_repo.get_by_license(license_number)

            if not record:
                raise ValueError(f"License '{license_number}' not found")

            # Mark as verified
            updated_record = await self.crsa_repo.verify_license(
                license_number,
                verified_by_user_id
            )

            logger.info(f"License '{license_number}' verified by user {verified_by_user_id}")
            return updated_record

        except Exception as e:
            logger.error(f"Error verifying license {license_number}: {e}")
            raise

    async def get_statistics(self) -> Dict[str, Any]:
        """
        Get CRSA database statistics

        Returns:
            Dictionary with counts and statistics
        """
        try:
            return await self.crsa_repo.get_statistics()
        except Exception as e:
            logger.error(f"Error getting CRSA statistics: {e}")
            return {
                'error': 'Failed to retrieve statistics',
                'total_stores': 0,
                'authorized_count': 0,
                'available_for_signup': 0
            }

    async def auto_fill_tenant_info(
        self,
        license_number: str
    ) -> Optional[Dict[str, Any]]:
        """
        Auto-fill tenant information from CRSA record

        Args:
            license_number: License number to lookup

        Returns:
            Dictionary with auto-fill data for tenant signup form, or None if not found
        """
        try:
            # Validate and get record
            validation = await self.validate_license(license_number)

            if not validation.is_valid or not validation.crsa_record:
                return None

            crsa = validation.crsa_record

            # Extract auto-fill data
            auto_fill_data = {
                'store_name': crsa.store_name,
                'address': crsa.address,
                'municipality': crsa.municipality or crsa.first_nation,
                'website': crsa.website,
                'license_number': crsa.license_number,
                'license_status': crsa.store_application_status,
                'crsa_id': str(crsa.id)
            }

            logger.info(f"Generated auto-fill data for license '{license_number}'")
            return auto_fill_data

        except Exception as e:
            logger.error(f"Error generating auto-fill data for license {license_number}: {e}")
            return None

    async def check_license_availability(self, license_number: str) -> bool:
        """
        Quick check if a license is available for signup

        Args:
            license_number: License number to check

        Returns:
            True if available, False otherwise
        """
        try:
            record = await self.crsa_repo.get_by_license(license_number)

            if not record:
                return False

            return record.is_available_for_signup()

        except Exception as e:
            logger.error(f"Error checking license availability: {e}")
            return False
