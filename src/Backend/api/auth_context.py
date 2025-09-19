"""
Context-Aware Authentication API Endpoints
Provides multi-context authentication allowing users to switch between customer and admin roles
"""

from fastapi import APIRouter, HTTPException, Depends, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import logging
import bcrypt
import uuid
import asyncpg
import os

from core.authentication import JWTAuthentication

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/auth/context", tags=["Context Authentication"])
security = HTTPBearer()

# Initialize JWT authentication
jwt_auth = JWTAuthentication()

# Database connection
async def get_db_connection():
    """Get database connection"""
    return await asyncpg.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=int(os.getenv('DB_PORT', 5434)),
        database=os.getenv('DB_NAME', 'ai_engine'),
        user=os.getenv('DB_USER', 'weedgo'),
        password=os.getenv('DB_PASSWORD', 'your_password_here')
    )

# Pydantic models
class UnifiedLoginRequest(BaseModel):
    """Unified login request"""
    email: EmailStr
    password: str = Field(..., min_length=6)
    context: Optional[str] = Field(None, description="Preferred context: 'customer' or 'admin'")

class UserContext(BaseModel):
    """User context information"""
    type: str  # 'customer' or 'admin'
    role: Optional[str]  # Specific role if admin
    tenant_id: Optional[str]
    store_id: Optional[str]
    permissions: List[str] = []
    access_token: str

class UnifiedLoginResponse(BaseModel):
    """Unified login response with all available contexts"""
    message: str
    user_id: str
    email: str
    name: str
    available_contexts: List[UserContext]
    default_context: str
    
class ContextSwitchRequest(BaseModel):
    """Request to switch user context"""
    target_context: str  # 'customer' or 'admin'
    
class ContextSwitchResponse(BaseModel):
    """Response after switching context"""
    message: str
    new_context: UserContext

# Helper functions
def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

async def get_user_contexts(user_id: str, conn: asyncpg.Connection) -> List[UserContext]:
    """Get all available contexts for a user"""
    contexts = []
    
    # Get user information
    user = await conn.fetchrow(
        """
        SELECT id, email, role, tenant_id, store_id, 
               first_name, last_name, session_id
        FROM users 
        WHERE id = $1
        """,
        user_id
    )
    
    if not user:
        return contexts
    
    # Check if user has customer context
    if user['role'] == 'customer':
        # User is primarily a customer
        customer_token = jwt_auth.create_access_token({
            'user_id': str(user['id']),  # Convert UUID to string
            'email': user['email'],
            'role': 'customer',
            'context': 'customer',
            'tenant_id': str(user['tenant_id']) if user['tenant_id'] else None,
            'session_id': str(user['session_id']) if user['session_id'] else str(uuid.uuid4())
        })
        
        contexts.append(UserContext(
            type='customer',
            role='customer',
            tenant_id=str(user['tenant_id']) if user['tenant_id'] else None,
            store_id=None,
            permissions=[],
            access_token=customer_token
        ))
    
    # Check if user has admin context
    if user['role'] in ['staff', 'store_manager', 'tenant_admin', 'super_admin']:
        # Get role-specific permissions
        permissions = await get_role_permissions(user['role'], conn)
        
        admin_token = jwt_auth.create_access_token({
            'user_id': str(user['id']),  # Convert UUID to string
            'email': user['email'],
            'role': user['role'],
            'context': 'admin',
            'tenant_id': str(user['tenant_id']) if user['tenant_id'] else None,
            'store_id': str(user['store_id']) if user['store_id'] else None,
            'permissions': permissions,
            'session_id': str(user['session_id']) if user['session_id'] else str(uuid.uuid4())
        })
        
        contexts.append(UserContext(
            type='admin',
            role=user['role'],
            tenant_id=str(user['tenant_id']) if user['tenant_id'] else None,
            store_id=str(user['store_id']) if user['store_id'] else None,
            permissions=permissions,
            access_token=admin_token
        ))
        
        # Also create customer context for admin users (they can shop too)
        customer_token = jwt_auth.create_access_token({
            'user_id': str(user['id']),  # Convert UUID to string
            'email': user['email'],
            'role': user['role'],
            'context': 'customer',
            'tenant_id': str(user['tenant_id']) if user['tenant_id'] else None,
            'session_id': str(user['session_id']) if user['session_id'] else str(uuid.uuid4())
        })
        
        contexts.append(UserContext(
            type='customer',
            role=user['role'],  # Keep their actual role
            tenant_id=str(user['tenant_id']) if user['tenant_id'] else None,
            store_id=None,
            permissions=[],
            access_token=customer_token
        ))
    
    return contexts

async def get_role_permissions(role: str, conn: asyncpg.Connection) -> List[str]:
    """Get permissions for a specific role"""
    # This is a simplified version - you might want to load from database
    permissions_map = {
        'super_admin': ['*'],  # All permissions
        'tenant_admin': [
            'tenant.manage', 'stores.manage', 'users.manage', 
            'inventory.manage', 'orders.manage', 'reports.view'
        ],
        'store_manager': [
            'store.manage', 'inventory.manage', 'orders.manage', 
            'staff.manage', 'reports.view'
        ],
        'staff': [
            'inventory.read', 'orders.create', 'orders.read', 
            'customers.read', 'pos.use'
        ],
        'customer': []
    }
    
    return permissions_map.get(role, [])

# API Endpoints
@router.post("/login", response_model=UnifiedLoginResponse)
async def unified_login(credentials: UnifiedLoginRequest):
    """
    Unified login endpoint that returns all available contexts for a user
    
    This allows users to:
    - See all their available contexts (customer, admin)
    - Get tokens for each context
    - Choose their preferred context
    """
    conn = None
    try:
        conn = await get_db_connection()
        
        # Fetch user
        user = await conn.fetchrow(
            """
            SELECT id, email, password_hash, first_name, last_name, 
                   role, tenant_id, store_id, active
            FROM users 
            WHERE email = $1
            """,
            credentials.email
        )
        
        if not user or not user['active']:
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
        
        # Get all available contexts for this user
        contexts = await get_user_contexts(user['id'], conn)
        
        # Determine default context
        if credentials.context:
            # User specified preference
            default_context = credentials.context
        elif user['role'] == 'customer':
            default_context = 'customer'
        else:
            # Admin users default to admin context
            default_context = 'admin'
        
        # Log the login
        await conn.execute(
            """
            INSERT INTO user_login_logs (user_id, ip_address, user_agent, login_successful)
            VALUES ($1, $2::inet, $3, $4)
            """,
            user['id'], '0.0.0.0', 'API', True
        )
        
        logger.info(f"Unified login successful for: {credentials.email}")
        
        return UnifiedLoginResponse(
            message="Login successful",
            user_id=str(user['id']),  # Convert UUID to string
            email=user['email'],
            name=f"{user['first_name']} {user['last_name']}",
            available_contexts=contexts,
            default_context=default_context
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unified login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during login"
        )
    finally:
        if conn:
            await conn.close()

@router.post("/switch-context", response_model=ContextSwitchResponse)
async def switch_context(
    request: ContextSwitchRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Switch user context between customer and admin
    
    This endpoint allows users with multiple contexts to switch between them
    without re-authenticating
    """
    conn = None
    try:
        # Verify current token
        token = credentials.credentials
        payload = jwt_auth.verify_token(token)
        
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token"
            )
        
        user_id = payload.get('user_id')
        
        conn = await get_db_connection()
        
        # Get all contexts for the user
        contexts = await get_user_contexts(user_id, conn)
        
        # Find the requested context
        new_context = None
        for ctx in contexts:
            if ctx.type == request.target_context:
                new_context = ctx
                break
        
        if not new_context:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User does not have access to {request.target_context} context"
            )
        
        logger.info(f"User {user_id} switched to {request.target_context} context")
        
        return ContextSwitchResponse(
            message=f"Switched to {request.target_context} context",
            new_context=new_context
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Context switch error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during context switch"
        )
    finally:
        if conn:
            await conn.close()

@router.get("/contexts")
async def get_my_contexts(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Get all available contexts for the current user
    """
    conn = None
    try:
        # Verify token
        token = credentials.credentials
        payload = jwt_auth.verify_token(token)
        
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token"
            )
        
        user_id = payload.get('user_id')
        
        conn = await get_db_connection()
        contexts = await get_user_contexts(user_id, conn)
        
        return {
            "user_id": user_id,
            "contexts": contexts
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get contexts error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while fetching contexts"
        )
    finally:
        if conn:
            await conn.close()

class DualRoleRegistration(BaseModel):
    """Dual role registration request"""
    email: EmailStr
    password: str = Field(..., min_length=6)
    first_name: str
    last_name: str
    admin_role: str
    tenant_id: Optional[str] = None
    store_id: Optional[str] = None

@router.post("/register-dual-role")
async def register_dual_role(registration: DualRoleRegistration):
    """
    Register a user with both customer and admin capabilities
    This is useful for staff members who also need to shop
    """
    conn = None
    try:
        conn = await get_db_connection()
        
        # Check if user exists
        existing = await conn.fetchrow(
            "SELECT id FROM users WHERE email = $1",
            registration.email
        )
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered"
            )
        
        # Validate admin role
        if registration.admin_role not in ['staff', 'store_manager', 'tenant_admin']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid admin role"
            )
        
        # Create user with admin role
        user_id = str(uuid.uuid4())
        password_hash = hash_password(registration.password)
        
        await conn.execute(
            """
            INSERT INTO users (
                id, email, password_hash, first_name, last_name,
                role, tenant_id, store_id, active, created_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            """,
            user_id, registration.email, password_hash, registration.first_name, registration.last_name,
            registration.admin_role, registration.tenant_id, registration.store_id, True, datetime.now()
        )
        
        # The customer record will be created automatically by the trigger
        # This gives them both admin and shopping capabilities
        
        logger.info(f"Dual-role user registered: {registration.email} with role {registration.admin_role}")
        
        # Get contexts for the new user
        contexts = await get_user_contexts(user_id, conn)
        
        return {
            "message": "User registered successfully with dual role",
            "user_id": user_id,
            "email": registration.email,
            "admin_role": registration.admin_role,
            "contexts": contexts
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Dual role registration error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during registration"
        )
    finally:
        if conn:
            await conn.close()