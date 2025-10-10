"""
OtpCode Entity
Following DDD Architecture Document Section 2.2
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, List
from uuid import UUID, uuid4
from enum import Enum
import random
import string
import hashlib

from ....shared.domain_base import Entity, BusinessRuleViolation


class OtpPurpose(str, Enum):
    """Purpose of OTP code"""
    LOGIN = "login"
    TRANSACTION = "transaction"
    PASSWORD_RESET = "password_reset"
    EMAIL_VERIFICATION = "email_verification"
    PHONE_VERIFICATION = "phone_verification"
    TWO_FACTOR_AUTH = "two_factor_auth"
    ORDER_CONFIRMATION = "order_confirmation"
    DELIVERY_CONFIRMATION = "delivery_confirmation"


class OtpStatus(str, Enum):
    """OTP code status"""
    PENDING = "pending"
    VERIFIED = "verified"
    EXPIRED = "expired"
    FAILED = "failed"  # Too many failed attempts


class OtpDeliveryMethod(str, Enum):
    """How OTP was delivered"""
    SMS = "sms"
    EMAIL = "email"
    VOICE = "voice"
    AUTHENTICATOR_APP = "authenticator_app"


@dataclass
class OtpCode(Entity):
    """
    OtpCode Entity - One-time passwords for verification
    As defined in DDD_ARCHITECTURE_REFACTORING.md Section 2.2
    """
    user_id: UUID = field(default_factory=uuid4)

    # OTP Information
    code_hash: str = ""  # Hashed OTP value
    purpose: OtpPurpose = OtpPurpose.LOGIN
    status: OtpStatus = OtpStatus.PENDING

    # Delivery Information
    delivery_method: OtpDeliveryMethod = OtpDeliveryMethod.SMS
    delivery_address: str = ""  # Phone number or email
    delivered_at: Optional[datetime] = None
    delivery_attempts: int = 0

    # Validity
    expires_at: datetime = field(default_factory=lambda: datetime.utcnow() + timedelta(minutes=5))
    valid_from: datetime = field(default_factory=datetime.utcnow)

    # Verification
    verified_at: Optional[datetime] = None
    verification_attempts: int = 0
    max_verification_attempts: int = 3

    # Security
    ip_address: Optional[str] = None  # IP that requested OTP
    user_agent: Optional[str] = None
    session_id: Optional[str] = None  # Session that requested OTP

    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        user_id: UUID,
        purpose: OtpPurpose,
        delivery_method: OtpDeliveryMethod,
        delivery_address: str,
        length: int = 6,
        expires_in: timedelta = timedelta(minutes=5),
        numeric_only: bool = True
    ) -> tuple['OtpCode', str]:
        """Factory method to create a new OTP code"""
        # Generate OTP code
        if numeric_only:
            raw_code = ''.join(random.choices(string.digits, k=length))
        else:
            raw_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

        # Hash the code
        code_hash = hashlib.sha256(raw_code.encode()).hexdigest()

        otp = cls(
            user_id=user_id,
            code_hash=code_hash,
            purpose=purpose,
            delivery_method=delivery_method,
            delivery_address=delivery_address,
            expires_at=datetime.utcnow() + expires_in
        )

        return otp, raw_code

    @classmethod
    def create_totp(
        cls,
        user_id: UUID,
        purpose: OtpPurpose,
        secret: str,
        time_step: int = 30
    ) -> 'OtpCode':
        """Create TOTP-based OTP (for authenticator apps)"""
        # This would integrate with a TOTP library in production
        # For now, we'll create a placeholder
        otp = cls(
            user_id=user_id,
            purpose=purpose,
            delivery_method=OtpDeliveryMethod.AUTHENTICATOR_APP,
            delivery_address="authenticator_app",
            expires_at=datetime.utcnow() + timedelta(seconds=time_step)
        )
        otp.metadata['time_step'] = time_step
        otp.metadata['secret'] = secret  # Would be encrypted in production

        return otp

    def verify(self, provided_code: str) -> bool:
        """Verify the provided OTP code"""
        if not self.is_valid():
            return False

        self.verification_attempts += 1

        # Check if too many failed attempts
        if self.verification_attempts > self.max_verification_attempts:
            self.status = OtpStatus.FAILED
            self.mark_as_modified()
            return False

        # Verify the code
        provided_hash = hashlib.sha256(provided_code.encode()).hexdigest()
        is_correct = provided_hash == self.code_hash

        if is_correct:
            self.status = OtpStatus.VERIFIED
            self.verified_at = datetime.utcnow()
        elif self.verification_attempts >= self.max_verification_attempts:
            self.status = OtpStatus.FAILED

        self.mark_as_modified()
        return is_correct

    def is_valid(self) -> bool:
        """Check if OTP is valid for verification"""
        if self.status != OtpStatus.PENDING:
            return False

        now = datetime.utcnow()

        # Check if expired
        if now > self.expires_at:
            self.status = OtpStatus.EXPIRED
            self.mark_as_modified()
            return False

        # Check if not yet valid
        if now < self.valid_from:
            return False

        # Check if too many attempts
        if self.verification_attempts >= self.max_verification_attempts:
            self.status = OtpStatus.FAILED
            self.mark_as_modified()
            return False

        return True

    def mark_delivered(self):
        """Mark OTP as delivered"""
        self.delivered_at = datetime.utcnow()
        self.delivery_attempts += 1
        self.mark_as_modified()

    def resend(self, new_expires_in: timedelta = timedelta(minutes=5)) -> tuple['OtpCode', str]:
        """Create a new OTP to replace this one"""
        if self.delivery_attempts >= 3:
            raise BusinessRuleViolation("Maximum resend attempts reached")

        # Create new OTP with same settings
        new_otp, raw_code = OtpCode.create(
            user_id=self.user_id,
            purpose=self.purpose,
            delivery_method=self.delivery_method,
            delivery_address=self.delivery_address,
            expires_in=new_expires_in
        )

        # Mark current OTP as expired
        self.status = OtpStatus.EXPIRED
        self.mark_as_modified()

        return new_otp, raw_code

    def extend_expiration(self, additional_time: timedelta):
        """Extend OTP expiration time"""
        if self.status != OtpStatus.PENDING:
            raise BusinessRuleViolation("Can only extend pending OTPs")

        self.expires_at = self.expires_at + additional_time
        self.mark_as_modified()

    def get_time_until_expiry(self) -> timedelta:
        """Get time remaining until OTP expires"""
        return self.expires_at - datetime.utcnow()

    def is_expired(self) -> bool:
        """Check if OTP is expired"""
        return datetime.utcnow() > self.expires_at

    def can_resend(self) -> bool:
        """Check if OTP can be resent"""
        return self.delivery_attempts < 3

    def get_masked_delivery_address(self) -> str:
        """Get masked delivery address for display"""
        if self.delivery_method == OtpDeliveryMethod.SMS:
            # Mask phone number: +1234****89
            if len(self.delivery_address) > 6:
                return f"{self.delivery_address[:5]}****{self.delivery_address[-2:]}"

        elif self.delivery_method == OtpDeliveryMethod.EMAIL:
            # Mask email: u****r@example.com
            if '@' in self.delivery_address:
                parts = self.delivery_address.split('@')
                if len(parts[0]) > 2:
                    masked_user = f"{parts[0][0]}****{parts[0][-1]}"
                else:
                    masked_user = parts[0]
                return f"{masked_user}@{parts[1]}"

        return "****"

    def update_session_info(
        self,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        session_id: Optional[str] = None
    ):
        """Update session information"""
        if ip_address:
            self.ip_address = ip_address
        if user_agent:
            self.user_agent = user_agent
        if session_id:
            self.session_id = session_id
        self.mark_as_modified()

    def validate(self) -> List[str]:
        """Validate OTP data"""
        errors = []

        if not self.user_id:
            errors.append("User ID is required")

        if not self.code_hash:
            errors.append("Code hash is required")

        if not self.delivery_address:
            errors.append("Delivery address is required")

        if self.expires_at <= datetime.utcnow():
            errors.append("Expiration must be in the future")

        if self.max_verification_attempts < 1:
            errors.append("Max verification attempts must be at least 1")

        if self.delivery_method == OtpDeliveryMethod.EMAIL and '@' not in self.delivery_address:
            errors.append("Invalid email address")

        return errors