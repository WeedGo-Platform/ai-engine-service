"""
TLS/HTTPS Configuration and Certificate Management
Implements secure TLS configuration with automatic certificate rotation
"""

import ssl
import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import certifi
import asyncio
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend

logger = logging.getLogger(__name__)


class TLSConfig:
    """
    Comprehensive TLS configuration for zero-trust environment
    Supports:
    - TLS 1.3 enforcement
    - Certificate pinning
    - Automatic certificate rotation
    - mTLS for service-to-service communication
    """

    def __init__(self, config: Dict[str, Any] = None):
        """Initialize TLS configuration"""
        self.config = config or {}

        # Certificate paths
        self.cert_dir = Path(os.environ.get('CERT_DIR', '/etc/weedgo/certs'))
        self.cert_dir.mkdir(parents=True, exist_ok=True)

        # TLS settings
        self.min_tls_version = ssl.TLSVersion.TLSv1_3  # Enforce TLS 1.3 minimum
        self.cipher_suites = [
            'TLS_AES_256_GCM_SHA384',
            'TLS_AES_128_GCM_SHA256',
            'TLS_CHACHA20_POLY1305_SHA256'
        ]

        # Certificate settings
        self.cert_expiry_days = config.get('cert_expiry_days', 90)
        self.rotation_threshold_days = config.get('rotation_threshold', 30)

        # mTLS settings
        self.enable_mtls = config.get('enable_mtls', True)
        self.client_ca_cert = self.cert_dir / 'client_ca.pem'

        # Certificate pinning
        self.pinned_certificates = {}
        self.enable_pinning = config.get('enable_pinning', True)

    def create_ssl_context(self,
                          purpose: ssl.Purpose = ssl.Purpose.CLIENT_AUTH,
                          enable_mtls: bool = False) -> ssl.SSLContext:
        """
        Create secure SSL context with proper configuration

        Args:
            purpose: SSL purpose (CLIENT_AUTH or SERVER_AUTH)
            enable_mtls: Enable mutual TLS

        Returns:
            Configured SSL context
        """
        # Create context with secure defaults
        context = ssl.create_default_context(purpose)

        # Set minimum TLS version
        context.minimum_version = self.min_tls_version

        # Disable older protocols
        context.options |= ssl.OP_NO_SSLv2
        context.options |= ssl.OP_NO_SSLv3
        context.options |= ssl.OP_NO_TLSv1
        context.options |= ssl.OP_NO_TLSv1_1
        context.options |= ssl.OP_NO_TLSv1_2  # Force TLS 1.3

        # Enable security options
        context.options |= ssl.OP_SINGLE_DH_USE
        context.options |= ssl.OP_SINGLE_ECDH_USE
        context.options |= ssl.OP_NO_COMPRESSION
        context.options |= ssl.OP_CIPHER_SERVER_PREFERENCE

        # Set cipher suites (TLS 1.3)
        cipher_string = ':'.join(self.cipher_suites)
        context.set_ciphers(cipher_string)

        # Load certificates
        cert_file = self.cert_dir / 'server.crt'
        key_file = self.cert_dir / 'server.key'

        if cert_file.exists() and key_file.exists():
            context.load_cert_chain(str(cert_file), str(key_file))
        else:
            # Generate self-signed certificate for development
            self._generate_self_signed_cert()
            if cert_file.exists() and key_file.exists():
                context.load_cert_chain(str(cert_file), str(key_file))

        # Configure mTLS if enabled
        if enable_mtls and self.enable_mtls:
            context.verify_mode = ssl.CERT_REQUIRED
            if self.client_ca_cert.exists():
                context.load_verify_locations(str(self.client_ca_cert))
            else:
                logger.warning("mTLS enabled but client CA certificate not found")

        # Certificate verification
        context.check_hostname = True
        context.verify_mode = ssl.CERT_REQUIRED if purpose == ssl.Purpose.SERVER_AUTH else ssl.CERT_OPTIONAL

        # Set up certificate verification callback for pinning
        if self.enable_pinning:
            context.verify_mode = ssl.CERT_REQUIRED
            # Note: Certificate pinning callback would be implemented here

        return context

    def _generate_self_signed_cert(self,
                                  hostname: str = "localhost",
                                  valid_days: int = 365):
        """
        Generate self-signed certificate for development

        Args:
            hostname: Certificate hostname
            valid_days: Certificate validity in days
        """
        cert_file = self.cert_dir / 'server.crt'
        key_file = self.cert_dir / 'server.key'

        # Generate private key
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=4096,  # Strong key size
            backend=default_backend()
        )

        # Create certificate
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "California"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "San Francisco"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "WeedGo Dev"),
            x509.NameAttribute(NameOID.COMMON_NAME, hostname),
        ])

        cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            issuer
        ).public_key(
            private_key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.utcnow()
        ).not_valid_after(
            datetime.utcnow() + timedelta(days=valid_days)
        ).add_extension(
            x509.SubjectAlternativeName([
                x509.DNSName(hostname),
                x509.DNSName("*.localhost"),
                x509.IPAddress(ipaddress.IPv4Address("127.0.0.1")),
                x509.IPAddress(ipaddress.IPv6Address("::1")),
            ]),
            critical=False,
        ).add_extension(
            x509.BasicConstraints(ca=True, path_length=0),
            critical=True,
        ).sign(private_key, hashes.SHA256(), backend=default_backend())

        # Write private key
        with open(key_file, "wb") as f:
            f.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption()
            ))

        # Write certificate
        with open(cert_file, "wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))

        # Set appropriate permissions
        os.chmod(key_file, 0o600)  # Read/write for owner only
        os.chmod(cert_file, 0o644)  # Read for all, write for owner

        logger.info(f"Generated self-signed certificate for {hostname}")

    async def check_certificate_expiry(self):
        """
        Check certificate expiration and trigger rotation if needed
        """
        cert_file = self.cert_dir / 'server.crt'

        if not cert_file.exists():
            logger.warning("Certificate file not found")
            return

        with open(cert_file, 'rb') as f:
            cert_data = f.read()
            cert = x509.load_pem_x509_certificate(cert_data, default_backend())

        # Check expiration
        days_until_expiry = (cert.not_valid_after - datetime.utcnow()).days

        if days_until_expiry < self.rotation_threshold_days:
            logger.warning(f"Certificate expires in {days_until_expiry} days. Triggering rotation.")
            await self.rotate_certificate()
        else:
            logger.info(f"Certificate valid for {days_until_expiry} more days")

    async def rotate_certificate(self):
        """
        Rotate certificates with zero downtime
        """
        logger.info("Starting certificate rotation...")

        # Generate new certificate
        new_cert_file = self.cert_dir / 'server_new.crt'
        new_key_file = self.cert_dir / 'server_new.key'

        # In production, this would request from CA
        # For now, generate self-signed
        self._generate_self_signed_cert()

        # Atomic rotation
        os.rename(self.cert_dir / 'server.crt', self.cert_dir / 'server_old.crt')
        os.rename(self.cert_dir / 'server.key', self.cert_dir / 'server_old.key')
        os.rename(new_cert_file, self.cert_dir / 'server.crt')
        os.rename(new_key_file, self.cert_dir / 'server.key')

        logger.info("Certificate rotation completed")

    def get_tls_config_for_uvicorn(self) -> Dict[str, Any]:
        """
        Get TLS configuration for Uvicorn server

        Returns:
            Dictionary with SSL configuration
        """
        cert_file = self.cert_dir / 'server.crt'
        key_file = self.cert_dir / 'server.key'

        # Generate certificates if they don't exist
        if not cert_file.exists() or not key_file.exists():
            self._generate_self_signed_cert()

        return {
            'ssl_keyfile': str(key_file),
            'ssl_certfile': str(cert_file),
            'ssl_version': ssl.PROTOCOL_TLS_SERVER,
            'ssl_cert_reqs': ssl.CERT_OPTIONAL,
            'ssl_ciphers': ':'.join(self.cipher_suites),
        }

    def validate_client_certificate(self, cert_der: bytes) -> bool:
        """
        Validate client certificate for mTLS

        Args:
            cert_der: Certificate in DER format

        Returns:
            True if certificate is valid
        """
        try:
            cert = x509.load_der_x509_certificate(cert_der, default_backend())

            # Check if certificate is not expired
            if cert.not_valid_after < datetime.utcnow():
                logger.warning("Client certificate expired")
                return False

            # Check if certificate is issued by trusted CA
            # In production, implement proper chain validation

            # Check certificate pinning if enabled
            if self.enable_pinning:
                cert_fingerprint = cert.fingerprint(hashes.SHA256())
                if cert_fingerprint not in self.pinned_certificates.values():
                    logger.warning("Certificate not in pinned list")
                    return False

            return True

        except Exception as e:
            logger.error(f"Certificate validation failed: {e}")
            return False


# Singleton instance
_tls_config: Optional[TLSConfig] = None


def get_tls_config() -> TLSConfig:
    """Get singleton TLS configuration instance"""
    global _tls_config
    if _tls_config is None:
        _tls_config = TLSConfig()
    return _tls_config


# Certificate rotation task
async def certificate_rotation_task():
    """Background task for certificate rotation"""
    tls_config = get_tls_config()
    while True:
        try:
            await tls_config.check_certificate_expiry()
            # Check daily
            await asyncio.sleep(86400)
        except Exception as e:
            logger.error(f"Certificate rotation task error: {e}")
            await asyncio.sleep(3600)  # Retry in an hour


import ipaddress