"""
Access Control System for AGI Platform
Implements RBAC (Role-Based Access Control) with fine-grained permissions
"""

import asyncio
import logging
from typing import Dict, List, Set, Optional, Any
from datetime import datetime, timedelta
from enum import Enum
import json
import hashlib
import secrets
from dataclasses import dataclass, field

from agi.core.database import get_db_manager
from agi.core.interfaces import IUser

logger = logging.getLogger(__name__)


class Permission(Enum):
    """System permissions"""
    # Model permissions
    MODEL_READ = "model:read"
    MODEL_WRITE = "model:write"
    MODEL_EXECUTE = "model:execute"
    MODEL_DELETE = "model:delete"
    
    # Tool permissions
    TOOL_READ = "tool:read"
    TOOL_WRITE = "tool:write"
    TOOL_EXECUTE = "tool:execute"
    TOOL_DELETE = "tool:delete"
    
    # Agent permissions
    AGENT_READ = "agent:read"
    AGENT_WRITE = "agent:write"
    AGENT_EXECUTE = "agent:execute"
    AGENT_DELETE = "agent:delete"
    AGENT_DELEGATE = "agent:delegate"
    
    # Knowledge permissions
    KNOWLEDGE_READ = "knowledge:read"
    KNOWLEDGE_WRITE = "knowledge:write"
    KNOWLEDGE_DELETE = "knowledge:delete"
    
    # Memory permissions
    MEMORY_READ = "memory:read"
    MEMORY_WRITE = "memory:write"
    MEMORY_DELETE = "memory:delete"
    
    # System permissions
    SYSTEM_CONFIG = "system:config"
    SYSTEM_MONITOR = "system:monitor"
    SYSTEM_DEBUG = "system:debug"
    SYSTEM_ADMIN = "system:admin"
    
    # Security permissions
    SECURITY_AUDIT = "security:audit"
    SECURITY_MANAGE_USERS = "security:manage_users"
    SECURITY_MANAGE_ROLES = "security:manage_roles"
    SECURITY_BYPASS_FILTER = "security:bypass_filter"


class Role(Enum):
    """System roles with predefined permissions"""
    GUEST = "guest"
    USER = "user"
    DEVELOPER = "developer"
    OPERATOR = "operator"
    ADMIN = "admin"
    SYSTEM = "system"


# Default role permissions
DEFAULT_ROLE_PERMISSIONS = {
    Role.GUEST: {
        Permission.MODEL_READ,
        Permission.TOOL_READ,
        Permission.AGENT_READ,
        Permission.KNOWLEDGE_READ
    },
    Role.USER: {
        Permission.MODEL_READ,
        Permission.MODEL_EXECUTE,
        Permission.TOOL_READ,
        Permission.TOOL_EXECUTE,
        Permission.AGENT_READ,
        Permission.AGENT_EXECUTE,
        Permission.KNOWLEDGE_READ,
        Permission.MEMORY_READ,
        Permission.MEMORY_WRITE
    },
    Role.DEVELOPER: {
        Permission.MODEL_READ,
        Permission.MODEL_WRITE,
        Permission.MODEL_EXECUTE,
        Permission.TOOL_READ,
        Permission.TOOL_WRITE,
        Permission.TOOL_EXECUTE,
        Permission.AGENT_READ,
        Permission.AGENT_WRITE,
        Permission.AGENT_EXECUTE,
        Permission.AGENT_DELEGATE,
        Permission.KNOWLEDGE_READ,
        Permission.KNOWLEDGE_WRITE,
        Permission.MEMORY_READ,
        Permission.MEMORY_WRITE,
        Permission.SYSTEM_MONITOR,
        Permission.SYSTEM_DEBUG
    },
    Role.OPERATOR: {
        Permission.MODEL_READ,
        Permission.MODEL_EXECUTE,
        Permission.TOOL_READ,
        Permission.TOOL_EXECUTE,
        Permission.AGENT_READ,
        Permission.AGENT_EXECUTE,
        Permission.AGENT_DELEGATE,
        Permission.KNOWLEDGE_READ,
        Permission.MEMORY_READ,
        Permission.SYSTEM_CONFIG,
        Permission.SYSTEM_MONITOR,
        Permission.SECURITY_AUDIT
    },
    Role.ADMIN: {
        # Admins get all permissions
        *[p for p in Permission]
    },
    Role.SYSTEM: {
        # System role has all permissions and bypasses checks
        *[p for p in Permission]
    }
}


@dataclass
class AccessContext:
    """Context for access control decisions"""
    user_id: str
    session_id: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    action: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AccessDecision:
    """Result of an access control decision"""
    allowed: bool
    reason: str
    permissions_required: Set[Permission] = field(default_factory=set)
    permissions_granted: Set[Permission] = field(default_factory=set)
    conditions: Dict[str, Any] = field(default_factory=dict)
    audit_logged: bool = False


class AccessControlManager:
    """
    Manages access control for the AGI system
    """
    
    _instance = None
    _lock = asyncio.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize access control manager"""
        if not hasattr(self, '_initialized'):
            self.db_manager = None
            self._user_cache: Dict[str, Dict[str, Any]] = {}
            self._role_cache: Dict[str, Set[Permission]] = {}
            self._session_cache: Dict[str, Dict[str, Any]] = {}
            self._api_keys: Dict[str, str] = {}  # api_key -> user_id
            self._initialized = False
    
    async def initialize(self):
        """Initialize the access control system"""
        if self._initialized:
            return
        
        async with self._lock:
            if self._initialized:
                return
            
            try:
                # Get database manager
                self.db_manager = await get_db_manager()
                
                # Create tables
                await self._create_tables()
                
                # Load default roles
                await self._load_default_roles()
                
                # Load cached data
                await self._load_cache()
                
                self._initialized = True
                logger.info("Access control manager initialized")
                
            except Exception as e:
                logger.error(f"Failed to initialize access control: {e}")
                raise
    
    async def _create_tables(self):
        """Create access control tables"""
        queries = [
            """
            CREATE TABLE IF NOT EXISTS agi_users (
                id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE,
                password_hash TEXT,
                roles TEXT[],
                permissions TEXT[],
                api_key TEXT UNIQUE,
                is_active BOOLEAN DEFAULT true,
                is_system BOOLEAN DEFAULT false,
                metadata JSONB DEFAULT '{}',
                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS agi_roles (
                name TEXT PRIMARY KEY,
                description TEXT,
                permissions TEXT[],
                is_system BOOLEAN DEFAULT false,
                metadata JSONB DEFAULT '{}',
                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS agi_sessions (
                id TEXT PRIMARY KEY,
                user_id TEXT REFERENCES agi_users(id),
                token TEXT UNIQUE NOT NULL,
                ip_address TEXT,
                user_agent TEXT,
                expires_at TIMESTAMPTZ,
                is_active BOOLEAN DEFAULT true,
                metadata JSONB DEFAULT '{}',
                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                last_accessed TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS agi_access_logs (
                id SERIAL PRIMARY KEY,
                user_id TEXT,
                session_id TEXT,
                resource_type TEXT,
                resource_id TEXT,
                action TEXT,
                allowed BOOLEAN,
                reason TEXT,
                context JSONB,
                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS agi_permission_overrides (
                id SERIAL PRIMARY KEY,
                user_id TEXT REFERENCES agi_users(id),
                resource_type TEXT,
                resource_id TEXT,
                permissions TEXT[],
                grant_type TEXT CHECK (grant_type IN ('allow', 'deny')),
                expires_at TIMESTAMPTZ,
                metadata JSONB DEFAULT '{}',
                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
            )
            """
        ]
        
        for query in queries:
            await self.db_manager.execute(query)
        
        # Create indexes
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_users_api_key ON agi_users(api_key)",
            "CREATE INDEX IF NOT EXISTS idx_sessions_token ON agi_sessions(token)",
            "CREATE INDEX IF NOT EXISTS idx_sessions_user ON agi_sessions(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_access_logs_user ON agi_access_logs(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_access_logs_resource ON agi_access_logs(resource_type, resource_id)",
            "CREATE INDEX IF NOT EXISTS idx_permission_overrides_user ON agi_permission_overrides(user_id)"
        ]
        
        for index in indexes:
            await self.db_manager.execute(index)
    
    async def _load_default_roles(self):
        """Load default system roles"""
        for role in Role:
            permissions = list(DEFAULT_ROLE_PERMISSIONS.get(role, set()))
            permission_strings = [p.value for p in permissions]
            
            await self.db_manager.execute(
                """
                INSERT INTO agi_roles (name, description, permissions, is_system)
                VALUES ($1, $2, $3, true)
                ON CONFLICT (name) DO UPDATE
                SET permissions = $3,
                    is_system = true
                """,
                role.value,
                f"System role: {role.value}",
                permission_strings
            )
    
    async def _load_cache(self):
        """Load frequently accessed data into cache"""
        # Load roles into cache
        rows = await self.db_manager.fetch(
            "SELECT name, permissions FROM agi_roles"
        )
        
        for row in rows:
            permissions = set()
            for perm_str in row['permissions']:
                try:
                    permissions.add(Permission(perm_str))
                except ValueError:
                    logger.warning(f"Unknown permission: {perm_str}")
            self._role_cache[row['name']] = permissions
    
    async def check_access(
        self,
        context: AccessContext,
        required_permissions: Set[Permission]
    ) -> AccessDecision:
        """
        Check if access should be allowed
        
        Args:
            context: Access context
            required_permissions: Required permissions
        
        Returns:
            Access decision
        """
        decision = AccessDecision(
            allowed=False,
            reason="Access denied",
            permissions_required=required_permissions
        )
        
        try:
            # Get user
            user = await self._get_user(context.user_id)
            if not user:
                decision.reason = "User not found"
                await self._log_access(context, decision)
                return decision
            
            if not user.get('is_active'):
                decision.reason = "User is inactive"
                await self._log_access(context, decision)
                return decision
            
            # Check session if provided
            if context.session_id:
                session = await self._get_session(context.session_id)
                if not session or session['user_id'] != context.user_id:
                    decision.reason = "Invalid session"
                    await self._log_access(context, decision)
                    return decision
                
                if session.get('expires_at') and session['expires_at'] < datetime.utcnow():
                    decision.reason = "Session expired"
                    await self._log_access(context, decision)
                    return decision
            
            # Get user permissions
            user_permissions = await self._get_user_permissions(user)
            
            # Check for system user
            if user.get('is_system'):
                decision.allowed = True
                decision.reason = "System user has all permissions"
                decision.permissions_granted = set(Permission)
                await self._log_access(context, decision)
                return decision
            
            # Check resource-specific overrides
            if context.resource_type and context.resource_id:
                override_permissions = await self._get_permission_overrides(
                    context.user_id,
                    context.resource_type,
                    context.resource_id
                )
                user_permissions.update(override_permissions)
            
            # Check if user has all required permissions
            decision.permissions_granted = user_permissions
            if required_permissions.issubset(user_permissions):
                decision.allowed = True
                decision.reason = "All required permissions granted"
            else:
                missing = required_permissions - user_permissions
                decision.reason = f"Missing permissions: {', '.join(p.value for p in missing)}"
            
            # Log access attempt
            await self._log_access(context, decision)
            
            return decision
            
        except Exception as e:
            logger.error(f"Error checking access: {e}")
            decision.reason = "Internal error"
            await self._log_access(context, decision)
            return decision
    
    async def _get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user from cache or database"""
        # Check cache
        if user_id in self._user_cache:
            return self._user_cache[user_id]
        
        # Load from database
        row = await self.db_manager.fetchone(
            "SELECT * FROM agi_users WHERE id = $1",
            user_id
        )
        
        if row:
            user = dict(row)
            self._user_cache[user_id] = user
            return user
        
        return None
    
    async def _get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session from cache or database"""
        # Check cache
        if session_id in self._session_cache:
            return self._session_cache[session_id]
        
        # Load from database
        row = await self.db_manager.fetchone(
            "SELECT * FROM agi_sessions WHERE id = $1 AND is_active = true",
            session_id
        )
        
        if row:
            session = dict(row)
            self._session_cache[session_id] = session
            
            # Update last accessed
            await self.db_manager.execute(
                "UPDATE agi_sessions SET last_accessed = CURRENT_TIMESTAMP WHERE id = $1",
                session_id
            )
            
            return session
        
        return None
    
    async def _get_user_permissions(self, user: Dict[str, Any]) -> Set[Permission]:
        """Get all permissions for a user"""
        permissions = set()
        
        # Get role permissions
        for role_name in user.get('roles', []):
            if role_name in self._role_cache:
                permissions.update(self._role_cache[role_name])
        
        # Get direct permissions
        for perm_str in user.get('permissions', []):
            try:
                permissions.add(Permission(perm_str))
            except ValueError:
                logger.warning(f"Unknown permission: {perm_str}")
        
        return permissions
    
    async def _get_permission_overrides(
        self,
        user_id: str,
        resource_type: str,
        resource_id: str
    ) -> Set[Permission]:
        """Get permission overrides for a specific resource"""
        rows = await self.db_manager.fetch(
            """
            SELECT permissions, grant_type
            FROM agi_permission_overrides
            WHERE user_id = $1
              AND resource_type = $2
              AND resource_id = $3
              AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)
            """,
            user_id,
            resource_type,
            resource_id
        )
        
        allowed = set()
        denied = set()
        
        for row in rows:
            perms = set()
            for perm_str in row['permissions']:
                try:
                    perms.add(Permission(perm_str))
                except ValueError:
                    logger.warning(f"Unknown permission: {perm_str}")
            
            if row['grant_type'] == 'allow':
                allowed.update(perms)
            else:
                denied.update(perms)
        
        return allowed - denied
    
    async def _log_access(
        self,
        context: AccessContext,
        decision: AccessDecision
    ):
        """Log access attempt"""
        try:
            await self.db_manager.execute(
                """
                INSERT INTO agi_access_logs (
                    user_id, session_id, resource_type, resource_id,
                    action, allowed, reason, context
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                """,
                context.user_id,
                context.session_id,
                context.resource_type,
                context.resource_id,
                context.action,
                decision.allowed,
                decision.reason,
                json.dumps({
                    'ip_address': context.ip_address,
                    'user_agent': context.user_agent,
                    'metadata': context.metadata,
                    'permissions_required': [p.value for p in decision.permissions_required],
                    'permissions_granted': [p.value for p in decision.permissions_granted]
                })
            )
            decision.audit_logged = True
        except Exception as e:
            logger.error(f"Failed to log access: {e}")
    
    async def create_user(
        self,
        username: str,
        email: Optional[str] = None,
        password: Optional[str] = None,
        roles: Optional[List[Role]] = None,
        permissions: Optional[List[Permission]] = None
    ) -> str:
        """Create a new user"""
        user_id = f"user_{secrets.token_hex(16)}"
        api_key = f"sk_{secrets.token_hex(32)}"
        
        # Hash password if provided
        password_hash = None
        if password:
            password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        # Convert roles and permissions to strings
        role_strings = [r.value for r in (roles or [Role.USER])]
        permission_strings = [p.value for p in (permissions or [])]
        
        await self.db_manager.execute(
            """
            INSERT INTO agi_users (
                id, username, email, password_hash,
                roles, permissions, api_key
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            """,
            user_id,
            username,
            email,
            password_hash,
            role_strings,
            permission_strings,
            api_key
        )
        
        # Clear cache
        if user_id in self._user_cache:
            del self._user_cache[user_id]
        
        self._api_keys[api_key] = user_id
        
        logger.info(f"Created user {username} with ID {user_id}")
        return user_id
    
    async def create_session(
        self,
        user_id: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        ttl_hours: int = 24
    ) -> str:
        """Create a new session for a user"""
        session_id = f"sess_{secrets.token_hex(16)}"
        token = f"tok_{secrets.token_hex(32)}"
        expires_at = datetime.utcnow() + timedelta(hours=ttl_hours)
        
        await self.db_manager.execute(
            """
            INSERT INTO agi_sessions (
                id, user_id, token, ip_address, user_agent, expires_at
            )
            VALUES ($1, $2, $3, $4, $5, $6)
            """,
            session_id,
            user_id,
            token,
            ip_address,
            user_agent,
            expires_at
        )
        
        logger.info(f"Created session {session_id} for user {user_id}")
        return session_id
    
    async def validate_api_key(self, api_key: str) -> Optional[str]:
        """Validate API key and return user ID"""
        # Check cache
        if api_key in self._api_keys:
            return self._api_keys[api_key]
        
        # Check database
        row = await self.db_manager.fetchone(
            "SELECT id FROM agi_users WHERE api_key = $1 AND is_active = true",
            api_key
        )
        
        if row:
            user_id = row['id']
            self._api_keys[api_key] = user_id
            return user_id
        
        return None
    
    async def grant_permission(
        self,
        user_id: str,
        resource_type: str,
        resource_id: str,
        permissions: List[Permission],
        expires_in_hours: Optional[int] = None
    ):
        """Grant permissions for a specific resource"""
        expires_at = None
        if expires_in_hours:
            expires_at = datetime.utcnow() + timedelta(hours=expires_in_hours)
        
        permission_strings = [p.value for p in permissions]
        
        await self.db_manager.execute(
            """
            INSERT INTO agi_permission_overrides (
                user_id, resource_type, resource_id,
                permissions, grant_type, expires_at
            )
            VALUES ($1, $2, $3, $4, 'allow', $5)
            """,
            user_id,
            resource_type,
            resource_id,
            permission_strings,
            expires_at
        )
        
        logger.info(f"Granted permissions for user {user_id} on {resource_type}/{resource_id}")
    
    async def revoke_permission(
        self,
        user_id: str,
        resource_type: str,
        resource_id: str,
        permissions: List[Permission]
    ):
        """Revoke permissions for a specific resource"""
        permission_strings = [p.value for p in permissions]
        
        await self.db_manager.execute(
            """
            INSERT INTO agi_permission_overrides (
                user_id, resource_type, resource_id,
                permissions, grant_type
            )
            VALUES ($1, $2, $3, $4, 'deny')
            """,
            user_id,
            resource_type,
            resource_id,
            permission_strings
        )
        
        logger.info(f"Revoked permissions for user {user_id} on {resource_type}/{resource_id}")
    
    async def get_audit_logs(
        self,
        user_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get audit logs"""
        query = "SELECT * FROM agi_access_logs WHERE 1=1"
        params = []
        
        if user_id:
            params.append(user_id)
            query += f" AND user_id = ${len(params)}"
        
        if resource_type:
            params.append(resource_type)
            query += f" AND resource_type = ${len(params)}"
        
        if resource_id:
            params.append(resource_id)
            query += f" AND resource_id = ${len(params)}"
        
        query += f" ORDER BY created_at DESC LIMIT {limit}"
        
        rows = await self.db_manager.fetch(query, *params)
        return [dict(row) for row in rows]


# Singleton accessor
_manager_instance = None

async def get_access_control() -> AccessControlManager:
    """Get or create the access control manager"""
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = AccessControlManager()
        await _manager_instance.initialize()
    return _manager_instance
