#!/usr/bin/env python3
"""
V5 Setup Test Script
Validates that all V5 components are properly configured and working
"""

import os
import sys
import asyncio
import json
from pathlib import Path

# Add V5 to path
sys.path.insert(0, str(Path(__file__).parent))

def check_environment():
    """Check required environment variables"""
    print("✓ Checking environment variables...")
    
    required_vars = ['DB_PASSWORD', 'JWT_SECRET', 'API_KEY_SALT']
    missing = []
    
    for var in required_vars:
        if not os.environ.get(var):
            missing.append(var)
    
    if missing:
        print(f"  ⚠️  Missing required variables: {missing}")
        print("  Loading from .env file...")
        from dotenv import load_dotenv
        load_dotenv()
        
        # Check again
        still_missing = [v for v in missing if not os.environ.get(v)]
        if still_missing:
            print(f"  ✗ Still missing: {still_missing}")
            return False
    
    print("  ✓ All required environment variables set")
    return True


def check_imports():
    """Check all V5 modules can be imported"""
    print("\n✓ Checking V5 module imports...")
    
    modules_to_check = [
        ('core.config_loader', 'SecureConfigLoader'),
        ('core.authentication', 'JWTAuthentication'),
        ('core.rate_limiter', 'RateLimiter'),
        ('core.input_validation', 'InputValidator'),
        ('core.secure_database', 'SecureDatabaseConnection'),
        ('core.function_schemas', 'FunctionRegistry'),
        ('services.smart_ai_engine_v5', 'SmartAIEngineV5'),
    ]
    
    for module_path, class_name in modules_to_check:
        try:
            module = __import__(module_path, fromlist=[class_name])
            cls = getattr(module, class_name)
            print(f"  ✓ {module_path}.{class_name}")
        except Exception as e:
            print(f"  ✗ Failed to import {module_path}.{class_name}: {e}")
            return False
    
    return True


def check_files():
    """Check all required files exist"""
    print("\n✓ Checking required files...")
    
    required_files = [
        'api_server.py',
        'requirements.txt',
        '.env',
        'config/system_config.json',
        'prompts/endpoint_prompts.json',
        'prompts/agents/dispensary_agent.json',
        'prompts/personality/friendly_personality.json',
    ]
    
    missing = []
    for file in required_files:
        file_path = Path(__file__).parent / file
        if file_path.exists():
            print(f"  ✓ {file}")
        else:
            print(f"  ✗ Missing: {file}")
            missing.append(file)
    
    return len(missing) == 0


async def check_database():
    """Check database connection"""
    print("\n✓ Checking database connection...")
    
    try:
        from core.secure_database import SecureDatabaseConnection
        
        db_config = {
            'host': os.environ.get('DB_HOST', 'localhost'),
            'port': int(os.environ.get('DB_PORT', 5434)),
            'database': os.environ.get('DB_NAME', 'ai_engine'),
            'user': os.environ.get('DB_USER', 'weedgo'),
            'password': os.environ.get('DB_PASSWORD')
        }
        
        if not db_config['password']:
            print("  ✗ Database password not set")
            return False
        
        db = SecureDatabaseConnection(db_config)
        await db.initialize()
        
        # Test a simple query
        result = await db.execute("SELECT 1 as test")
        if result and result[0]['test'] == 1:
            print("  ✓ Database connection successful")
            await db.close()
            return True
        else:
            print("  ✗ Database query failed")
            await db.close()
            return False
            
    except Exception as e:
        print(f"  ✗ Database connection failed: {e}")
        return False


def check_model():
    """Check if model file exists"""
    print("\n✓ Checking model file...")
    
    model_path = os.environ.get('MODEL_PATH', '')
    if not model_path:
        print("  ⚠️  MODEL_PATH not set in environment")
        return False
    
    model_file = Path(model_path)
    if model_file.exists():
        size_mb = model_file.stat().st_size / (1024 * 1024)
        print(f"  ✓ Model found: {model_file.name} ({size_mb:.1f} MB)")
        return True
    else:
        print(f"  ✗ Model not found: {model_path}")
        return False


async def test_v5_engine():
    """Test V5 engine initialization"""
    print("\n✓ Testing V5 engine initialization...")
    
    try:
        from services.smart_ai_engine_v5 import SmartAIEngineV5
        
        engine = SmartAIEngineV5()
        
        # Load agent
        engine.load_agent_personality(
            agent_id="dispensary",
            personality_id="friendly"
        )
        
        # Test simple message processing
        result = await engine.process_message(
            message="Hello",
            context={'user_id': 'test'},
            session_id='test_session'
        )
        
        if result and 'response' in result:
            print(f"  ✓ Engine test successful")
            print(f"    Response: {result['response'][:100]}...")
            return True
        else:
            print("  ✗ Engine test failed - no response")
            return False
            
    except Exception as e:
        print(f"  ✗ Engine test failed: {e}")
        return False


async def main():
    """Run all tests"""
    print("=" * 60)
    print("V5 AI Engine Setup Test")
    print("=" * 60)
    
    # Load .env file
    from dotenv import load_dotenv
    load_dotenv()
    
    tests = [
        ("Environment", check_environment()),
        ("File Structure", check_files()),
        ("Module Imports", check_imports()),
        ("Model File", check_model()),
    ]
    
    # Async tests
    async_tests = [
        ("Database Connection", await check_database()),
        ("V5 Engine", await test_v5_engine()),
    ]
    
    all_tests = tests + async_tests
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in all_tests if result)
    total = len(all_tests)
    
    for name, result in all_tests:
        status = "✓" if result else "✗"
        print(f"{status} {name}")
    
    print(f"\nResult: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✅ V5 setup is complete and working!")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please fix the issues above.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)