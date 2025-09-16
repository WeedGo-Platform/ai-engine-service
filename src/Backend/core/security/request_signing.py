"""
Request Signing and Verification with HMAC-SHA256
Implements secure request signing for API integrity and authentication
"""

import hmac
import hashlib
import base64
import time
import json
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional, List, Tuple
from urllib.parse import urlparse, parse_qs
import logging
from fastapi import Request, HTTPException, status
from starlette.datastructures import Headers
import asyncio

logger = logging.getLogger(__name__)


class RequestSigner:
    """
    HMAC-SHA256 Request Signing Implementation

    Features:
    - Request body integrity verification
    - Timestamp validation to prevent replay attacks
    - Nonce tracking for additional replay protection
    - Support for multiple signing algorithms
    - Request canonicalization
    - Signature versioning for key rotation
    """

    def __init__(self, config: Dict[str, Any] = None):
        """Initialize request signer"""
        self.config = config or {}

        # Signing configuration
        self.algorithm = self.config.get('algorithm', 'SHA256')
        self.signature_header = self.config.get('signature_header', 'X-Signature')
        self.timestamp_header = self.config.get('timestamp_header', 'X-Timestamp')
        self.nonce_header = self.config.get('nonce_header', 'X-Nonce')
        self.key_id_header = self.config.get('key_id_header', 'X-Key-Id')

        # Time window for valid requests (seconds)
        self.time_window = self.config.get('time_window', 300)  # 5 minutes

        # Nonce tracking (in production, use Redis)
        self.used_nonces = set()
        self.nonce_expiry = {}

        # Supported algorithms
        self.algorithms = {
            'SHA256': hashlib.sha256,
            'SHA384': hashlib.sha384,
            'SHA512': hashlib.sha512,
            'SHA3_256': hashlib.sha3_256,
            'SHA3_512': hashlib.sha3_512
        }

        # Version for signature format changes
        self.signature_version = "v1"

    def generate_signature(
        self,
        secret_key: str,
        method: str,
        path: str,
        headers: Dict[str, str],
        body: Optional[bytes] = None,
        query_params: Optional[Dict[str, Any]] = None,
        timestamp: Optional[int] = None,
        nonce: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Generate HMAC signature for a request

        Args:
            secret_key: Secret key for signing
            method: HTTP method (GET, POST, etc.)
            path: Request path
            headers: Request headers
            body: Request body bytes
            query_params: Query parameters
            timestamp: Unix timestamp (generates if not provided)
            nonce: Unique request identifier (generates if not provided)

        Returns:
            Dictionary with signature headers
        """
        # Generate timestamp if not provided
        if timestamp is None:
            timestamp = int(time.time())

        # Generate nonce if not provided
        if nonce is None:
            nonce = base64.b64encode(hashlib.sha256(
                f"{timestamp}{secret_key}{method}{path}".encode()
            ).digest()).decode()[:32]

        # Create canonical request
        canonical_request = self._create_canonical_request(
            method, path, headers, body, query_params, timestamp, nonce
        )

        # Generate signature
        signature = self._compute_signature(secret_key, canonical_request)

        # Return headers to add to request
        return {
            self.signature_header: f"{self.signature_version}:{signature}",
            self.timestamp_header: str(timestamp),
            self.nonce_header: nonce
        }

    def _create_canonical_request(
        self,
        method: str,
        path: str,
        headers: Dict[str, str],
        body: Optional[bytes],
        query_params: Optional[Dict[str, Any]],
        timestamp: int,
        nonce: str
    ) -> str:
        """
        Create canonical request string for signing

        The canonical format ensures consistent signing across different clients
        """
        parts = []

        # HTTP Method (uppercase)
        parts.append(method.upper())

        # Request path
        parts.append(path)

        # Canonicalized query string
        if query_params:
            sorted_params = sorted(query_params.items())
            query_string = "&".join([f"{k}={v}" for k, v in sorted_params])
            parts.append(query_string)
        else:
            parts.append("")

        # Canonicalized headers (subset of security-relevant headers)
        canonical_headers = self._canonicalize_headers(headers)
        parts.append(canonical_headers)

        # Timestamp
        parts.append(str(timestamp))

        # Nonce
        parts.append(nonce)

        # Body hash (for integrity)
        if body:
            body_hash = base64.b64encode(
                hashlib.sha256(body).digest()
            ).decode()
            parts.append(body_hash)
        else:
            parts.append("")

        # Join with newlines
        canonical_request = "\n".join(parts)

        logger.debug(f"Canonical request:\n{canonical_request}")

        return canonical_request

    def _canonicalize_headers(self, headers: Dict[str, str]) -> str:
        """
        Canonicalize headers for signing

        Only includes specific security-relevant headers
        """
        # Headers to include in signature
        signed_headers = [
            'content-type',
            'content-length',
            'host',
            'x-api-version',
            'x-client-id'
        ]

        canonical = []
        for header in signed_headers:
            value = headers.get(header, headers.get(header.lower(), ""))
            if value:
                canonical.append(f"{header.lower()}:{value.strip()}")

        return "\n".join(sorted(canonical))

    def _compute_signature(self, secret_key: str, message: str) -> str:
        """Compute HMAC signature"""
        # Get hash function
        hash_func = self.algorithms.get(self.algorithm, hashlib.sha256)

        # Compute HMAC
        signature = hmac.new(
            secret_key.encode(),
            message.encode(),
            hash_func
        ).digest()

        # Base64 encode
        return base64.b64encode(signature).decode()

    async def verify_signature(
        self,
        request: Request,
        secret_key: str,
        check_replay: bool = True
    ) -> bool:
        """
        Verify request signature

        Args:
            request: FastAPI request object
            secret_key: Secret key for verification
            check_replay: Whether to check for replay attacks

        Returns:
            True if signature is valid

        Raises:
            HTTPException if signature is invalid
        """
        # Extract signature headers
        signature = request.headers.get(self.signature_header)
        timestamp_str = request.headers.get(self.timestamp_header)
        nonce = request.headers.get(self.nonce_header)

        if not all([signature, timestamp_str, nonce]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing signature headers"
            )

        # Parse signature version
        if ':' in signature:
            version, sig_value = signature.split(':', 1)
            if version != self.signature_version:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Unsupported signature version: {version}"
                )
        else:
            sig_value = signature

        # Verify timestamp
        try:
            timestamp = int(timestamp_str)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid timestamp"
            )

        # Check timestamp window
        current_time = int(time.time())
        if abs(current_time - timestamp) > self.time_window:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Request timestamp outside valid window"
            )

        # Check for replay attack
        if check_replay:
            if not await self._check_nonce(nonce, timestamp):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Duplicate request detected (nonce reuse)"
                )

        # Get request body
        body = await request.body() if request.method in ["POST", "PUT", "PATCH"] else None

        # Parse query parameters
        query_params = dict(request.query_params) if request.query_params else None

        # Create canonical request
        canonical_request = self._create_canonical_request(
            method=request.method,
            path=request.url.path,
            headers=dict(request.headers),
            body=body,
            query_params=query_params,
            timestamp=timestamp,
            nonce=nonce
        )

        # Compute expected signature
        expected_signature = self._compute_signature(secret_key, canonical_request)

        # Constant-time comparison
        if not hmac.compare_digest(sig_value, expected_signature):
            logger.warning(f"Invalid signature for request: {request.url.path}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid signature"
            )

        logger.debug(f"Valid signature for request: {request.url.path}")
        return True

    async def _check_nonce(self, nonce: str, timestamp: int) -> bool:
        """
        Check if nonce has been used (replay protection)

        Args:
            nonce: Request nonce
            timestamp: Request timestamp

        Returns:
            True if nonce is new, False if it's a replay
        """
        # Clean up old nonces
        await self._cleanup_nonces()

        # Check if nonce was used
        if nonce in self.used_nonces:
            logger.warning(f"Nonce reuse detected: {nonce}")
            return False

        # Track nonce
        self.used_nonces.add(nonce)
        self.nonce_expiry[nonce] = timestamp + self.time_window

        return True

    async def _cleanup_nonces(self):
        """Clean up expired nonces"""
        current_time = int(time.time())
        expired = []

        for nonce, expiry in self.nonce_expiry.items():
            if expiry < current_time:
                expired.append(nonce)

        for nonce in expired:
            self.used_nonces.discard(nonce)
            del self.nonce_expiry[nonce]


class WebhookSigner:
    """
    Webhook signature generation and verification

    Used for signing outgoing webhooks and verifying incoming webhooks
    """

    def __init__(self, config: Dict[str, Any] = None):
        """Initialize webhook signer"""
        self.config = config or {}
        self.algorithm = self.config.get('algorithm', 'SHA256')
        self.header_name = self.config.get('header_name', 'X-Webhook-Signature')
        self.include_timestamp = self.config.get('include_timestamp', True)

    def sign_webhook(
        self,
        secret: str,
        payload: Dict[str, Any],
        event_type: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Sign webhook payload

        Args:
            secret: Webhook secret
            payload: Webhook payload dictionary
            event_type: Optional event type

        Returns:
            Headers to include with webhook
        """
        # Add metadata
        webhook_data = {
            'payload': payload,
            'timestamp': int(time.time()) if self.include_timestamp else None,
            'event_type': event_type
        }

        # Serialize to JSON (canonical)
        json_payload = json.dumps(webhook_data, sort_keys=True, separators=(',', ':'))

        # Compute signature
        if self.algorithm == 'SHA256':
            signature = hmac.new(
                secret.encode(),
                json_payload.encode(),
                hashlib.sha256
            ).hexdigest()
        else:
            raise ValueError(f"Unsupported algorithm: {self.algorithm}")

        return {
            self.header_name: f"sha256={signature}",
            'Content-Type': 'application/json',
            'X-Webhook-Timestamp': str(webhook_data['timestamp']) if self.include_timestamp else None,
            'X-Webhook-Event': event_type or 'webhook'
        }

    def verify_webhook(
        self,
        secret: str,
        signature: str,
        body: bytes,
        timestamp: Optional[str] = None,
        max_age_seconds: int = 300
    ) -> bool:
        """
        Verify webhook signature

        Args:
            secret: Webhook secret
            signature: Signature from webhook header
            body: Raw webhook body bytes
            timestamp: Optional timestamp header
            max_age_seconds: Maximum age for webhook

        Returns:
            True if signature is valid
        """
        # Check timestamp if provided
        if timestamp and self.include_timestamp:
            try:
                webhook_time = int(timestamp)
                current_time = int(time.time())
                if abs(current_time - webhook_time) > max_age_seconds:
                    logger.warning("Webhook timestamp outside valid window")
                    return False
            except ValueError:
                logger.warning("Invalid webhook timestamp")
                return False

        # Parse signature format (e.g., "sha256=...")
        if '=' in signature:
            algo, sig_value = signature.split('=', 1)
            if algo != 'sha256':
                logger.warning(f"Unsupported webhook algorithm: {algo}")
                return False
        else:
            sig_value = signature

        # Compute expected signature
        expected = hmac.new(
            secret.encode(),
            body,
            hashlib.sha256
        ).hexdigest()

        # Constant-time comparison
        return hmac.compare_digest(sig_value, expected)


class SignedURLGenerator:
    """
    Generate and verify signed URLs for temporary access
    """

    def __init__(self, secret_key: str):
        """Initialize with secret key"""
        self.secret_key = secret_key

    def generate_signed_url(
        self,
        base_url: str,
        params: Dict[str, Any] = None,
        expires_in: int = 3600
    ) -> str:
        """
        Generate a signed URL with expiration

        Args:
            base_url: Base URL to sign
            params: Query parameters
            expires_in: Expiration time in seconds

        Returns:
            Signed URL
        """
        # Add expiration timestamp
        expires_at = int(time.time()) + expires_in

        # Build parameters
        all_params = params.copy() if params else {}
        all_params['expires'] = expires_at

        # Sort parameters for consistent signing
        sorted_params = sorted(all_params.items())

        # Create string to sign
        parsed = urlparse(base_url)
        to_sign = f"{parsed.path}\n"
        to_sign += "\n".join([f"{k}={v}" for k, v in sorted_params])

        # Generate signature
        signature = hmac.new(
            self.secret_key.encode(),
            to_sign.encode(),
            hashlib.sha256
        ).hexdigest()

        # Add signature to parameters
        all_params['signature'] = signature

        # Build final URL
        query_string = "&".join([f"{k}={v}" for k, v in all_params.items()])

        if '?' in base_url:
            return f"{base_url}&{query_string}"
        else:
            return f"{base_url}?{query_string}"

    def verify_signed_url(self, url: str) -> bool:
        """
        Verify a signed URL

        Args:
            url: Signed URL to verify

        Returns:
            True if URL is valid and not expired
        """
        parsed = urlparse(url)
        params = parse_qs(parsed.query)

        # Extract signature and expiration
        signature = params.pop('signature', [None])[0]
        expires = params.pop('expires', [None])[0]

        if not signature or not expires:
            return False

        # Check expiration
        try:
            expires_at = int(expires)
            if expires_at < int(time.time()):
                logger.warning("Signed URL has expired")
                return False
        except ValueError:
            return False

        # Reconstruct parameters
        clean_params = {k: v[0] for k, v in params.items()}
        clean_params['expires'] = expires_at

        # Recreate string to sign
        sorted_params = sorted(clean_params.items())
        to_sign = f"{parsed.path}\n"
        to_sign += "\n".join([f"{k}={v}" for k, v in sorted_params])

        # Verify signature
        expected = hmac.new(
            self.secret_key.encode(),
            to_sign.encode(),
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(signature, expected)


# FastAPI middleware for request signing
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


class RequestSigningMiddleware(BaseHTTPMiddleware):
    """
    Middleware to verify request signatures
    """

    def __init__(self, app, signer: RequestSigner, get_secret_key, excluded_paths: List[str] = None):
        """
        Initialize middleware

        Args:
            app: FastAPI app
            signer: RequestSigner instance
            get_secret_key: Callable to get secret key for request
            excluded_paths: Paths to exclude from signing
        """
        super().__init__(app)
        self.signer = signer
        self.get_secret_key = get_secret_key
        self.excluded_paths = excluded_paths or ['/health', '/docs', '/openapi.json']

    async def dispatch(self, request: Request, call_next):
        """Process request"""
        # Check if path is excluded
        if any(request.url.path.startswith(path) for path in self.excluded_paths):
            return await call_next(request)

        # Check if signature headers are present
        if not request.headers.get(self.signer.signature_header):
            # Optional: Allow unsigned requests for public endpoints
            # return await call_next(request)
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Request signature required"}
            )

        # Get secret key for this request
        try:
            # Extract key ID from header
            key_id = request.headers.get(self.signer.key_id_header)
            if not key_id:
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Key ID required"}
                )

            # Get secret key
            secret_key = await self.get_secret_key(key_id)
            if not secret_key:
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Invalid key ID"}
                )

            # Verify signature
            await self.signer.verify_signature(request, secret_key)

        except HTTPException as e:
            return JSONResponse(
                status_code=e.status_code,
                content={"detail": e.detail}
            )
        except Exception as e:
            logger.error(f"Signature verification error: {e}")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": "Internal server error"}
            )

        # Process request
        response = await call_next(request)
        return response


# Global instances
_request_signer: Optional[RequestSigner] = None
_webhook_signer: Optional[WebhookSigner] = None


def get_request_signer() -> RequestSigner:
    """Get global request signer instance"""
    global _request_signer
    if _request_signer is None:
        from core.config_loader import get_config
        config = get_config()
        _request_signer = RequestSigner(config.get_security_config())
    return _request_signer


def get_webhook_signer() -> WebhookSigner:
    """Get global webhook signer instance"""
    global _webhook_signer
    if _webhook_signer is None:
        from core.config_loader import get_config
        config = get_config()
        _webhook_signer = WebhookSigner(config.get_security_config())
    return _webhook_signer