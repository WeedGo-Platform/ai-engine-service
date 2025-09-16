"""
Security module for voice authentication
"""

from .encryption import (
    encrypt_embedding,
    decrypt_embedding,
    encrypt_sensitive_data,
    decrypt_sensitive_data,
    hash_user_id
)

__all__ = [
    'encrypt_embedding',
    'decrypt_embedding',
    'encrypt_sensitive_data',
    'decrypt_sensitive_data',
    'hash_user_id'
]