"""
Identity & Access Management V2 API

DDD-powered user authentication and authorization using the Identity & Access bounded context.

Features:
- User registration and authentication
- Password management with bcrypt hashing
- Email, phone, and age verification (19+ for cannabis)
- Two-factor authentication (2FA)
- Account status management (active, inactive, suspended, pending, deleted)
- Account locking after 5 failed login attempts (30 min lock)
- Role-based access control (RBAC)
- Direct permission assignment
- Soft delete with data anonymization
- User preferences and profile management
- Activity tracking and audit logging

User Statuses:
- active: User can access the system
- inactive: User cannot access (temporarily disabled)
- suspended: User suspended by admin
- pending: User registered but not activated
- deleted: User soft deleted with anonymized data

Authentication Providers:
- local: Email/password authentication
- google: Google OAuth
- facebook: Facebook OAuth
- apple: Apple Sign In
- phone: Phone number authentication

Security Features:
- Bcrypt password hashing (replacing legacy SHA256)
- Password policy validation (min 8 chars, uppercase, lowercase, digit)
- Account locking after 5 failed attempts
- Two-factor authentication
- Session invalidation on password change
- Age verification for cannabis compliance (19+)
"""

from .identity_access_endpoints import router

__all__ = ["router"]
