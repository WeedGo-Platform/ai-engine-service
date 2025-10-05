"""
Customer Authentication API Endpoints
Handles customer registration, login, and session management
"""

from fastapi import APIRouter, HTTPException, Depends, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import logging
import bcrypt
import uuid
import json
import asyncpg

from core.authentication import get_auth

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/auth/customer", tags=["Customer Authentication"])
security = HTTPBearer()

# Use singleton JWT authentication instance
jwt_auth = get_auth()


# Pydantic models for request/response
class UserRegistration(BaseModel):
    """User registration request model"""
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128)
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    date_of_birth: str = Field(..., description="Format: YYYY-MM-DD")
    phone: str = Field(..., min_length=10, max_length=15)
    province: Optional[str] = Field(default="ON", description="Province code (e.g., ON for Ontario)")


class UserLogin(BaseModel):
    """User login request model"""
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    """Login response model"""
    message: str
    access_token: str
    token_type: str = "bearer"
    user: Dict[str, Any]


# Database connection helper
async def get_db_connection():
    """Get database connection"""
    try:
        conn = await asyncpg.connect(
            host='localhost',
            port=5434,
            database='ai_engine',
            user='weedgo',
            password='your_password_here'
        )
        return conn
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection failed"
        )


# Helper functions
async def get_minimum_age_for_province(province_code: str = "ON") -> int:
    """Get the minimum age requirement for a province"""
    conn = None
    try:
        conn = await get_db_connection()
        result = await conn.fetchrow(
            "SELECT min_age FROM provinces_territories WHERE code = $1",
            province_code.upper()
        )
        if result and result['min_age']:
            return result['min_age']
        # Default to 19 if not found (Ontario standard)
        return 19
    except Exception as e:
        logger.error(f"Failed to get minimum age for province {province_code}: {e}")
        return 19  # Default fallback
    finally:
        if conn:
            await conn.close()

def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current authenticated user from token"""
    token = credentials.credentials

    try:
        payload = jwt_auth.verify_token(token)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
        return payload
    except Exception as e:
        logger.error(f"Authentication failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )

async def get_current_user_flexible(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
):
    """Get current authenticated user from token or X-User-Id header"""
    # Try JWT token first
    if credentials and credentials.credentials:
        try:
            payload = jwt_auth.verify_token(credentials.credentials)
            if payload:
                return payload
        except Exception as e:
            # Log the actual error for debugging
            logger.error(f"🔴 Token verification failed in get_current_user_flexible: {type(e).__name__}: {str(e)}")
            logger.error(f"Token preview: {credentials.credentials[:50]}...")
            # Re-raise the original exception with proper error detail instead of swallowing it
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Token verification failed: {str(e)}"
            )

    # Fall back to X-User-Id header (for development/testing)
    user_id = request.headers.get("X-User-Id")
    if user_id:
        logger.warning(f"⚠️ Using X-User-Id header for authentication: {user_id}")
        return {"user_id": user_id}

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated - no token or X-User-Id header provided"
    )


async def get_optional_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)):
    """Get current user from token if provided, otherwise return None"""
    if not credentials:
        return None
    
    try:
        token = credentials.credentials
        payload = jwt_auth.verify_token(token)
        return payload if payload else None
    except Exception:
        return None


# API Endpoints
@router.post("/register", response_model=LoginResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegistration):
    """
    Register a new user account
    
    Required fields:
    - email: Valid email address
    - password: Minimum 6 characters
    - first_name: User's first name
    - last_name: User's last name
    - date_of_birth: YYYY-MM-DD format (must be 19+)
    - phone: Phone number
    """
    conn = None
    try:
        conn = await get_db_connection()
        
        # Check if user already exists
        existing = await conn.fetchrow(
            "SELECT id FROM users WHERE email = $1",
            user_data.email
        )
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered"
            )
        
        # Get minimum age for the province
        province_code = user_data.province if hasattr(user_data, 'province') else "ON"
        min_age = await get_minimum_age_for_province(province_code)

        # Verify age
        dob = datetime.strptime(user_data.date_of_birth, '%Y-%m-%d')
        age = (datetime.now() - dob).days / 365.25
        age_verified = age >= min_age

        if not age_verified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Must be {min_age} years or older to register in this province"
            )
        
        # Hash password
        password_hash = hash_password(user_data.password)
        
        # Create user record
        user_id = str(uuid.uuid4())
        session_id = str(uuid.uuid4())
        
        await conn.execute(
            """
            INSERT INTO users (
                id, email, password_hash, phone, 
                first_name, last_name, date_of_birth,
                age_verified, session_id, active,
                role, created_at, updated_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
            """,
            user_id, user_data.email, password_hash, user_data.phone,
            user_data.first_name, user_data.last_name, dob.date(),  # Convert to date object
            age_verified, session_id, True,
            'customer',  # Explicitly set role to customer
            datetime.now(), datetime.now()
        )
        
        # Create JWT token
        access_token = jwt_auth.create_access_token({
            'user_id': user_id,
            'email': user_data.email,
            'session_id': session_id
        })
        
        logger.info(f"User registered: {user_data.email}")
        
        return LoginResponse(
            message="Registration successful",
            access_token=access_token,
            user={
                'id': user_id,
                'email': user_data.email,
                'first_name': user_data.first_name,
                'last_name': user_data.last_name,
                'phone': user_data.phone,
                'age_verified': age_verified
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed. Please try again."
        )
    finally:
        if conn:
            await conn.close()


@router.post("/login", response_model=LoginResponse)
async def login(credentials: UserLogin):
    """
    Authenticate user and create session
    
    Required fields:
    - email: Registered email address
    - password: User password
    """
    conn = None
    try:
        conn = await get_db_connection()
        
        # Fetch user
        user = await conn.fetchrow(
            """
            SELECT id, email, password_hash, first_name, last_name, 
                   phone, age_verified, session_id, role, tenant_id, store_id
            FROM users 
            WHERE email = $1 AND active = true
            """,
            credentials.email
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Verify password
        if not verify_password(credentials.password, user['password_hash']):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Update last login
        await conn.execute(
            "UPDATE users SET last_login = $1 WHERE id = $2",
            datetime.now(), user['id']
        )
        
        # Create JWT token with role and context
        access_token = jwt_auth.create_access_token({
            'user_id': str(user['id']),
            'email': user['email'],
            'session_id': user['session_id'] or str(uuid.uuid4()),
            'role': user['role'],
            'tenant_id': str(user['tenant_id']) if user['tenant_id'] else None,
            'store_id': str(user['store_id']) if user['store_id'] else None
        })

        logger.info(f"User logged in: {credentials.email}")

        return LoginResponse(
            message="Login successful",
            access_token=access_token,
            user={
                'id': str(user['id']),
                'email': user['email'],
                'first_name': user['first_name'],
                'last_name': user['last_name'],
                'phone': user['phone'],
                'age_verified': user['age_verified']
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed. Please try again."
        )
    finally:
        if conn:
            await conn.close()


@router.post("/logout")
async def logout(current_user: Dict = Depends(get_current_user)):
    """
    Logout user
    
    Requires authentication token in header
    """
    # In a simple implementation, logout is handled client-side by removing the token
    # For server-side tracking, you could add token to a blacklist
    
    logger.info(f"User logged out: {current_user.get('email')}")
    
    return {
        'message': 'Logout successful',
        'email': current_user.get('email')
    }


@router.get("/verify")
async def verify_token(current_user: Dict = Depends(get_current_user)):
    """
    Verify if token is valid
    
    Requires authentication token in header
    """
    conn = None
    try:
        conn = await get_db_connection()
        
        # Get user details
        user = await conn.fetchrow(
            """
            SELECT id, email, first_name, last_name, phone, age_verified
            FROM users
            WHERE id = $1 AND active = true
            """,
            current_user['user_id']
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return {
            'valid': True,
            'user': {
                'id': user['id'],
                'email': user['email'],
                'first_name': user['first_name'],
                'last_name': user['last_name'],
                'phone': user['phone'],
                'age_verified': user['age_verified']
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Verification failed"
        )
    finally:
        if conn:
            await conn.close()


@router.get("/minimum-age/{province_code}")
async def get_province_minimum_age(province_code: str):
    """
    Get minimum age requirement for a province

    Parameters:
    - province_code: Two-letter province code (e.g., 'ON' for Ontario)

    Returns minimum age requirement for the province
    """
    conn = None
    try:
        conn = await get_db_connection()

        result = await conn.fetchrow(
            """
            SELECT code, name, min_age, type
            FROM provinces_territories
            WHERE code = $1
            """,
            province_code.upper()
        )

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Province/territory with code '{province_code}' not found"
            )

        return {
            'province_code': result['code'],
            'province_name': result['name'],
            'minimum_age': result['min_age'] or 19,  # Default to 19 if not set
            'type': result['type']
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get minimum age for province {province_code}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve province information"
        )
    finally:
        if conn:
            await conn.close()


@router.get("/me")
async def get_current_user_info(current_user: Dict = Depends(get_current_user)):
    """
    Get current user information

    Requires authentication token in header
    """
    conn = None
    try:
        conn = await get_db_connection()

        # Get user details
        user = await conn.fetchrow(
            """
            SELECT id, email, first_name, last_name, phone,
                   date_of_birth, age_verified, created_at, last_login
            FROM users
            WHERE id = $1
            """,
            current_user['user_id']
        )

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        return {
            'id': user['id'],
            'email': user['email'],
            'first_name': user['first_name'],
            'last_name': user['last_name'],
            'phone': user['phone'],
            'date_of_birth': user['date_of_birth'].isoformat() if user['date_of_birth'] else None,
            'age_verified': user['age_verified'],
            'member_since': user['created_at'].isoformat() if user['created_at'] else None,
            'last_login': user['last_login'].isoformat() if user['last_login'] else None
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get user info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user information"
        )
    finally:
        if conn:
            await conn.close()


@router.get("/users/{user_id}")
async def get_user_by_id(user_id: str):
    """
    Get user information by ID

    This endpoint is used by the frontend to fetch user data
    after voice authentication or session creation.

    Parameters:
        user_id: The UUID of the user

    Returns:
        User information including profile details
    """
    conn = None
    try:
        conn = await get_db_connection()

        # Get user details
        user = await conn.fetchrow(
            """
            SELECT id, email, first_name, last_name, phone,
                   date_of_birth, age_verified, email_verified, phone_verified,
                   created_at, updated_at, last_login
            FROM users
            WHERE id = $1
            """,
            uuid.UUID(user_id)
        )

        if not user:
            logger.warning(f"User not found: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Return user data in the expected format
        return {
            'id': str(user['id']),
            'email': user['email'],
            'firstName': user['first_name'],
            'lastName': user['last_name'],
            'phone': user['phone'],
            'dateOfBirth': user['date_of_birth'].isoformat() if user['date_of_birth'] else None,
            'emailVerified': user['email_verified'],
            'phoneVerified': user['phone_verified'],
            'createdAt': user['created_at'].isoformat() if user['created_at'] else None,
            'updatedAt': user['updated_at'].isoformat() if user['updated_at'] else None
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get user by ID: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user information"
        )
    finally:
        if conn:
            await conn.close()

# Address Management Endpoints

class AddressRequest(BaseModel):
    """Address request model"""
    address_type: str = Field(..., pattern="^(delivery|billing)$")
    street_address: str = Field(..., min_length=1, max_length=255)
    unit_number: Optional[str] = Field(None, max_length=50)
    city: str = Field(..., min_length=1, max_length=100)
    province_state: str = Field(..., min_length=1, max_length=100)
    postal_code: str = Field(..., min_length=1, max_length=20)
    country: str = Field(default="CA", max_length=2)
    phone_number: Optional[str] = Field(None, max_length=50)
    label: Optional[str] = Field(None, max_length=100)
    is_default: bool = Field(default=False)
    delivery_instructions: Optional[str] = None
    same_as_billing: Optional[bool] = Field(default=False)


@router.get("/addresses")
async def get_user_addresses(current_user: Dict = Depends(get_current_user_flexible)):
    """
    Get all addresses for the current user

    Requires authentication token in header
    """
    conn = None
    try:
        conn = await get_db_connection()

        addresses = await conn.fetch(
            """
            SELECT
                id,
                address_type,
                is_default,
                label,
                street_address,
                unit_number,
                city,
                province_state,
                postal_code,
                country,
                phone_number,
                delivery_instructions,
                created_at,
                updated_at
            FROM user_addresses
            WHERE user_id = $1
            ORDER BY is_default DESC, address_type, created_at DESC
            """,
            uuid.UUID(current_user['user_id'])
        )

        # Format addresses for frontend
        formatted_addresses = []
        for addr in addresses:
            formatted_addresses.append({
                'id': str(addr['id']),
                'type': addr['address_type'],
                'isDefault': addr['is_default'],
                'label': addr['label'],
                'street': addr['street_address'],
                'apartment': addr['unit_number'],
                'city': addr['city'],
                'province': addr['province_state'],
                'postalCode': addr['postal_code'],
                'country': addr['country'],
                'phone': addr['phone_number'],
                'deliveryInstructions': addr['delivery_instructions'],
                'createdAt': addr['created_at'].isoformat() if addr['created_at'] else None,
                'updatedAt': addr['updated_at'].isoformat() if addr['updated_at'] else None
            })

        return {
            'addresses': formatted_addresses,
            'count': len(formatted_addresses)
        }

    except Exception as e:
        logger.error(f"Failed to get addresses: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve addresses"
        )
    finally:
        if conn:
            await conn.close()


@router.post("/addresses")
async def create_user_address(
    address: AddressRequest,
    request: Request,
    current_user: Dict = Depends(get_current_user_flexible)
):
    """
    Create a new address for the current user

    Requires authentication token in header
    """
    # Debug logging
    logger.info(f"📍 CREATE ADDRESS REQUEST RECEIVED")
    logger.info(f"  Headers: {dict(request.headers)}")
    logger.info(f"  Current user from auth: {current_user}")
    logger.info(f"  Address data: {address.dict()}")

    conn = None
    try:
        conn = await get_db_connection()
        user_id = uuid.UUID(current_user['user_id'])

        # If setting as default, unset other defaults of same type
        if address.is_default:
            await conn.execute(
                """
                UPDATE user_addresses
                SET is_default = false
                WHERE user_id = $1 AND address_type = $2
                """,
                user_id,
                address.address_type
            )

        # Create the new address
        address_id = await conn.fetchval(
            """
            INSERT INTO user_addresses (
                user_id,
                address_type,
                is_default,
                label,
                street_address,
                unit_number,
                city,
                province_state,
                postal_code,
                country,
                phone_number,
                delivery_instructions
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
            RETURNING id
            """,
            user_id,
            address.address_type,
            address.is_default,
            address.label,
            address.street_address,
            address.unit_number,
            address.city,
            address.province_state,
            address.postal_code,
            address.country,
            address.phone_number,
            address.delivery_instructions
        )

        logger.info(f"Address created for user {current_user['user_id']}: {address_id}")

        return {
            'message': 'Address created successfully',
            'address_id': str(address_id)
        }

    except Exception as e:
        logger.error(f"Failed to create address: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create address"
        )
    finally:
        if conn:
            await conn.close()


@router.put("/addresses/{address_id}")
async def update_user_address(
    address_id: str,
    address: AddressRequest,
    current_user: Dict = Depends(get_current_user_flexible)
):
    """
    Update an existing address for the current user

    Requires authentication token in header
    """
    conn = None
    try:
        conn = await get_db_connection()
        user_id = uuid.UUID(current_user['user_id'])

        # Verify ownership
        owner_id = await conn.fetchval(
            "SELECT user_id FROM user_addresses WHERE id = $1",
            uuid.UUID(address_id)
        )

        if not owner_id or owner_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this address"
            )

        # If setting as default, unset other defaults of same type
        if address.is_default:
            await conn.execute(
                """
                UPDATE user_addresses
                SET is_default = false
                WHERE user_id = $1 AND address_type = $2 AND id != $3
                """,
                user_id,
                address.address_type,
                uuid.UUID(address_id)
            )

        # Update the address
        await conn.execute(
            """
            UPDATE user_addresses
            SET
                address_type = $2,
                is_default = $3,
                label = $4,
                street_address = $5,
                unit_number = $6,
                city = $7,
                province_state = $8,
                postal_code = $9,
                country = $10,
                phone_number = $11,
                delivery_instructions = $12,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = $1
            """,
            uuid.UUID(address_id),
            address.address_type,
            address.is_default,
            address.label,
            address.street_address,
            address.unit_number,
            address.city,
            address.province_state,
            address.postal_code,
            address.country,
            address.phone_number,
            address.delivery_instructions
        )

        logger.info(f"Address {address_id} updated for user {current_user['user_id']}")

        return {'message': 'Address updated successfully'}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update address: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update address"
        )
    finally:
        if conn:
            await conn.close()


@router.delete("/addresses/{address_id}")
async def delete_user_address(
    address_id: str,
    current_user: Dict = Depends(get_current_user_flexible)
):
    """
    Delete an address for the current user

    Requires authentication token in header
    """
    conn = None
    try:
        conn = await get_db_connection()
        user_id = uuid.UUID(current_user['user_id'])

        # Verify ownership and delete
        deleted = await conn.fetchval(
            """
            DELETE FROM user_addresses
            WHERE id = $1 AND user_id = $2
            RETURNING id
            """,
            uuid.UUID(address_id),
            user_id
        )

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Address not found or not authorized"
            )

        logger.info(f"Address {address_id} deleted for user {current_user['user_id']}")

        return {'message': 'Address deleted successfully'}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete address: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete address"
        )
    finally:
        if conn:
            await conn.close()


@router.put("/addresses/{address_id}/set-default")
async def set_default_address(
    address_id: str,
    current_user: Dict = Depends(get_current_user_flexible)
):
    """
    Set an address as the default for its type

    Requires authentication token in header
    """
    conn = None
    try:
        conn = await get_db_connection()
        user_id = uuid.UUID(current_user['user_id'])

        # Get address type and verify ownership
        address = await conn.fetchrow(
            "SELECT user_id, address_type FROM user_addresses WHERE id = $1",
            uuid.UUID(address_id)
        )

        if not address or address['user_id'] != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Address not found or not authorized"
            )

        # Unset other defaults of same type
        await conn.execute(
            """
            UPDATE user_addresses
            SET is_default = false
            WHERE user_id = $1 AND address_type = $2
            """,
            user_id,
            address['address_type']
        )

        # Set this address as default
        await conn.execute(
            """
            UPDATE user_addresses
            SET is_default = true, updated_at = CURRENT_TIMESTAMP
            WHERE id = $1
            """,
            uuid.UUID(address_id)
        )

        logger.info(f"Address {address_id} set as default for user {current_user['user_id']}")

        return {'message': 'Default address updated successfully'}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to set default address: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to set default address"
        )
    finally:
        if conn:
            await conn.close()
