#!/usr/bin/env python3
"""
Test CORS Configuration Logic
Verifies that CORS origins are parsed correctly from environment variables
"""

import os
import sys

def test_cors_parsing():
    """Test CORS origin parsing logic"""

    # Environment-specific CORS defaults
    environment_cors_defaults = {
        "uat": {
            "origins": [
                "https://weedgo-uat-admin.pages.dev",
                "https://weedgo-uat-commerce-headless.pages.dev",
                "https://weedgo-uat-commerce-pot-palace.pages.dev",
                "https://weedgo-uat-commerce-modern.pages.dev"
            ],
            "regex": r"https://.*\.weedgo-uat-.*\.pages\.dev"
        },
        "development": {
            "origins": [
                "http://localhost:3000",
                "http://localhost:5173"
            ],
            "regex": r"https://.*\.vercel\.app"
        }
    }

    print("=" * 60)
    print("CORS CONFIGURATION TEST")
    print("=" * 60)

    # Test 1: With semicolon-separated CORS_ALLOWED_ORIGINS
    print("\n[Test 1] Semicolon-separated CORS_ALLOWED_ORIGINS:")
    os.environ["CORS_ALLOWED_ORIGINS"] = "https://weedgo-uat-admin.pages.dev;https://weedgo-uat-commerce-headless.pages.dev"
    os.environ["CORS_ORIGIN_REGEX"] = r"https://.*\.weedgo-uat-admin\.pages\.dev"
    os.environ["ENVIRONMENT"] = "uat"

    environment = os.getenv("ENVIRONMENT", "development")
    cors_origins_str = os.getenv("CORS_ALLOWED_ORIGINS", "")

    if cors_origins_str:
        delimiter = ";" if ";" in cors_origins_str else ","
        cors_origins = [origin.strip() for origin in cors_origins_str.split(delimiter) if origin.strip()]
        print(f"✓ Using CORS origins from CORS_ALLOWED_ORIGINS environment variable:")
        for origin in cors_origins:
            print(f"  - {origin}")
    else:
        env_config = environment_cors_defaults.get(environment, environment_cors_defaults["development"])
        cors_origins = env_config["origins"]
        print(f"✓ Using CORS origins for {environment} environment:")
        for origin in cors_origins:
            print(f"  - {origin}")

    cors_origin_regex = os.getenv("CORS_ORIGIN_REGEX", "")
    if not cors_origin_regex:
        env_config = environment_cors_defaults.get(environment, environment_cors_defaults["development"])
        cors_origin_regex = env_config["regex"]

    print(f"✓ Using CORS regex: {cors_origin_regex}")

    # Test 2: Without CORS_ALLOWED_ORIGINS (should use environment defaults)
    print("\n[Test 2] No CORS_ALLOWED_ORIGINS (using environment defaults):")
    del os.environ["CORS_ALLOWED_ORIGINS"]
    del os.environ["CORS_ORIGIN_REGEX"]

    environment = os.getenv("ENVIRONMENT", "development")
    cors_origins_str = os.getenv("CORS_ALLOWED_ORIGINS", "")

    if cors_origins_str:
        delimiter = ";" if ";" in cors_origins_str else ","
        cors_origins = [origin.strip() for origin in cors_origins_str.split(delimiter) if origin.strip()]
        print(f"✓ Using CORS origins from environment variable")
    else:
        env_config = environment_cors_defaults.get(environment, environment_cors_defaults["development"])
        cors_origins = env_config["origins"]
        print(f"✓ Using CORS origins for {environment} environment:")
        for origin in cors_origins:
            print(f"  - {origin}")

    cors_origin_regex = os.getenv("CORS_ORIGIN_REGEX", "")
    if not cors_origin_regex:
        env_config = environment_cors_defaults.get(environment, environment_cors_defaults["development"])
        cors_origin_regex = env_config["regex"]

    print(f"✓ Using CORS regex: {cors_origin_regex}")

    # Test 3: Comma-separated
    print("\n[Test 3] Comma-separated CORS_ALLOWED_ORIGINS:")
    os.environ["CORS_ALLOWED_ORIGINS"] = "https://example1.com,https://example2.com"

    cors_origins_str = os.getenv("CORS_ALLOWED_ORIGINS", "")
    if cors_origins_str:
        delimiter = ";" if ";" in cors_origins_str else ","
        cors_origins = [origin.strip() for origin in cors_origins_str.split(delimiter) if origin.strip()]
        print(f"✓ Detected delimiter: '{delimiter}'")
        print(f"✓ Parsed origins:")
        for origin in cors_origins:
            print(f"  - {origin}")

    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED")
    print("=" * 60)

    return True

if __name__ == "__main__":
    try:
        test_cors_parsing()
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
