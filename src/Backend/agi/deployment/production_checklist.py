#!/usr/bin/env python3
"""
Production Deployment Checklist and Verification
Ensures AGI system is production-ready
"""

import asyncio
import sys
import os
import json
import logging
from typing import Dict, List, Tuple, Any
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

logger = logging.getLogger(__name__)


class ProductionReadinessChecker:
    """Verify production readiness of AGI system"""

    def __init__(self):
        self.checks_passed = []
        self.checks_failed = []
        self.warnings = []

    async def check_database(self) -> Tuple[bool, str]:
        """Verify database is properly configured"""
        try:
            from agi.core.database import get_db_manager

            db = await get_db_manager()
            conn = await db.get_connection()

            # Check all required tables exist
            required_tables = [
                'sessions', 'conversations', 'agents', 'agent_tasks',
                'tool_executions', 'models', 'personas', 'templates',
                'metrics', 'learning_feedback', 'document_embeddings',
                'document_chunks', 'agent_memories', 'security_audit_log'
            ]

            query = """
            SELECT tablename FROM pg_tables
            WHERE schemaname = 'agi'
            """
            tables = await conn.fetch(query)
            existing_tables = [row['tablename'] for row in tables]

            missing = [t for t in required_tables if t not in existing_tables]

            await db.release_connection(conn)

            if missing:
                return False, f"Missing tables: {', '.join(missing)}"

            return True, f"All {len(required_tables)} required tables present"

        except Exception as e:
            return False, f"Database check failed: {str(e)}"

    async def check_models(self) -> Tuple[bool, str]:
        """Verify model configuration"""
        try:
            from agi.models.registry import get_model_registry
            from agi.models.fallback_strategy import get_fallback_strategy

            registry = await get_model_registry()
            models = await registry.list_models()

            if len(models) == 0:
                return False, "No models available"

            # Check fallback strategy
            fallback = await get_fallback_strategy()
            health_report = fallback.get_health_report()

            healthy_models = sum(
                1 for m in health_report.values()
                if m['available']
            )

            if healthy_models == 0:
                return False, "No healthy models available"

            return True, f"{healthy_models}/{len(models)} models healthy"

        except Exception as e:
            return False, f"Model check failed: {str(e)}"

    async def check_security(self) -> Tuple[bool, str]:
        """Verify security configuration"""
        try:
            from agi.api.middleware.auth import SECRET_KEY
            from agi.security import get_rate_limiter, get_audit_logger

            # Check JWT secret is configured
            if not SECRET_KEY or SECRET_KEY == "your-secret-key-here":
                return False, "JWT secret key not properly configured"

            # Check rate limiter
            rate_limiter = await get_rate_limiter()
            if not rate_limiter:
                self.warnings.append("Rate limiter not configured")

            # Check audit logger
            audit_logger = await get_audit_logger()
            if not audit_logger:
                self.warnings.append("Audit logger not configured")

            return True, "Security configured (check warnings)"

        except Exception as e:
            return False, f"Security check failed: {str(e)}"

    async def check_api_endpoints(self) -> Tuple[bool, str]:
        """Verify API endpoints are accessible"""
        try:
            import aiohttp

            base_url = "http://localhost:5024/api/agi"
            critical_endpoints = [
                "/health",
                "/models",
                "/tools",
                "/stats"
            ]

            async with aiohttp.ClientSession() as session:
                failed_endpoints = []

                for endpoint in critical_endpoints:
                    try:
                        async with session.get(f"{base_url}{endpoint}") as response:
                            if response.status != 200:
                                failed_endpoints.append(endpoint)
                    except:
                        failed_endpoints.append(endpoint)

                if failed_endpoints:
                    return False, f"Failed endpoints: {', '.join(failed_endpoints)}"

                return True, f"All {len(critical_endpoints)} critical endpoints accessible"

        except Exception as e:
            return False, f"API check failed: {str(e)}"

    async def check_performance(self) -> Tuple[bool, str]:
        """Check performance metrics"""
        try:
            import aiohttp
            import time

            base_url = "http://localhost:5024/api/agi"

            async with aiohttp.ClientSession() as session:
                # Test health endpoint response time
                start = time.time()
                async with session.get(f"{base_url}/health") as response:
                    health_time = time.time() - start

                if health_time > 1.0:
                    self.warnings.append(f"Health endpoint slow: {health_time:.2f}s")

                # Test chat endpoint response time
                start = time.time()
                async with session.post(
                    f"{base_url}/chat",
                    json={"message": "test", "session_id": "perf-test"}
                ) as response:
                    chat_time = time.time() - start

                if chat_time > 30.0:
                    return False, f"Chat endpoint too slow: {chat_time:.2f}s"

                return True, f"Performance acceptable (health: {health_time:.2f}s, chat: {chat_time:.2f}s)"

        except Exception as e:
            return False, f"Performance check failed: {str(e)}"

    async def check_monitoring(self) -> Tuple[bool, str]:
        """Check monitoring and observability"""
        try:
            from agi.analytics import get_metrics_collector

            metrics = await get_metrics_collector()

            # Check if metrics are being collected
            from datetime import timedelta
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=1)

            recent_metrics = await metrics.get_metrics(
                start_time=start_time,
                end_time=end_time
            )

            if len(recent_metrics) == 0:
                self.warnings.append("No recent metrics found")

            # Check logging configuration
            if logger.level > logging.INFO:
                self.warnings.append("Logging level too high for production")

            return True, f"Monitoring configured ({len(recent_metrics)} recent metrics)"

        except Exception as e:
            return False, f"Monitoring check failed: {str(e)}"

    async def check_error_handling(self) -> Tuple[bool, str]:
        """Verify error handling is in place"""
        try:
            import aiohttp

            base_url = "http://localhost:5024/api/agi"

            async with aiohttp.ClientSession() as session:
                # Test 404 handling
                async with session.get(f"{base_url}/nonexistent") as response:
                    if response.status != 404:
                        return False, "404 errors not handled properly"

                # Test validation error handling
                async with session.post(
                    f"{base_url}/chat",
                    json={"invalid": "data"}
                ) as response:
                    if response.status not in [400, 422]:
                        return False, "Validation errors not handled properly"

                # Test malformed JSON
                async with session.post(
                    f"{base_url}/chat",
                    data="invalid json",
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status not in [400, 422]:
                        return False, "Malformed JSON not handled properly"

            return True, "Error handling verified"

        except Exception as e:
            # Some errors are expected in these tests
            if "404" in str(e) or "422" in str(e) or "400" in str(e):
                return True, "Error handling verified"
            return False, f"Error handling check failed: {str(e)}"

    async def check_configuration(self) -> Tuple[bool, str]:
        """Check system configuration"""
        try:
            from agi.config.agi_config import get_config

            config = get_config()

            # Check environment
            if config.environment != "production":
                self.warnings.append(f"Environment is '{config.environment}', not 'production'")

            # Check database pool size
            if config.database.pool_size < 10:
                self.warnings.append(f"Database pool size low: {config.database.pool_size}")

            # Check service flags
            if not config.services.enable_rag:
                self.warnings.append("RAG service disabled")

            if not config.services.enable_memory:
                self.warnings.append("Memory service disabled")

            if not config.services.enable_analytics:
                self.warnings.append("Analytics service disabled")

            return True, f"Configuration checked (environment: {config.environment})"

        except Exception as e:
            return False, f"Configuration check failed: {str(e)}"

    async def check_resources(self) -> Tuple[bool, str]:
        """Check system resources"""
        try:
            import psutil

            # Check CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            if cpu_percent > 80:
                self.warnings.append(f"High CPU usage: {cpu_percent}%")

            # Check memory
            memory = psutil.virtual_memory()
            if memory.percent > 80:
                self.warnings.append(f"High memory usage: {memory.percent}%")

            # Check disk space
            disk = psutil.disk_usage('/')
            if disk.percent > 90:
                return False, f"Disk space critical: {disk.percent}%"

            return True, f"Resources OK (CPU: {cpu_percent:.1f}%, Mem: {memory.percent:.1f}%, Disk: {disk.percent:.1f}%)"

        except Exception as e:
            return False, f"Resource check failed: {str(e)}"

    async def check_dependencies(self) -> Tuple[bool, str]:
        """Check all dependencies are installed"""
        try:
            required_packages = [
                'fastapi', 'uvicorn', 'asyncpg', 'llama-cpp-python',
                'numpy', 'sentence-transformers', 'pydantic',
                'python-jose', 'passlib', 'python-multipart'
            ]

            missing = []
            for package in required_packages:
                try:
                    __import__(package.replace('-', '_'))
                except ImportError:
                    missing.append(package)

            if missing:
                return False, f"Missing packages: {', '.join(missing)}"

            return True, f"All {len(required_packages)} required packages installed"

        except Exception as e:
            return False, f"Dependency check failed: {str(e)}"

    async def run_all_checks(self) -> Dict[str, Any]:
        """Run all production readiness checks"""
        checks = [
            ("Database", self.check_database),
            ("Models", self.check_models),
            ("Security", self.check_security),
            ("API Endpoints", self.check_api_endpoints),
            ("Performance", self.check_performance),
            ("Monitoring", self.check_monitoring),
            ("Error Handling", self.check_error_handling),
            ("Configuration", self.check_configuration),
            ("Resources", self.check_resources),
            ("Dependencies", self.check_dependencies)
        ]

        results = {}

        print("\n" + "="*60)
        print("Production Readiness Checklist")
        print("="*60)

        for check_name, check_func in checks:
            print(f"\nChecking {check_name}...")
            try:
                passed, message = await check_func()
                results[check_name] = {
                    "passed": passed,
                    "message": message
                }

                if passed:
                    self.checks_passed.append(check_name)
                    print(f"✓ {check_name}: {message}")
                else:
                    self.checks_failed.append(check_name)
                    print(f"✗ {check_name}: {message}")

            except Exception as e:
                results[check_name] = {
                    "passed": False,
                    "message": f"Check failed: {str(e)}"
                }
                self.checks_failed.append(check_name)
                print(f"✗ {check_name}: Check failed - {str(e)}")

        # Summary
        print("\n" + "="*60)
        print("Summary")
        print("="*60)
        print(f"Checks Passed: {len(self.checks_passed)}/{len(checks)}")
        print(f"Checks Failed: {len(self.checks_failed)}/{len(checks)}")

        if self.warnings:
            print(f"\nWarnings ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"  ⚠️  {warning}")

        # Overall status
        production_ready = len(self.checks_failed) == 0

        print("\n" + "="*60)
        if production_ready:
            print("✓ SYSTEM IS PRODUCTION READY")
        else:
            print("✗ SYSTEM NOT PRODUCTION READY")
            print(f"\nFailed checks: {', '.join(self.checks_failed)}")
        print("="*60)

        return {
            "production_ready": production_ready,
            "checks_passed": self.checks_passed,
            "checks_failed": self.checks_failed,
            "warnings": self.warnings,
            "results": results,
            "timestamp": datetime.utcnow().isoformat()
        }


async def generate_deployment_report(results: Dict[str, Any]):
    """Generate deployment report"""
    report_path = Path("deployment_report.json")

    with open(report_path, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\nDeployment report saved to: {report_path}")

    # Generate recommendations
    print("\n" + "="*60)
    print("Recommendations")
    print("="*60)

    if not results["production_ready"]:
        print("\nCritical Issues to Fix:")
        for check in results["checks_failed"]:
            print(f"  • Fix: {check}")
            if check == "Database":
                print("    - Run migration scripts")
                print("    - Verify database connection")
            elif check == "Models":
                print("    - Download required models")
                print("    - Verify model paths")
            elif check == "Security":
                print("    - Set proper JWT secret key")
                print("    - Configure rate limiting")

    if results["warnings"]:
        print("\nWarnings to Address:")
        for warning in results["warnings"]:
            print(f"  • {warning}")

    print("\nNext Steps:")
    if results["production_ready"]:
        print("  1. Review warnings and address if needed")
        print("  2. Configure monitoring and alerting")
        print("  3. Set up backup procedures")
        print("  4. Deploy to production environment")
        print("  5. Run smoke tests in production")
    else:
        print("  1. Fix all failed checks")
        print("  2. Re-run production readiness checks")
        print("  3. Address all warnings")
        print("  4. Review security configuration")
        print("  5. Test under load conditions")


async def main():
    """Main entry point"""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Check server is running
    import aiohttp
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:5024/api/agi/health") as response:
                if response.status != 200:
                    print("⚠️  AGI server not responding properly on port 5024")
    except:
        print("⚠️  AGI server not running on port 5024")
        print("Please start the server before running production checks")
        return 1

    # Run checks
    checker = ProductionReadinessChecker()
    results = await checker.run_all_checks()

    # Generate report
    await generate_deployment_report(results)

    return 0 if results["production_ready"] else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)