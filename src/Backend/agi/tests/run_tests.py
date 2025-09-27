#!/usr/bin/env python3
"""
Test Runner for AGI System
Executes all test suites with proper configuration
"""

import os
import sys
import asyncio
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Configure test environment
os.environ["AGI_ENVIRONMENT"] = "test"
os.environ["AGI_TEST_MODE"] = "true"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def run_integration_tests():
    """Run integration tests"""
    import pytest

    print("\n" + "="*60)
    print("Running AGI Integration Tests")
    print("="*60)

    # Run pytest with coverage
    exit_code = pytest.main([
        "test_api_integration.py",
        "-v",
        "--asyncio-mode=auto",
        "--tb=short",
        "--maxfail=5",
        "-x"  # Stop on first failure
    ])

    return exit_code

async def run_unit_tests():
    """Run unit tests"""
    import pytest

    print("\n" + "="*60)
    print("Running AGI Unit Tests")
    print("="*60)

    # Find all test files
    test_files = [
        "test_models.py",
        "test_tools.py",
        "test_database.py",
        "test_orchestrator.py",
        "test_security.py"
    ]

    # Run tests that exist
    existing_tests = [f for f in test_files if Path(f).exists()]

    if existing_tests:
        exit_code = pytest.main([
            *existing_tests,
            "-v",
            "--asyncio-mode=auto",
            "--tb=short"
        ])
        return exit_code
    else:
        print("No unit tests found")
        return 0

async def run_smoke_tests():
    """Run quick smoke tests"""
    print("\n" + "="*60)
    print("Running Smoke Tests")
    print("="*60)

    try:
        # Test database connection
        from agi.core.database import get_db_manager

        print("Testing database connection...")
        db = await get_db_manager()
        conn = await db.get_connection()
        result = await conn.fetchval("SELECT 1")
        await db.release_connection(conn)
        print("✓ Database connection successful")

        # Test model registry
        from agi.models.registry import get_model_registry

        print("Testing model registry...")
        registry = await get_model_registry()
        models = await registry.list_models()
        print(f"✓ Model registry loaded with {len(models)} models")

        # Test tool registry
        from agi.tools import get_tool_registry

        print("Testing tool registry...")
        tool_registry = await get_tool_registry()
        tools = tool_registry.list_tools()
        print(f"✓ Tool registry loaded with {len(tools)} tools")

        # Test orchestrator
        from agi.orchestrator import get_orchestrator

        print("Testing orchestrator...")
        orchestrator = await get_orchestrator()
        print("✓ Orchestrator initialized successfully")

        print("\n✓ All smoke tests passed!")
        return 0

    except Exception as e:
        print(f"\n✗ Smoke test failed: {e}")
        return 1

async def run_load_tests():
    """Run basic load tests"""
    print("\n" + "="*60)
    print("Running Load Tests")
    print("="*60)

    try:
        import aiohttp
        import time

        base_url = "http://localhost:5024/api/agi"

        async def make_request(session, endpoint):
            """Make a single request"""
            try:
                async with session.get(f"{base_url}{endpoint}") as response:
                    return response.status, time.time()
            except:
                return 0, time.time()

        async with aiohttp.ClientSession() as session:
            # Test health endpoint under load
            print("Testing /health endpoint...")
            start_time = time.time()

            tasks = [make_request(session, "/health") for _ in range(100)]
            results = await asyncio.gather(*tasks)

            elapsed = time.time() - start_time
            successful = sum(1 for status, _ in results if status == 200)

            print(f"Completed {len(results)} requests in {elapsed:.2f}s")
            print(f"Successful: {successful}/{len(results)}")
            print(f"Requests/sec: {len(results)/elapsed:.2f}")

            if successful < len(results) * 0.95:  # 95% success rate
                print("✗ Load test failed - too many failures")
                return 1

            print("✓ Load test passed!")
            return 0

    except Exception as e:
        print(f"✗ Load test error: {e}")
        return 1

async def main():
    """Main test runner"""
    print("\n" + "="*60)
    print("AGI System Test Suite")
    print("="*60)

    # Check if server is running
    import aiohttp
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:5024/api/agi/health") as response:
                if response.status != 200:
                    print("⚠️  Warning: AGI server may not be running properly")
    except:
        print("⚠️  Warning: AGI server is not running on port 5024")
        print("Starting tests anyway...")

    # Run test suites
    test_suites = [
        ("Smoke Tests", run_smoke_tests),
        ("Integration Tests", run_integration_tests),
        ("Unit Tests", run_unit_tests),
    ]

    # Add load tests only if requested
    if "--load" in sys.argv:
        test_suites.append(("Load Tests", run_load_tests))

    results = {}

    for suite_name, test_func in test_suites:
        try:
            exit_code = await test_func()
            results[suite_name] = "PASSED" if exit_code == 0 else "FAILED"
        except Exception as e:
            print(f"Error running {suite_name}: {e}")
            results[suite_name] = "ERROR"

    # Print summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)

    for suite_name, result in results.items():
        symbol = "✓" if result == "PASSED" else "✗"
        print(f"{symbol} {suite_name}: {result}")

    # Overall result
    all_passed = all(r == "PASSED" for r in results.values())

    print("\n" + "="*60)
    if all_passed:
        print("✓ ALL TESTS PASSED")
    else:
        print("✗ SOME TESTS FAILED")
    print("="*60)

    return 0 if all_passed else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)