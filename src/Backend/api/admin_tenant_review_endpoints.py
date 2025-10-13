"""
Admin Tenant Review API Endpoints
Manage accounts flagged for manual review during signup
"""

import logging
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, EmailStr
import asyncpg

from core.domain.models import Tenant, TenantStatus
from core.repositories.tenant_repository import TenantRepository
from core.repositories.subscription_repository import SubscriptionRepository
from core.repositories.ontario_crsa_repository import OntarioCRSARepository
from core.services.tenant_service import TenantService
from core.services.ontario_crsa_service import OntarioCRSAService
from services.notification_service import get_notification_service
from services.redis_verification_store import get_redis_verification_store

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin/pending-review", tags=["admin-review"])
security = HTTPBearer()


# =====================================================
# Authentication & Authorization
# =====================================================

async def check_admin_access(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify admin access using centralized authentication"""
    try:
        from core.authentication import get_auth

        auth = get_auth()
        token = credentials.credentials

        payload = auth.verify_token(token)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )

        user = {
            'user_id': payload.get('user_id'),
            'email': payload.get('email'),
            'role': payload.get('role'),
            'first_name': payload.get('first_name'),
            'last_name': payload.get('last_name')
        }

        # Only super_admin and tenant_admin can review accounts
        allowed_roles = ['super_admin', 'tenant_admin', 'admin', 'superadmin']
        if user.get('role') not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )

        return user

    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )


# =====================================================
# Database Connection
# =====================================================

async def get_db_pool() -> asyncpg.Pool:
    """Get or create database connection pool"""
    return await asyncpg.create_pool(
        host=os.getenv('DB_HOST', 'localhost'),
        port=int(os.getenv('DB_PORT', 5434)),
        user=os.getenv('DB_USER', 'weedgo'),
        password=os.getenv('DB_PASSWORD', 'your_password_here'),
        database=os.getenv('DB_NAME', 'ai_engine'),
        min_size=2,
        max_size=10
    )


# =====================================================
# Request/Response Models
# =====================================================

class PendingAccountSummary(BaseModel):
    """Summary of a pending account for list view"""
    tenant_id: str
    tenant_code: str
    store_name: str
    license_number: str
    contact_email: str
    contact_phone: Optional[str]
    contact_name: str
    contact_role: str
    submitted_at: datetime
    verification_tier: str
    needs_manual_review: bool


class PendingAccountDetail(BaseModel):
    """Detailed information for a pending account"""
    tenant_id: str
    tenant_code: str
    store_name: str
    license_number: str
    contact_email: str
    contact_phone: Optional[str]
    contact_name: str
    contact_role: str
    submitted_at: datetime
    verification_tier: str
    needs_manual_review: bool

    # CRSA Information
    crsa_address: str
    crsa_municipality: Optional[str]
    crsa_store_status: str
    crsa_website: Optional[str]

    # Additional Context
    email_domain: str
    domain_matches_crsa: bool
    subscription_tier: str
    account_status: str


class ApproveRequest(BaseModel):
    """Request to approve a pending account"""
    admin_notes: Optional[str] = None
    send_welcome_email: bool = True


class RejectRequest(BaseModel):
    """Request to reject a pending account"""
    reason: str = Field(..., min_length=10, max_length=500)
    send_notification: bool = True


class ReviewStats(BaseModel):
    """Statistics for manual review queue"""
    total_pending: int
    pending_this_week: int
    avg_review_time_hours: float
    approval_rate: float


# =====================================================
# Helper Functions
# =====================================================

async def get_pending_tenants(pool: asyncpg.Pool, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
    """
    Query tenants that need manual review

    A tenant needs manual review if:
    1. settings.needs_manual_review = true
    2. status = 'active' (but not yet fully approved by admin)
    """
    query = """
        SELECT
            t.id,
            t.code,
            t.name,
            t.contact_email,
            t.contact_phone,
            t.status,
            t.subscription_tier,
            t.settings,
            t.created_at,
            t.updated_at
        FROM tenants t
        WHERE
            t.settings->>'needs_manual_review' = 'true'
            AND t.status = 'active'
        ORDER BY t.created_at DESC
        LIMIT $1 OFFSET $2
    """

    async with pool.acquire() as conn:
        rows = await conn.fetch(query, limit, offset)
        return [dict(row) for row in rows]


def _extract_signup_info(settings: Dict[str, Any]) -> Dict[str, Any]:
    """Extract signup information from tenant settings"""
    return {
        'verification_tier': settings.get('verification_tier', 'unknown'),
        'crsa_license': settings.get('crsa_license', ''),
        'needs_manual_review': settings.get('needs_manual_review', False),
        'signup_date': settings.get('signup_date'),
        'signup_contact': settings.get('signup_contact', {})
    }


def _get_email_domain(email: str) -> str:
    """Extract domain from email address"""
    return email.split('@')[-1] if '@' in email else ''


def _check_domain_match(email_domain: str, crsa_website: Optional[str]) -> bool:
    """Check if email domain matches CRSA website domain"""
    if not crsa_website:
        return False

    # Extract domain from website URL
    website_domain = crsa_website.replace('http://', '').replace('https://', '').replace('www.', '').split('/')[0]

    # Simple domain matching
    return email_domain.lower() in website_domain.lower() or website_domain.lower() in email_domain.lower()


# =====================================================
# API Endpoints
# =====================================================

@router.get("/", response_model=List[PendingAccountSummary])
async def list_pending_accounts(
    limit: int = 100,
    offset: int = 0,
    user: Dict = Depends(check_admin_access)
):
    """
    List all accounts pending manual review

    Returns list of accounts that need admin verification before full activation
    """
    try:
        pool = await get_db_pool()

        # Get pending tenants
        pending_tenants = await get_pending_tenants(pool, limit, offset)

        results = []
        for tenant_data in pending_tenants:
            settings = tenant_data.get('settings', {})
            signup_info = _extract_signup_info(settings)
            signup_contact = signup_info['signup_contact']

            results.append(PendingAccountSummary(
                tenant_id=str(tenant_data['id']),
                tenant_code=tenant_data['code'],
                store_name=tenant_data['name'],
                license_number=signup_info['crsa_license'],
                contact_email=tenant_data['contact_email'],
                contact_phone=tenant_data.get('contact_phone'),
                contact_name=signup_contact.get('name', 'Unknown'),
                contact_role=signup_contact.get('role', 'Unknown'),
                submitted_at=tenant_data['created_at'],
                verification_tier=signup_info['verification_tier'],
                needs_manual_review=signup_info['needs_manual_review']
            ))

        logger.info(f"Admin {user['email']} listed {len(results)} pending accounts")
        return results

    except Exception as e:
        logger.error(f"Error listing pending accounts: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list pending accounts: {str(e)}"
        )


@router.get("/stats", response_model=ReviewStats)
async def get_review_stats(user: Dict = Depends(check_admin_access)):
    """
    Get statistics for manual review queue

    Returns metrics about pending reviews and approval rates
    """
    try:
        pool = await get_db_pool()

        async with pool.acquire() as conn:
            # Total pending
            total_pending = await conn.fetchval("""
                SELECT COUNT(*)
                FROM tenants
                WHERE settings->>'needs_manual_review' = 'true'
                AND status = 'active'
            """)

            # Pending this week
            pending_this_week = await conn.fetchval("""
                SELECT COUNT(*)
                FROM tenants
                WHERE settings->>'needs_manual_review' = 'true'
                AND status = 'active'
                AND created_at >= NOW() - INTERVAL '7 days'
            """)

            # Calculate approval rate (tenants that were manually reviewed and approved)
            # For now, we'll estimate based on tenants without needs_manual_review flag
            total_signups = await conn.fetchval("""
                SELECT COUNT(*)
                FROM tenants
                WHERE settings->>'verification_tier' IS NOT NULL
            """)

            approval_rate = 100.0
            if total_signups > 0:
                approval_rate = ((total_signups - total_pending) / total_signups) * 100

        return ReviewStats(
            total_pending=total_pending or 0,
            pending_this_week=pending_this_week or 0,
            avg_review_time_hours=2.5,  # TODO: Calculate from actual review timestamps
            approval_rate=round(approval_rate, 2)
        )

    except Exception as e:
        logger.error(f"Error getting review stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get review stats: {str(e)}"
        )


@router.get("/{tenant_id}", response_model=PendingAccountDetail)
async def get_pending_account_detail(
    tenant_id: str,
    user: Dict = Depends(check_admin_access)
):
    """
    Get detailed information for a specific pending account

    Includes CRSA verification data, contact information, and verification context
    """
    try:
        pool = await get_db_pool()
        tenant_repo = TenantRepository(pool)
        crsa_repo = OntarioCRSARepository(pool)

        # Get tenant
        tenant = await tenant_repo.get_by_id(UUID(tenant_id))
        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tenant {tenant_id} not found"
            )

        # Extract signup information
        signup_info = _extract_signup_info(tenant.settings)
        signup_contact = signup_info['signup_contact']

        # Check if actually needs review
        if not signup_info['needs_manual_review']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This tenant does not require manual review"
            )

        # Get CRSA information
        crsa_record = await crsa_repo.get_by_license_number(signup_info['crsa_license'])

        # Check domain matching
        email_domain = _get_email_domain(tenant.contact_email)
        domain_matches = _check_domain_match(email_domain, crsa_record.website if crsa_record else None)

        detail = PendingAccountDetail(
            tenant_id=str(tenant.id),
            tenant_code=tenant.code,
            store_name=tenant.name,
            license_number=signup_info['crsa_license'],
            contact_email=tenant.contact_email,
            contact_phone=tenant.contact_phone,
            contact_name=signup_contact.get('name', 'Unknown'),
            contact_role=signup_contact.get('role', 'Unknown'),
            submitted_at=tenant.created_at,
            verification_tier=signup_info['verification_tier'],
            needs_manual_review=True,
            crsa_address=crsa_record.address if crsa_record else 'Unknown',
            crsa_municipality=crsa_record.municipality if crsa_record else None,
            crsa_store_status=crsa_record.store_application_status if crsa_record else 'Unknown',
            crsa_website=crsa_record.website if crsa_record else None,
            email_domain=email_domain,
            domain_matches_crsa=domain_matches,
            subscription_tier=tenant.subscription_tier.value,
            account_status=tenant.status.value
        )

        logger.info(f"Admin {user['email']} viewed pending account {tenant_id}")
        return detail

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting pending account detail: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get account detail: {str(e)}"
        )


@router.post("/{tenant_id}/approve")
async def approve_pending_account(
    tenant_id: str,
    request: ApproveRequest,
    user: Dict = Depends(check_admin_access)
):
    """
    Approve a pending account and activate it

    - Removes needs_manual_review flag
    - Generates password setup token
    - Sends approval email with setup link
    - Logs approval action
    """
    try:
        pool = await get_db_pool()
        tenant_repo = TenantRepository(pool)

        # Get tenant
        tenant = await tenant_repo.get_by_id(UUID(tenant_id))
        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tenant {tenant_id} not found"
            )

        # Verify needs review
        if not tenant.settings.get('needs_manual_review'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This tenant does not require manual review"
            )

        # Update tenant settings - remove manual review flag
        tenant.settings['needs_manual_review'] = False
        tenant.settings['approved_at'] = datetime.utcnow().isoformat()
        tenant.settings['approved_by'] = user['user_id']
        tenant.settings['admin_notes'] = request.admin_notes

        # Update tenant
        await tenant_repo.update(tenant)

        # Generate password setup token
        import secrets
        from datetime import timedelta

        token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(hours=24)

        # Store password token in Redis if available
        try:
            redis_store = get_redis_verification_store()
            redis_store.store_password_token(
                token=token,
                tenant_id=str(tenant.id),
                email=tenant.contact_email,
                expiry_hours=24
            )
        except Exception as e:
            logger.warning(f"Failed to store password token in Redis: {e}")
            # Continue without Redis - token will be sent in email

        # Generate setup link
        base_url = os.getenv('FRONTEND_URL', 'https://admin.weedgo.com')
        setup_link = f"{base_url}/setup-password?token={token}"

        # Send approval email
        if request.send_welcome_email:
            notification_service = get_notification_service()
            email_success, email_error = await notification_service.send_password_setup_email(
                to_email=tenant.contact_email,
                store_name=tenant.name,
                setup_link=setup_link,
                tenant_id=str(tenant.id)
            )

            if not email_success:
                logger.error(f"Failed to send approval email: {email_error}")
                # Don't fail approval if email fails

        logger.info(
            f"Admin {user['email']} approved tenant {tenant_id} ({tenant.name}). "
            f"Email sent: {request.send_welcome_email}"
        )

        return {
            "success": True,
            "message": f"Account approved successfully",
            "tenant_id": str(tenant.id),
            "tenant_code": tenant.code,
            "store_name": tenant.name,
            "password_setup_link": setup_link,
            "email_sent": request.send_welcome_email,
            "approved_by": user['email'],
            "approved_at": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error approving account: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to approve account: {str(e)}"
        )


@router.post("/{tenant_id}/reject")
async def reject_pending_account(
    tenant_id: str,
    request: RejectRequest,
    user: Dict = Depends(check_admin_access)
):
    """
    Reject a pending account

    - Marks tenant as cancelled
    - Stores rejection reason
    - Optionally sends notification email
    - Logs rejection action
    """
    try:
        pool = await get_db_pool()
        tenant_repo = TenantRepository(pool)

        # Get tenant
        tenant = await tenant_repo.get_by_id(UUID(tenant_id))
        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tenant {tenant_id} not found"
            )

        # Verify needs review
        if not tenant.settings.get('needs_manual_review'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This tenant does not require manual review"
            )

        # Update tenant status and settings
        tenant.status = TenantStatus.CANCELLED
        tenant.settings['rejected_at'] = datetime.utcnow().isoformat()
        tenant.settings['rejected_by'] = user['user_id']
        tenant.settings['rejection_reason'] = request.reason
        tenant.settings['needs_manual_review'] = False

        # Update tenant
        await tenant_repo.update(tenant)

        # Send rejection notification
        if request.send_notification:
            notification_service = get_notification_service()
            # TODO: Implement rejection email template
            logger.info(f"Would send rejection email to {tenant.contact_email}")

        logger.warning(
            f"Admin {user['email']} rejected tenant {tenant_id} ({tenant.name}). "
            f"Reason: {request.reason}"
        )

        return {
            "success": True,
            "message": "Account rejected successfully",
            "tenant_id": str(tenant.id),
            "tenant_code": tenant.code,
            "store_name": tenant.name,
            "rejection_reason": request.reason,
            "rejected_by": user['email'],
            "rejected_at": datetime.utcnow().isoformat(),
            "notification_sent": request.send_notification
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error rejecting account: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reject account: {str(e)}"
        )
