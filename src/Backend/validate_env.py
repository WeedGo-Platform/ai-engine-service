#!/usr/bin/env python3
"""
Environment Configuration Validator
Validates that all required environment variables are set correctly
"""

import os
import sys
from pathlib import Path
from typing import List, Tuple, Dict

# ANSI color codes for terminal output
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
RED = '\033[0;31m'
BLUE = '\033[0;34m'
NC = '\033[0m'  # No Color

# Required variables for all environments
REQUIRED_COMMON = [
    'ENVIRONMENT',
    'DB_HOST',
    'DB_PORT',
    'DB_NAME',
    'DB_USER',
    'DB_PASSWORD',
    'JWT_SECRET_KEY',
    'CORS_ALLOWED_ORIGINS',
]

# Required variables per environment
REQUIRED_PER_ENV = {
    'development': [],
    'test': [],
    'uat': [
        'UPSTASH_REDIS_REST_URL',
        'UPSTASH_REDIS_REST_TOKEN',
    ],
    'beta': [
        'UPSTASH_REDIS_REST_URL',
        'UPSTASH_REDIS_REST_TOKEN',
    ],
    'production': [
        'UPSTASH_REDIS_REST_URL',
        'UPSTASH_REDIS_REST_TOKEN',
        'SECRET_KEY',
    ],
}

# Variables that should NOT contain placeholder values
NO_PLACEHOLDER_VARS = [
    'DB_PASSWORD',
    'JWT_SECRET_KEY',
    'SECRET_KEY',
]

PLACEHOLDER_INDICATORS = [
    'REPLACE_WITH_',
    'CHANGE_ME',
    'your_',
    'example.com',
]

def check_placeholder(var_name: str, value: str) -> bool:
    """Check if a value contains placeholder text"""
    if not value:
        return False

    for indicator in PLACEHOLDER_INDICATORS:
        if indicator in value:
            return True
    return False

def validate_environment() -> Tuple[bool, List[str], List[str]]:
    """
    Validate environment configuration
    Returns: (is_valid, errors, warnings)
    """
    errors = []
    warnings = []

    # Check ENVIRONMENT variable
    env = os.getenv('ENVIRONMENT', 'development')
    print(f"{BLUE}Validating environment: {env}{NC}")
    print()

    # Get required variables for this environment
    required_vars = REQUIRED_COMMON + REQUIRED_PER_ENV.get(env, [])

    # Check required variables
    print(f"{BLUE}Checking required variables...{NC}")
    for var in required_vars:
        value = os.getenv(var)

        if not value:
            errors.append(f"Missing required variable: {var}")
            print(f"  {RED}✗{NC} {var}: MISSING")
        elif var in NO_PLACEHOLDER_VARS and check_placeholder(var, value):
            errors.append(f"Variable contains placeholder: {var}")
            print(f"  {RED}✗{NC} {var}: Contains placeholder value")
        else:
            # Truncate long values for display
            display_value = value if len(value) < 40 else f"{value[:37]}..."
            # Mask sensitive values
            if any(sensitive in var for sensitive in ['PASSWORD', 'SECRET', 'TOKEN', 'KEY']):
                display_value = '***' + value[-4:] if len(value) > 4 else '***'
            print(f"  {GREEN}✓{NC} {var}: {display_value}")

    print()

    # Check CORS configuration
    print(f"{BLUE}Checking CORS configuration...{NC}")
    cors_origins = os.getenv('CORS_ALLOWED_ORIGINS', '')
    if not cors_origins:
        errors.append("CORS_ALLOWED_ORIGINS is empty")
        print(f"  {RED}✗{NC} CORS_ALLOWED_ORIGINS: EMPTY (CORS will block all requests!)")
    else:
        origins = cors_origins.split(';') if ';' in cors_origins else cors_origins.split(',')
        origins = [o.strip() for o in origins if o.strip()]
        print(f"  {GREEN}✓{NC} CORS_ALLOWED_ORIGINS: {len(origins)} origins configured")
        for origin in origins:
            print(f"    - {origin}")

    cors_regex = os.getenv('CORS_ORIGIN_REGEX', '')
    if cors_regex:
        print(f"  {GREEN}✓{NC} CORS_ORIGIN_REGEX: {cors_regex}")
    else:
        print(f"  {YELLOW}ℹ{NC} CORS_ORIGIN_REGEX: Not set (only exact matches allowed)")

    print()

    # Check port configuration
    print(f"{BLUE}Checking port configuration...{NC}")
    port = os.getenv('PORT', os.getenv('V5_PORT', '5024'))
    print(f"  {GREEN}✓{NC} Port: {port}")

    # Environment-specific port validation
    if env == 'development' and port not in ['5024']:
        warnings.append(f"Development environment using non-standard port: {port} (expected 5024)")
    elif env == 'test' and port not in ['6024']:
        warnings.append(f"Test environment using non-standard port: {port} (expected 6024)")

    print()

    # Check database configuration
    print(f"{BLUE}Checking database configuration...{NC}")
    db_host = os.getenv('DB_HOST', '')
    db_port = os.getenv('DB_PORT', '')
    db_name = os.getenv('DB_NAME', '')

    if env in ['production', 'beta', 'uat']:
        if db_host in ['localhost', '127.0.0.1']:
            errors.append(f"Production/UAT/Beta environment using localhost database")
            print(f"  {RED}✗{NC} DB_HOST: Using localhost in {env} environment!")
        else:
            print(f"  {GREEN}✓{NC} DB_HOST: {db_host}")
    else:
        print(f"  {GREEN}✓{NC} DB_HOST: {db_host}")

    print(f"  {GREEN}✓{NC} DB_PORT: {db_port}")
    print(f"  {GREEN}✓{NC} DB_NAME: {db_name}")

    print()

    # Check secrets
    print(f"{BLUE}Checking secrets...{NC}")
    secret_vars = [
        'SECRET_KEY',
        'JWT_SECRET_KEY',
        'DB_PASSWORD',
        'STRIPE_SECRET_KEY',
        'TWILIO_AUTH_TOKEN',
        'SENDGRID_API_KEY',
    ]

    for var in secret_vars:
        value = os.getenv(var, '')
        if not value:
            warnings.append(f"Secret not set: {var}")
            print(f"  {YELLOW}⚠{NC} {var}: Not set")
        elif check_placeholder(var, value):
            errors.append(f"Secret contains placeholder: {var}")
            print(f"  {RED}✗{NC} {var}: Contains placeholder value")
        else:
            masked = '***' + value[-4:] if len(value) > 4 else '***'
            print(f"  {GREEN}✓{NC} {var}: {masked}")

    print()

    # Summary
    is_valid = len(errors) == 0

    if is_valid:
        print(f"{GREEN}{'='*60}{NC}")
        print(f"{GREEN}✓ Environment validation PASSED{NC}")
        print(f"{GREEN}{'='*60}{NC}")
    else:
        print(f"{RED}{'='*60}{NC}")
        print(f"{RED}✗ Environment validation FAILED{NC}")
        print(f"{RED}{'='*60}{NC}")

    if errors:
        print(f"\n{RED}Errors:{NC}")
        for error in errors:
            print(f"  {RED}✗{NC} {error}")

    if warnings:
        print(f"\n{YELLOW}Warnings:{NC}")
        for warning in warnings:
            print(f"  {YELLOW}⚠{NC} {warning}")

    print()

    return is_valid, errors, warnings

def main():
    """Main entry point"""
    print(f"{BLUE}{'='*60}{NC}")
    print(f"{BLUE}WeedGo Backend - Environment Configuration Validator{NC}")
    print(f"{BLUE}{'='*60}{NC}")
    print()

    # Check if .env file exists
    env_file = Path('.env')
    if not env_file.exists():
        print(f"{RED}Error: .env file not found{NC}")
        print(f"{YELLOW}Create a .env file by copying one of:{NC}")
        print(f"  - .env.local  (for local development)")
        print(f"  - .env.test   (for testing)")
        print(f"  - .env.uat    (for UAT)")
        print(f"  - .env.beta   (for beta)")
        print(f"  - .env.prod   (for production)")
        print()
        print(f"{YELLOW}Example:{NC}")
        print(f"  cp .env.local .env")
        print()
        sys.exit(1)

    # Load .env file
    from dotenv import load_dotenv
    load_dotenv()

    # Validate
    is_valid, errors, warnings = validate_environment()

    # Exit code
    if not is_valid:
        sys.exit(1)
    elif warnings:
        print(f"{YELLOW}Validation passed with warnings{NC}")
        sys.exit(0)
    else:
        print(f"{GREEN}All checks passed!{NC}")
        sys.exit(0)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Validation cancelled{NC}")
        sys.exit(130)
    except Exception as e:
        print(f"\n{RED}Error during validation: {e}{NC}")
        sys.exit(1)
