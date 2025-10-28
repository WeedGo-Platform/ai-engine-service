#!/usr/bin/env python3
"""
Test CORS Server - Quick local test of CORS configuration
Runs a minimal FastAPI server with CORS middleware to test the configuration
"""

import os
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Set UAT environment
os.environ["ENVIRONMENT"] = "uat"

# Create minimal FastAPI app
app = FastAPI()

# Environment-specific CORS defaults
environment = os.getenv("ENVIRONMENT", "development")
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
        "origins": ["http://localhost:3000"],
        "regex": r"https://.*\.vercel\.app"
    }
}

# Parse CORS configuration (same logic as api_server.py)
cors_origins_str = os.getenv("CORS_ALLOWED_ORIGINS", "")
if cors_origins_str:
    delimiter = ";" if ";" in cors_origins_str else ","
    cors_origins = [origin.strip() for origin in cors_origins_str.split(delimiter) if origin.strip()]
    print(f"✓ Using CORS origins from CORS_ALLOWED_ORIGINS environment variable: {cors_origins}")
else:
    env_config = environment_cors_defaults.get(environment, environment_cors_defaults["development"])
    cors_origins = env_config["origins"]
    print(f"✓ Using CORS origins for {environment} environment: {cors_origins}")

cors_origin_regex = os.getenv("CORS_ORIGIN_REGEX", "")
if not cors_origin_regex:
    env_config = environment_cors_defaults.get(environment, environment_cors_defaults["development"])
    cors_origin_regex = env_config["regex"]
    print(f"✓ Using CORS regex: {cors_origin_regex}")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_origin_regex=cors_origin_regex,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.post("/api/v1/auth/admin/login")
async def login():
    return {"status": "ok", "message": "Test endpoint"}

if __name__ == "__main__":
    import uvicorn
    print("\n" + "=" * 60)
    print("CORS TEST SERVER")
    print("=" * 60)
    print(f"Environment: {environment}")
    print(f"Server: http://localhost:8888")
    print("\nTest CORS with:")
    print("curl -i -X OPTIONS http://localhost:8888/api/v1/auth/admin/login \\")
    print('  -H "Origin: https://weedgo-uat-admin.pages.dev" \\')
    print('  -H "Access-Control-Request-Method: POST"')
    print("=" * 60 + "\n")

    uvicorn.run(app, host="0.0.0.0", port=8888, log_level="info")
