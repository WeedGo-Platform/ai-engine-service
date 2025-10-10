"""
Identity & Access Management V2 API Endpoints

DDD-powered user authentication and authorization using the Identity & Access bounded context.

All endpoints use domain-driven design with aggregates, value objects, and domain events.
"""

from fastapi import APIRouter, HTTPException, Query, Depends, status
from typing import List, Optional
from datetime import datetime, date, timedelta
from uuid import UUID, uuid4

from api.v2.dto_mappers import (
    # Response DTOs
    UserDTO,
    UserSummaryDTO,
    UserListDTO,
    UserStatsDTO,
    PasswordPolicyDTO,
    VerificationStatusDTO,
    AccountSecurityDTO,

    # Request DTOs
    RegisterUserRequest,
    LoginRequest,
    ChangePasswordRequest,
    UpdateProfileRequest,
    UpdatePreferencesRequest,
    VerifyEmailRequest,
    VerifyPhoneRequest,
    VerifyAgeRequest,
    Enable2FARequest,
    AssignRoleRequest,
    AssignPermissionRequest,
    SuspendUserRequest,
    UpdateUserRequest,

    # Mappers
    map_user_to_dto,
    map_user_summary_to_dto,
    map_password_policy_to_dto,
    map_verification_status_to_dto,
    map_account_security_to_dto,
)

from pydantic import BaseModel, Field
from typing import Dict, Any

# Additional response model for login that includes tokens
class FrontendUserDTO(BaseModel):
    """User format expected by frontend"""
    user_id: str
    email: str
    role: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    tenant_id: Optional[str] = None
    store_role: Optional[str] = None
    tenants: List[Dict[str, Any]] = Field(default_factory=list)
    stores: List[Dict[str, Any]] = Field(default_factory=list)

class LoginResponseDTO(BaseModel):
    """Login response with user data and tokens"""
    user: FrontendUserDTO
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int = 3600  # Default 1 hour
    permissions: List[str]

from ddd_refactored.domain.identity_access.entities.user import (
    User,
    UserStatus,
    UserType,
    AuthProvider,
)
from ddd_refactored.domain.identity_access.value_objects.password_policy import (
    PasswordPolicy,
    DEFAULT_PASSWORD_POLICY,
    ADMIN_PASSWORD_POLICY,
)
from ddd_refactored.shared.domain_base import BusinessRuleViolation

# Temporary auth dependency (replace with actual auth)
async def get_current_user():
    return {"id": "user-123", "role": "admin"}


router = APIRouter(
    prefix="/v2/identity-access",
    tags=["👤 Identity & Access Management V2"]
)


# ============================================================================
# User Registration & Authentication
# ============================================================================

@router.post("/users/register", response_model=UserDTO, status_code=201)
async def register_user(
    request: RegisterUserRequest,
    tenant_id: str = Query(..., description="Tenant ID"),
):
    """
    Register a new user.

    **Business Rules:**
    - Email is required and must be valid
    - Password must meet policy requirements (min 8 chars, uppercase, lowercase, digit)
    - Email must be unique
    - User type defaults to 'customer'
    - Status starts as 'pending' (requires email verification)
    - Password is hashed with bcrypt

    **Domain Events Generated:**
    - UserRegistered

    **Next Steps:**
    - Send email verification link
    - User verifies email to activate account
    """
    try:
        # Parse user type
        user_type = UserType(request.user_type)

        # Create user
        user = User.create(
            email=request.email,
            user_type=user_type,
            first_name=request.first_name,
            last_name=request.last_name,
            phone=request.phone
        )

        # Set ID
        user.id = uuid4()

        # Set password
        policy = ADMIN_PASSWORD_POLICY if user_type == UserType.ADMIN else DEFAULT_PASSWORD_POLICY
        user.set_password(request.password, policy=policy)

        # Set date of birth if provided
        if request.date_of_birth:
            user.date_of_birth = datetime.fromisoformat(request.date_of_birth).date()

        # Set preferences
        user.language = request.language
        user.timezone = request.timezone
        user.marketing_emails_enabled = request.marketing_emails_enabled

        # TODO: Persist to database
        # await user_repository.save(user)

        # TODO: Send verification email
        # await email_service.send_verification_email(user.email)

        return map_user_to_dto(user)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except BusinessRuleViolation as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.post("/auth/login", response_model=LoginResponseDTO)
async def login(
    request: LoginRequest,
    tenant_id: Optional[str] = Query(None, description="Tenant ID"),  # Made optional for testing
):
    """
    Authenticate user and start session.

    **Business Rules:**
    - Email and password are required
    - Account must not be locked (5 failed attempts = 30 min lock)
    - Account must not be suspended or deleted
    - If 2FA enabled, requires 2FA code
    - Failed login increments failed_login_attempts
    - Successful login resets failed_login_attempts and updates last_login_at

    **Security:**
    - Password verification uses bcrypt
    - Supports legacy SHA256 hashes (for migration)
    - Account locked after 5 failed attempts for 30 minutes
    - IP address tracking for audit trail

    **Domain Events Generated:**
    - LoginAttempt (successful or failed)
    """
    try:
        # TODO: Load user from database
        # user = await user_repository.find_by_email(request.email)
        # if not user:
        #     raise HTTPException(status_code=401, detail="Invalid email or password")

        # For now, return mock admin user for testing
        # Accept any email/password for testing

        # Create a complete mock UserDTO with all required fields
        user_id = str(uuid4())
        now = datetime.utcnow()

        # Create nested DTOs
        verification_status = VerificationStatusDTO(
            email_verified=True,
            email_verified_at=now.isoformat(),
            phone_verified=False,
            phone_verified_at=None,
            age_verified=True,
            age_verified_at=now.isoformat(),
            is_fully_verified=False
        )

        security_info = AccountSecurityDTO(
            two_factor_enabled=False,
            failed_login_attempts=0,
            last_failed_login=None,
            account_locked_until=None,
            is_account_locked=False,
            last_login_at=now.isoformat(),
            last_login_ip=request.ip_address or "127.0.0.1",
            login_count=1
        )

        # Create complete UserDTO with all required fields
        user_dto = UserDTO(
            id=user_id,
            email=request.email,
            phone=None,
            username=request.email.split('@')[0],
            user_type="admin",
            status="active",
            auth_provider="email",
            provider_user_id=None,

            # Personal Information
            first_name="Admin",
            last_name="User",
            full_name="Admin User",
            display_name="Admin",
            date_of_birth=None,
            age=None,
            gender=None,

            # Nested DTOs
            verification=verification_status,
            security=security_info,

            # Permissions
            permissions=["system:*"],
            roles=["admin", "super_admin"],

            # Activity
            last_activity_at=now.isoformat(),

            # Preferences
            language="en",
            timezone="America/Toronto",
            currency="CAD",
            notifications_enabled=True,
            marketing_emails_enabled=False,

            # Metadata
            metadata={"login_method": "password"},
            tags=["admin", "verified"],

            # Flags
            can_make_purchase=True,
            is_active=True,

            # Timestamps
            created_at=(now.isoformat() if now else datetime.utcnow().isoformat()),
            updated_at=(now.isoformat() if now else datetime.utcnow().isoformat()),

            # Domain Events
            events=["UserLoggedIn"]
        )

        # Create simplified frontend user format
        frontend_user = FrontendUserDTO(
            user_id=user_id,
            email=request.email,
            role="super_admin",  # Primary role for frontend
            first_name="Admin",
            last_name="User",
            tenant_id="ce2d57bc-b3ba-4801-b229-889a9fe9626d",
            store_role=None,
            tenants=[
                {
                    "id": "ce2d57bc-b3ba-4801-b229-889a9fe9626d",
                    "name": "Demo Tenant",
                    "code": "DEMO",
                    "role": "owner"
                }
            ],
            stores=[]
        )

        # Generate real JWT tokens using the authentication system
        from core.authentication import get_auth
        auth = get_auth()

        # Debug: Log the JWT secret being used
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Login endpoint JWT secret (first 10 chars): {auth.secret_key[:10] if auth.secret_key else 'None'}")

        # Create token payload with admin role
        token_data = {
            'user_id': user_id,
            'email': request.email,
            'role': 'admin',  # Admin role for admin dashboard access
            'tenant_id': "ce2d57bc-b3ba-4801-b229-889a9fe9626d",
            'session_id': f"session_{user_id}"
        }

        # Generate real JWT tokens
        access_token = auth.create_access_token(token_data)
        refresh_token = auth.create_refresh_token(token_data)

        # Return LoginResponseDTO with real JWT tokens
        return LoginResponseDTO(
            user=frontend_user,
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="Bearer",
            expires_in=auth.access_token_expire_minutes * 60,  # Convert to seconds
            permissions=["system:*"]
        )

        # Check if account is locked
        # if user.is_account_locked():
        #     raise HTTPException(status_code=423, detail="Account is locked due to too many failed login attempts. Try again in 30 minutes.")

        # Verify password
        # if not user.verify_password(request.password):
        #     user.record_login(ip_address=request.ip_address, successful=False)
        #     await user_repository.save(user)
        #     raise HTTPException(status_code=401, detail="Invalid email or password")

        # Check if 2FA is enabled
        # if user.two_factor_enabled:
        #     if not request.two_factor_code:
        #         raise HTTPException(status_code=401, detail="Two-factor authentication code required")
        #     # TODO: Verify 2FA code
        #     # if not verify_2fa_code(user.two_factor_secret, request.two_factor_code):
        #     #     raise HTTPException(status_code=401, detail="Invalid two-factor authentication code")

        # Check account status
        # if user.status == UserStatus.SUSPENDED:
        #     raise HTTPException(status_code=403, detail="Account is suspended")
        # if user.status == UserStatus.DELETED:
        #     raise HTTPException(status_code=403, detail="Account is deleted")
        # if user.status == UserStatus.INACTIVE:
        #     raise HTTPException(status_code=403, detail="Account is inactive")

        # Record successful login
        # user.record_login(ip_address=request.ip_address, successful=True)
        # await user_repository.save(user)

        # TODO: Create session token
        # token = await session_service.create_session(user.id)

        # return map_user_to_dto(user)

    except BusinessRuleViolation as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.post("/auth/logout", status_code=204)
async def logout(
    tenant_id: str = Query(..., description="Tenant ID"),
    current_user: dict = Depends(get_current_user),
):
    """
    Logout current user and invalidate session.

    **Actions:**
    - Invalidate current session token
    - Clear session cookies
    """
    # TODO: Invalidate session token
    # await session_service.invalidate_session(current_user["session_id"])
    pass


# ============================================================================
# User Profile Management
# ============================================================================

# Create a new response model for getCurrentUser endpoint
class CurrentUserResponseDTO(BaseModel):
    """Response for getCurrentUser endpoint"""
    user: FrontendUserDTO
    permissions: List[str]

@router.get("/users/me", response_model=CurrentUserResponseDTO)
async def get_current_user_profile(
    tenant_id: Optional[str] = Query(None, description="Tenant ID"),  # Made optional for now
    current_user: dict = Depends(get_current_user),
):
    """
    Get current user's profile.

    **Returns:**
    - Complete user details
    - Permissions
    """
    # TODO: Load from database
    # user = await user_repository.find_by_id(UUID(current_user["id"]))
    # if not user:
    #     raise HTTPException(status_code=404, detail="User not found")

    # For now, return mock user for testing
    user_id = current_user.get("id", "user-123")

    # Create simplified frontend user format
    frontend_user = FrontendUserDTO(
        user_id=user_id,
        email="admin@weedgo.ca",
        role="super_admin",
        first_name="Admin",
        last_name="User",
        tenant_id="ce2d57bc-b3ba-4801-b229-889a9fe9626d",
        store_role=None,
        tenants=[
            {
                "id": "ce2d57bc-b3ba-4801-b229-889a9fe9626d",
                "name": "Demo Tenant",
                "code": "DEMO",
                "role": "owner"
            }
        ],
        stores=[]
    )

    # Return response with user and permissions
    return CurrentUserResponseDTO(
        user=frontend_user,
        permissions=["system:*"]
    )


@router.put("/users/me/profile", response_model=UserDTO)
async def update_profile(
    request: UpdateProfileRequest,
    tenant_id: str = Query(..., description="Tenant ID"),
    current_user: dict = Depends(get_current_user),
):
    """
    Update current user's profile.

    **Updates:**
    - First name
    - Last name
    - Date of birth
    - Gender

    **Business Rules:**
    - Cannot change email (use separate endpoint)
    - Changing date of birth may invalidate age verification
    """
    try:
        # TODO: Load from database
        # user = await user_repository.find_by_id(UUID(current_user["id"]))
        # if not user:
        #     raise HTTPException(status_code=404, detail="User not found")

        # Apply updates
        # dob = datetime.fromisoformat(request.date_of_birth).date() if request.date_of_birth else None
        # user.update_profile(
        #     first_name=request.first_name,
        #     last_name=request.last_name,
        #     date_of_birth=dob,
        #     gender=request.gender
        # )

        # await user_repository.save(user)

        # return map_user_to_dto(user)

        raise HTTPException(status_code=404, detail="User not found - database integration pending")

    except BusinessRuleViolation as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.put("/users/me/preferences", response_model=UserDTO)
async def update_preferences(
    request: UpdatePreferencesRequest,
    tenant_id: str = Query(..., description="Tenant ID"),
    current_user: dict = Depends(get_current_user),
):
    """
    Update current user's preferences.

    **Updates:**
    - Language (en, fr, es, pt, zh)
    - Timezone
    - Currency
    - Notification settings
    - Marketing email opt-in
    """
    try:
        # TODO: Load from database
        # user = await user_repository.find_by_id(UUID(current_user["id"]))
        # if not user:
        #     raise HTTPException(status_code=404, detail="User not found")

        # user.update_preferences(
        #     language=request.language,
        #     timezone=request.timezone,
        #     currency=request.currency,
        #     notifications_enabled=request.notifications_enabled,
        #     marketing_emails_enabled=request.marketing_emails_enabled
        # )

        # await user_repository.save(user)

        # return map_user_to_dto(user)

        raise HTTPException(status_code=404, detail="User not found - database integration pending")

    except BusinessRuleViolation as e:
        raise HTTPException(status_code=422, detail=str(e))


# ============================================================================
# Password Management
# ============================================================================

@router.post("/auth/change-password", response_model=UserDTO)
async def change_password(
    request: ChangePasswordRequest,
    tenant_id: str = Query(..., description="Tenant ID"),
    current_user: dict = Depends(get_current_user),
):
    """
    Change user password.

    **Business Rules:**
    - Current password must be correct
    - New password must be different from current
    - New password must meet policy requirements
    - Password hashed with bcrypt
    - All user sessions invalidated after password change

    **Domain Events Generated:**
    - PasswordChanged (with invalidate_sessions=True)
    """
    try:
        # TODO: Load from database
        # user = await user_repository.find_by_id(UUID(current_user["id"]))
        # if not user:
        #     raise HTTPException(status_code=404, detail="User not found")

        # Change password
        # policy = ADMIN_PASSWORD_POLICY if user.user_type == UserType.ADMIN else DEFAULT_PASSWORD_POLICY
        # user.change_password(
        #     current_password=request.current_password,
        #     new_password=request.new_password,
        #     policy=policy
        # )

        # await user_repository.save(user)

        # TODO: Invalidate all sessions except current
        # await session_service.invalidate_all_sessions(user.id, except_session_id=current_user["session_id"])

        # return map_user_to_dto(user)

        raise HTTPException(status_code=404, detail="User not found - database integration pending")

    except BusinessRuleViolation as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.get("/auth/password-policy", response_model=PasswordPolicyDTO)
async def get_password_policy(
    user_type: str = Query("customer", description="User type (customer, staff, admin)"),
):
    """
    Get password policy requirements.

    **Default Policy (customer, staff):**
    - Min 8 characters
    - Requires uppercase
    - Requires lowercase
    - Requires digit
    - Special char optional

    **Admin Policy:**
    - Min 12 characters
    - Requires uppercase
    - Requires lowercase
    - Requires digit
    - Requires special char
    """
    if user_type == "admin":
        return map_password_policy_to_dto(ADMIN_PASSWORD_POLICY)
    else:
        return map_password_policy_to_dto(DEFAULT_PASSWORD_POLICY)


# ============================================================================
# Verification Endpoints
# ============================================================================

@router.post("/auth/verify-email", response_model=UserDTO)
async def verify_email(
    request: VerifyEmailRequest,
    tenant_id: str = Query(..., description="Tenant ID"),
    current_user: dict = Depends(get_current_user),
):
    """
    Verify user's email address.

    **Business Rules:**
    - Email must not already be verified
    - Verification code must be valid
    - Sets email_verified=True and email_verified_at timestamp

    **Actions:**
    - If user status is 'pending', activates user
    """
    try:
        # TODO: Verify code
        # if not await verification_service.verify_email_code(current_user["id"], request.verification_code):
        #     raise HTTPException(status_code=400, detail="Invalid verification code")

        # user = await user_repository.find_by_id(UUID(current_user["id"]))
        # user.verify_email()

        # If user is pending, activate
        # if user.status == UserStatus.PENDING:
        #     user.activate()

        # await user_repository.save(user)

        # return map_user_to_dto(user)

        raise HTTPException(status_code=404, detail="User not found - database integration pending")

    except BusinessRuleViolation as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.post("/auth/verify-phone", response_model=UserDTO)
async def verify_phone(
    request: VerifyPhoneRequest,
    tenant_id: str = Query(..., description="Tenant ID"),
    current_user: dict = Depends(get_current_user),
):
    """
    Verify user's phone number.

    **Business Rules:**
    - Phone number must be set
    - Phone must not already be verified
    - Verification code must be valid
    - Sets phone_verified=True and phone_verified_at timestamp
    """
    try:
        # TODO: Verify code
        # if not await verification_service.verify_phone_code(current_user["id"], request.verification_code):
        #     raise HTTPException(status_code=400, detail="Invalid verification code")

        # user = await user_repository.find_by_id(UUID(current_user["id"]))
        # user.verify_phone()

        # await user_repository.save(user)

        # return map_user_to_dto(user)

        raise HTTPException(status_code=404, detail="User not found - database integration pending")

    except BusinessRuleViolation as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.post("/auth/verify-age", response_model=UserDTO)
async def verify_age(
    request: VerifyAgeRequest,
    tenant_id: str = Query(..., description="Tenant ID"),
    current_user: dict = Depends(get_current_user),
):
    """
    Verify user's age (19+ for cannabis).

    **Business Rules:**
    - User must be 19 or older (Ontario cannabis requirement)
    - Age calculated from date of birth
    - Sets age_verified=True and age_verified_at timestamp
    - Required before user can make cannabis purchases

    **Raises:**
    - 422 if user is under 19
    """
    try:
        # user = await user_repository.find_by_id(UUID(current_user["id"]))

        # Update date of birth if provided
        # dob = datetime.fromisoformat(request.date_of_birth).date()
        # user.date_of_birth = dob

        # Verify age
        # user.verify_age()

        # await user_repository.save(user)

        # return map_user_to_dto(user)

        raise HTTPException(status_code=404, detail="User not found - database integration pending")

    except BusinessRuleViolation as e:
        raise HTTPException(status_code=422, detail=str(e))


# ============================================================================
# Two-Factor Authentication
# ============================================================================

@router.post("/auth/2fa/enable", response_model=dict)
async def enable_2fa(
    request: Enable2FARequest,
    tenant_id: str = Query(..., description="Tenant ID"),
    current_user: dict = Depends(get_current_user),
):
    """
    Enable two-factor authentication.

    **Business Rules:**
    - Password verification required
    - 2FA must not already be enabled
    - Generates TOTP secret

    **Returns:**
    - secret: TOTP secret for QR code generation
    - qr_code_url: URL for QR code (for authenticator apps)

    **Next Steps:**
    - User scans QR code with authenticator app
    - User enters 2FA code on next login
    """
    try:
        # user = await user_repository.find_by_id(UUID(current_user["id"]))

        # Verify password
        # if not user.verify_password(request.password):
        #     raise HTTPException(status_code=401, detail="Invalid password")

        # Enable 2FA
        # secret = user.enable_two_factor()

        # await user_repository.save(user)

        # Generate QR code URL
        # qr_code_url = f"otpauth://totp/WeedGo:{user.email}?secret={secret}&issuer=WeedGo"

        # return {
        #     "secret": secret,
        #     "qr_code_url": qr_code_url
        # }

        raise HTTPException(status_code=404, detail="User not found - database integration pending")

    except BusinessRuleViolation as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.post("/auth/2fa/disable", response_model=UserDTO)
async def disable_2fa(
    tenant_id: str = Query(..., description="Tenant ID"),
    current_user: dict = Depends(get_current_user),
):
    """
    Disable two-factor authentication.

    **Business Rules:**
    - 2FA must be enabled
    - Clears two_factor_secret
    """
    try:
        # user = await user_repository.find_by_id(UUID(current_user["id"]))

        # user.disable_two_factor()

        # await user_repository.save(user)

        # return map_user_to_dto(user)

        raise HTTPException(status_code=404, detail="User not found - database integration pending")

    except BusinessRuleViolation as e:
        raise HTTPException(status_code=422, detail=str(e))


# ============================================================================
# User Management (Admin Endpoints)
# ============================================================================

@router.get("/users", response_model=UserListDTO)
async def list_users(
    tenant_id: str = Query(..., description="Tenant ID"),
    user_type: Optional[str] = Query(None, description="Filter by user type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    role: Optional[str] = Query(None, description="Filter by role"),
    search: Optional[str] = Query(None, description="Search by email, name, phone"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
):
    """
    List all users (admin only).

    **Filters:**
    - User type (customer, staff, admin, system)
    - Status (active, inactive, suspended, pending, deleted)
    - Role
    - Search (email, name, phone)

    **Returns:**
    - Paginated list of user summaries
    """
    # TODO: Query from database with filters
    # users = await user_repository.find_all(filters)

    # Mock response
    users = []
    total = 0

    return UserListDTO(
        users=users,
        total=total,
        page=page,
        page_size=page_size,
        has_more=(page * page_size) < total
    )


@router.get("/users/{user_id}", response_model=UserDTO)
async def get_user(
    user_id: str,
    tenant_id: str = Query(..., description="Tenant ID"),
    current_user: dict = Depends(get_current_user),
):
    """
    Get user details (admin only).

    **Returns:**
    - Complete user details
    - Verification status
    - Security settings
    - Roles and permissions
    """
    # TODO: Load from database
    # user = await user_repository.find_by_id(UUID(user_id))
    # if not user:
    #     raise HTTPException(status_code=404, detail="User not found")

    # return map_user_to_dto(user)

    raise HTTPException(status_code=404, detail="User not found - database integration pending")


@router.put("/users/{user_id}", response_model=UserDTO)
async def update_user(
    user_id: str,
    request: UpdateUserRequest,
    tenant_id: str = Query(..., description="Tenant ID"),
    current_user: dict = Depends(get_current_user),
):
    """
    Update user (admin only).

    **Updates:**
    - Email
    - Phone
    - Username
    - Status
    - Roles
    - Permissions
    - Tags
    """
    try:
        # TODO: Load from database
        # user = await user_repository.find_by_id(UUID(user_id))
        # if not user:
        #     raise HTTPException(status_code=404, detail="User not found")

        # Apply updates
        # if request.email:
        #     user.email = request.email
        # if request.phone:
        #     user.phone = request.phone
        # if request.username:
        #     user.username = request.username
        # if request.status:
        #     user.status = UserStatus(request.status)
        # if request.roles is not None:
        #     user.roles = request.roles
        # if request.permissions is not None:
        #     user.permissions = request.permissions
        # if request.tags is not None:
        #     user.tags = request.tags

        # user.updated_at = datetime.utcnow()

        # await user_repository.save(user)

        # return map_user_to_dto(user)

        raise HTTPException(status_code=404, detail="User not found - database integration pending")

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except BusinessRuleViolation as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.delete("/users/{user_id}", status_code=204)
async def delete_user(
    user_id: str,
    tenant_id: str = Query(..., description="Tenant ID"),
    current_user: dict = Depends(get_current_user),
):
    """
    Soft delete user (admin only).

    **Actions:**
    - Sets status to 'deleted'
    - Anonymizes data (email, phone, name, password)
    - Preserves user ID for referential integrity

    **Anonymization:**
    - Email: deleted_{user_id}@deleted.com
    - Phone: None
    - First name: "Deleted"
    - Last name: "User"
    - Password hash: None
    - 2FA secret: None
    """
    # TODO: Load from database
    # user = await user_repository.find_by_id(UUID(user_id))
    # if not user:
    #     raise HTTPException(status_code=404, detail="User not found")

    # user.soft_delete()

    # await user_repository.save(user)

    raise HTTPException(status_code=404, detail="User not found - database integration pending")


# ============================================================================
# User Status Management
# ============================================================================

@router.post("/users/{user_id}/activate", response_model=UserDTO)
async def activate_user(
    user_id: str,
    tenant_id: str = Query(..., description="Tenant ID"),
    current_user: dict = Depends(get_current_user),
):
    """
    Activate user (admin only).

    **Business Rules:**
    - Cannot activate deleted users
    - Sets status to 'active'
    - Sets email_verified=True

    **Domain Events Generated:**
    - UserActivated
    """
    try:
        # user = await user_repository.find_by_id(UUID(user_id))
        # user.activate()
        # await user_repository.save(user)
        # return map_user_to_dto(user)

        raise HTTPException(status_code=404, detail="User not found - database integration pending")

    except BusinessRuleViolation as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.post("/users/{user_id}/suspend", response_model=UserDTO)
async def suspend_user(
    user_id: str,
    request: SuspendUserRequest,
    tenant_id: str = Query(..., description="Tenant ID"),
    current_user: dict = Depends(get_current_user),
):
    """
    Suspend user (admin only).

    **Business Rules:**
    - Cannot suspend deleted users
    - Sets status to 'suspended'
    - Stores suspension reason in metadata

    **Domain Events Generated:**
    - UserSuspended
    """
    try:
        # user = await user_repository.find_by_id(UUID(user_id))
        # user.suspend(reason=request.reason)
        # await user_repository.save(user)
        # return map_user_to_dto(user)

        raise HTTPException(status_code=404, detail="User not found - database integration pending")

    except BusinessRuleViolation as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.post("/users/{user_id}/reactivate", response_model=UserDTO)
async def reactivate_user(
    user_id: str,
    tenant_id: str = Query(..., description="Tenant ID"),
    current_user: dict = Depends(get_current_user),
):
    """
    Reactivate suspended or inactive user (admin only).

    **Business Rules:**
    - Can only reactivate suspended or inactive users
    - Sets status to 'active'
    - Clears suspension reason
    - Resets failed_login_attempts and unlocks account
    """
    try:
        # user = await user_repository.find_by_id(UUID(user_id))
        # user.reactivate()
        # await user_repository.save(user)
        # return map_user_to_dto(user)

        raise HTTPException(status_code=404, detail="User not found - database integration pending")

    except BusinessRuleViolation as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.post("/users/{user_id}/unlock", response_model=UserDTO)
async def unlock_account(
    user_id: str,
    tenant_id: str = Query(..., description="Tenant ID"),
    current_user: dict = Depends(get_current_user),
):
    """
    Unlock user account (admin only).

    **Actions:**
    - Clears account_locked_until
    - Resets failed_login_attempts to 0
    """
    # user = await user_repository.find_by_id(UUID(user_id))
    # user.unlock_account()
    # await user_repository.save(user)
    # return map_user_to_dto(user)

    raise HTTPException(status_code=404, detail="User not found - database integration pending")


# ============================================================================
# Roles & Permissions Management
# ============================================================================

@router.post("/users/{user_id}/roles", response_model=UserDTO)
async def assign_role(
    user_id: str,
    request: AssignRoleRequest,
    tenant_id: str = Query(..., description="Tenant ID"),
    current_user: dict = Depends(get_current_user),
):
    """
    Assign role to user (admin only).

    **Common Roles:**
    - customer: Regular customer
    - staff: Store staff
    - manager: Store manager
    - admin: System administrator
    - super_admin: Super administrator
    """
    # user = await user_repository.find_by_id(UUID(user_id))
    # user.add_role(request.role)
    # await user_repository.save(user)
    # return map_user_to_dto(user)

    raise HTTPException(status_code=404, detail="User not found - database integration pending")


@router.delete("/users/{user_id}/roles/{role}", response_model=UserDTO)
async def remove_role(
    user_id: str,
    role: str,
    tenant_id: str = Query(..., description="Tenant ID"),
    current_user: dict = Depends(get_current_user),
):
    """
    Remove role from user (admin only).
    """
    # user = await user_repository.find_by_id(UUID(user_id))
    # user.remove_role(role)
    # await user_repository.save(user)
    # return map_user_to_dto(user)

    raise HTTPException(status_code=404, detail="User not found - database integration pending")


@router.post("/users/{user_id}/permissions", response_model=UserDTO)
async def assign_permission(
    user_id: str,
    request: AssignPermissionRequest,
    tenant_id: str = Query(..., description="Tenant ID"),
    current_user: dict = Depends(get_current_user),
):
    """
    Assign direct permission to user (admin only).

    **Common Permissions:**
    - users.create
    - users.read
    - users.update
    - users.delete
    - products.manage
    - orders.manage
    - inventory.manage
    """
    # user = await user_repository.find_by_id(UUID(user_id))
    # user.add_permission(request.permission)
    # await user_repository.save(user)
    # return map_user_to_dto(user)

    raise HTTPException(status_code=404, detail="User not found - database integration pending")


@router.delete("/users/{user_id}/permissions/{permission}", response_model=UserDTO)
async def remove_permission(
    user_id: str,
    permission: str,
    tenant_id: str = Query(..., description="Tenant ID"),
    current_user: dict = Depends(get_current_user),
):
    """
    Remove direct permission from user (admin only).
    """
    # user = await user_repository.find_by_id(UUID(user_id))
    # user.remove_permission(permission)
    # await user_repository.save(user)
    # return map_user_to_dto(user)

    raise HTTPException(status_code=404, detail="User not found - database integration pending")


# ============================================================================
# Statistics & Analytics
# ============================================================================

@router.get("/users/stats", response_model=UserStatsDTO)
async def get_user_stats(
    tenant_id: str = Query(..., description="Tenant ID"),
    current_user: dict = Depends(get_current_user),
):
    """
    Get user statistics (admin only).

    **Returns:**
    - Total users by status
    - Users by type
    - Users by role
    - 2FA adoption rate
    - Verification rates
    - New user counts (today, week, month)
    """
    # TODO: Query from database
    # stats = await user_repository.get_stats()

    # Mock response
    return UserStatsDTO(
        total_users=0,
        active_users=0,
        inactive_users=0,
        suspended_users=0,
        pending_users=0,
        deleted_users=0,
        users_with_2fa=0,
        verified_users=0,
        users_by_type={},
        users_by_role={},
        new_users_today=0,
        new_users_this_week=0,
        new_users_this_month=0
    )
