"""
Password Policy Value Object
Following DDD Architecture Document Section 2.2
Encapsulates password validation rules and strength requirements
"""

from dataclasses import dataclass
from typing import List
import re

from ....shared.domain_base import ValueObject, BusinessRuleViolation


@dataclass(frozen=True)
class PasswordPolicy(ValueObject):
    """
    Password Policy value object
    Defines and validates password strength requirements

    Default requirements:
    - Minimum 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character (optional)
    """
    min_length: int = 8
    require_uppercase: bool = True
    require_lowercase: bool = True
    require_digit: bool = True
    require_special: bool = False
    max_length: int = 100

    def validate(self, password: str) -> List[str]:
        """
        Validate password against policy
        Returns list of validation errors (empty if valid)
        """
        errors = []

        if not password:
            errors.append("Password is required")
            return errors

        if len(password) < self.min_length:
            errors.append(f"Password must be at least {self.min_length} characters")

        if len(password) > self.max_length:
            errors.append(f"Password must not exceed {self.max_length} characters")

        if self.require_uppercase and not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter")

        if self.require_lowercase and not re.search(r'[a-z]', password):
            errors.append("Password must contain at least one lowercase letter")

        if self.require_digit and not re.search(r'[0-9]', password):
            errors.append("Password must contain at least one digit")

        if self.require_special and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("Password must contain at least one special character")

        return errors

    def is_valid(self, password: str) -> bool:
        """Check if password meets policy requirements"""
        return len(self.validate(password)) == 0

    def assert_valid(self, password: str):
        """
        Assert password is valid, raise exception if not
        Raises BusinessRuleViolation with validation errors
        """
        errors = self.validate(password)
        if errors:
            raise BusinessRuleViolation(f"Password validation failed: {'; '.join(errors)}")

    def calculate_strength(self, password: str) -> int:
        """
        Calculate password strength score (0-100)
        Based on length, character diversity, and entropy
        """
        if not password:
            return 0

        score = 0

        # Length contribution (up to 40 points)
        length_score = min(len(password) * 3, 40)
        score += length_score

        # Character variety (up to 40 points)
        if re.search(r'[a-z]', password):
            score += 10
        if re.search(r'[A-Z]', password):
            score += 10
        if re.search(r'[0-9]', password):
            score += 10
        if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            score += 10

        # Unique characters (up to 20 points)
        unique_chars = len(set(password))
        unique_score = min(unique_chars * 2, 20)
        score += unique_score

        return min(score, 100)

    def get_strength_label(self, password: str) -> str:
        """Get human-readable strength label"""
        strength = self.calculate_strength(password)

        if strength >= 80:
            return "Strong"
        elif strength >= 60:
            return "Good"
        elif strength >= 40:
            return "Fair"
        elif strength >= 20:
            return "Weak"
        else:
            return "Very Weak"

    def to_dict(self) -> dict:
        """Convert to dictionary representation"""
        return {
            'min_length': self.min_length,
            'require_uppercase': self.require_uppercase,
            'require_lowercase': self.require_lowercase,
            'require_digit': self.require_digit,
            'require_special': self.require_special,
            'max_length': self.max_length
        }


# Default password policy for the system
DEFAULT_PASSWORD_POLICY = PasswordPolicy(
    min_length=8,
    require_uppercase=True,
    require_lowercase=True,
    require_digit=True,
    require_special=False,
    max_length=100
)

# Strong password policy for admin users
ADMIN_PASSWORD_POLICY = PasswordPolicy(
    min_length=12,
    require_uppercase=True,
    require_lowercase=True,
    require_digit=True,
    require_special=True,
    max_length=100
)
