"""
Encryption utilities for voice embeddings and sensitive data
"""

import base64
import os
from typing import Union
import numpy as np
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import logging

logger = logging.getLogger(__name__)

# Get encryption key from environment or generate one
ENCRYPTION_KEY = os.environ.get('VOICE_EMBEDDING_KEY', 'default-dev-key-change-in-production')
SALT = b'weedgo-voice-auth-salt'  # Should be random in production


def _get_encryption_key() -> bytes:
    """Derive encryption key from password"""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=SALT,
        iterations=100000,
        backend=default_backend()
    )
    return kdf.derive(ENCRYPTION_KEY.encode())


def encrypt_embedding(embedding: np.ndarray) -> str:
    """
    Encrypt voice embedding for secure storage

    Args:
        embedding: Numpy array containing voice embedding

    Returns:
        Base64 encoded encrypted embedding
    """
    try:
        # Convert embedding to bytes
        embedding_bytes = embedding.astype(np.float32).tobytes()

        # Generate IV
        iv = os.urandom(16)

        # Create cipher
        cipher = Cipher(
            algorithms.AES(_get_encryption_key()),
            modes.CBC(iv),
            backend=default_backend()
        )
        encryptor = cipher.encryptor()

        # Pad data to multiple of 16 bytes
        padding_length = 16 - (len(embedding_bytes) % 16)
        if padding_length != 16:
            embedding_bytes += bytes([padding_length]) * padding_length

        # Encrypt
        encrypted = encryptor.update(embedding_bytes) + encryptor.finalize()

        # Combine IV and encrypted data
        encrypted_with_iv = iv + encrypted

        # Encode to base64
        return base64.b64encode(encrypted_with_iv).decode('utf-8')

    except Exception as e:
        logger.error(f"Error encrypting embedding: {str(e)}")
        raise


def decrypt_embedding(encrypted_data: str, embedding_size: int = None) -> np.ndarray:
    """
    Decrypt voice embedding from storage

    Args:
        encrypted_data: Base64 encoded encrypted embedding
        embedding_size: Expected size of embedding (for validation)

    Returns:
        Decrypted numpy array
    """
    try:
        # Decode from base64
        encrypted_with_iv = base64.b64decode(encrypted_data)

        # Extract IV
        iv = encrypted_with_iv[:16]
        encrypted = encrypted_with_iv[16:]

        # Create cipher
        cipher = Cipher(
            algorithms.AES(_get_encryption_key()),
            modes.CBC(iv),
            backend=default_backend()
        )
        decryptor = cipher.decryptor()

        # Decrypt
        decrypted = decryptor.update(encrypted) + decryptor.finalize()

        # Remove padding
        if len(decrypted) > 0:
            padding_length = decrypted[-1]
            if padding_length < 16:
                decrypted = decrypted[:-padding_length]

        # Convert back to numpy array
        embedding = np.frombuffer(decrypted, dtype=np.float32)

        # Validate size if provided
        if embedding_size and len(embedding) != embedding_size:
            logger.warning(f"Embedding size mismatch: expected {embedding_size}, got {len(embedding)}")

        return embedding

    except Exception as e:
        logger.error(f"Error decrypting embedding: {str(e)}")
        raise


def encrypt_sensitive_data(data: str) -> str:
    """
    Encrypt sensitive string data

    Args:
        data: String data to encrypt

    Returns:
        Base64 encoded encrypted data
    """
    try:
        data_bytes = data.encode('utf-8')

        # Generate IV
        iv = os.urandom(16)

        # Create cipher
        cipher = Cipher(
            algorithms.AES(_get_encryption_key()),
            modes.CBC(iv),
            backend=default_backend()
        )
        encryptor = cipher.encryptor()

        # Pad data
        padding_length = 16 - (len(data_bytes) % 16)
        if padding_length != 16:
            data_bytes += bytes([padding_length]) * padding_length

        # Encrypt
        encrypted = encryptor.update(data_bytes) + encryptor.finalize()

        # Combine IV and encrypted data
        encrypted_with_iv = iv + encrypted

        return base64.b64encode(encrypted_with_iv).decode('utf-8')

    except Exception as e:
        logger.error(f"Error encrypting data: {str(e)}")
        raise


def decrypt_sensitive_data(encrypted_data: str) -> str:
    """
    Decrypt sensitive string data

    Args:
        encrypted_data: Base64 encoded encrypted data

    Returns:
        Decrypted string
    """
    try:
        # Decode from base64
        encrypted_with_iv = base64.b64decode(encrypted_data)

        # Extract IV
        iv = encrypted_with_iv[:16]
        encrypted = encrypted_with_iv[16:]

        # Create cipher
        cipher = Cipher(
            algorithms.AES(_get_encryption_key()),
            modes.CBC(iv),
            backend=default_backend()
        )
        decryptor = cipher.decryptor()

        # Decrypt
        decrypted = decryptor.update(encrypted) + decryptor.finalize()

        # Remove padding
        if len(decrypted) > 0:
            padding_length = decrypted[-1]
            if padding_length < 16:
                decrypted = decrypted[:-padding_length]

        return decrypted.decode('utf-8')

    except Exception as e:
        logger.error(f"Error decrypting data: {str(e)}")
        raise


def hash_user_id(user_id: str) -> str:
    """
    Create secure hash of user ID for indexing

    Args:
        user_id: User ID to hash

    Returns:
        Hashed user ID
    """
    digest = hashes.Hash(hashes.SHA256(), backend=default_backend())
    digest.update(user_id.encode('utf-8'))
    digest.update(SALT)
    return base64.urlsafe_b64encode(digest.finalize()).decode('utf-8')[:32]