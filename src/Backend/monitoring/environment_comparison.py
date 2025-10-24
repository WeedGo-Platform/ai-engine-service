#!/usr/bin/env python3
"""
Multi-Environment Performance Monitoring & Comparison Dashboard

This script monitors all three environments (UAT, Beta, Pre-PROD) and generates
comparison reports on performance, uptime, and costs.

Usage:
    python monitoring/environment_comparison.py --output dashboard.html
"""

import asyncio
import aiohttp
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any
import json

# Environment configurations
ENVIRONMENTS = {
    "UAT": {
        "name": "UAT (Cloudflare + Koyeb + Neon)",
        "backend_url": "https://weedgo-uat.koyeb.app",
        "frontend_url": "https://weedgo-uat-admin.pages.dev",
        "platform": "Cloudflare Pages + Koyeb + Neon + Upstash",
        "color": "#FF6B6B"
    },
    "Beta": {
        "name": "Beta (Netlify + Render + Supabase)",
        "backend_url": "https://weedgo-beta.onrender.com",
        "frontend_url": "https://weedgo-beta-admin.netlify.app",
        "platform": "Netlify + Render + Supabase",
        "color": "#4ECDC4"
    },
    "Pre-PROD": {
        "name": "Pre-PROD (Vercel + Railway)",
        "backend_url": "https://weedgo-preprod.up.railway.app",
        "frontend_url": "https://weedgo-preprod-admin.vercel.app",
        "platform": "Vercel + Railway",
        "color": "#95E1D3"
    }
}

ENDPOINTS_TO_TEST = [
    "/health",
    "/api/v1/products?limit=10",
    "/api/v1/stores",
    "/api/admin/auth/verify"
]


async def measure_response_time(session: aiohttp.ClientSession, url: str, endpoint: str) -> Dict[str, Any]:
    """Measure response time for a single endpoint."""
    full_url = f"{url}{endpoint}"

    try:
        start = time.time()
        async with session.get(full_url, timeout=aiohttp.ClientTimeout(total=30)) as response:
            await response.text()
            duration = (time.time() - start) * 1000  # Convert to milliseconds

            return {
                "endpoint": endpoint,
                "status": response.status,
                "duration_ms": round(duration, 2),
                "success": 200 <= response.status < 300,
                "timestamp": datetime.now().isoformat()
            }
    except asyncio.TimeoutError:
        return {
            "endpoint": endpoint,
            "status": 0,
            "duration_ms": 30000,
            "success": False,
            "error": "Timeout",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "endpoint": endpoint,
            "status": 0,
            "duration_ms": 0,
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


async def test_environment(env_name: str, config: Dict[str, str]) -> Dict[str, Any]:
    """Test all endpoints for a single environment."""
    print(f"Testing {env_name}...")

    async with aiohttp.ClientSession() as session:
        tasks = [
            measure_response_time(session, config["backend_url"], endpoint)
            for endpoint in ENDPOINTS_TO_TEST
        ]

        results = await asyncio.gather(*tasks)

        # Calculate metrics
        successful = [r for r in results if r["success"]]
        failed = [r for r in results if not r["success"]]
        durations = [r["duration_ms"] for r in successful]

        return {
            "environment": env_name,
            "platform": config["platform"],
            "backend_url": config["backend_url"],
            "frontend_url": config["frontend_url"],
            "color": config["color"],
            "results": results,
            "metrics": {
                "total_requests": len(results),
                "successful_requests": len(successful),
                "failed_requests": len(failed),
                "success_rate": round(len(successful) / len(results) * 100, 2) if results else 0,
                "avg_response_time": round(sum(durations) / len(durations), 2) if durations else 0,
                "min_response_time": round(min(durations), 2) if durations else 0,
                "max_response_time": round(max(durations), 2) if durations else 0,
                "p95_response_time": round(sorted(durations)[int(len(durations) * 0.95)], 2) if durations else 0,
            },
            "timestamp": datetime.now().isoformat()
        }


async def run_comparison() -> Dict[str, Any]:
    """Run comparison across all environments."""
    print("=" * 60)
    print("Multi-Environment Performance Comparison")
    print("=" * 60)

    tasks = [
        test_environment(env_name, config)
        for env_name, config in ENVIRONMENTS.items()
    ]

    results = await asyncio.gather(*tasks)

    return {
        "comparison_timestamp": datetime.now().isoformat(),
        "environments": results,
        "winner": determine_winner(results)
    }


def determine_winner(results: List[Dict[str, Any]]) -> Dict[str, str]:
    """Determine the best performing environment."""
    winners = {
        "fastest_avg": min(results, key=lambda x: x["metrics"]["avg_response_time"])["environment"],
        "most_reliable": max(results, key=lambda x: x["metrics"]["success_rate"])["environment"],
        "fastest_p95": min(results, key=lambda x: x["metrics"]["p95_response_time"])["environment"],
    }

    return winners


def generate_html_report(comparison_data: Dict[str, Any]) -> str:
    """Generate HTML dashboard."""

    html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>WeedGo Multi-Environment Comparison</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            margin: 0;
            padding: 20px;
            background: #f5f7fa;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        h1 {{
            color: #2c3e50;
            text-align: center;
            margin-bottom: 10px;
        }}
        .timestamp {{
            text-align: center;
            color: #7f8c8d;
            margin-bottom: 30px;
        }}
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .env-card {{
            background: white;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        .env-header {{
            display: flex;
            align-items: center;
            margin-bottom: 15px;
        }}
        .env-indicator {{
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 10px;
        }}
        .env-name {{
            font-size: 18px;
            font-weight: 600;
            color: #2c3e50;
        }}
        .platform {{
            font-size: 12px;
            color: #7f8c8d;
            margin-bottom: 15px;
        }}
        .metric {{
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid #ecf0f1;
        }}
        .metric:last-child {{
            border-bottom: none;
        }}
        .metric-label {{
            color: #7f8c8d;
            font-size: 14px;
        }}
        .metric-value {{
            font-weight: 600;
            color: #2c3e50;
        }}
        .winner-badge {{
            display: inline-block;
            background: #27ae60;
            color: white;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 11px;
            margin-left: 5px;
        }}
        .comparison-table {{
            background: white;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            overflow-x: auto;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ecf0f1;
        }}
        th {{
            background: #f8f9fa;
            font-weight: 600;
            color: #2c3e50;
        }}
        .status-success {{
            color: #27ae60;
        }}
        .status-error {{
            color: #e74c3c;
        }}
        .chart {{
            margin-top: 30px;
            background: white;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 Multi-Environment Performance Dashboard</h1>
        <div class="timestamp">Last updated: {comparison_data['comparison_timestamp']}</div>

        <div class="grid">
"""

    # Add environment cards
    for env in comparison_data["environments"]:
        metrics = env["metrics"]
        is_fastest = comparison_data["winner"]["fastest_avg"] == env["environment"]
        is_most_reliable = comparison_data["winner"]["most_reliable"] == env["environment"]

        html += f"""
            <div class="env-card">
                <div class="env-header">
                    <div class="env-indicator" style="background: {env['color']}"></div>
                    <div class="env-name">{env['environment']}</div>
                </div>
                <div class="platform">{env['platform']}</div>

                <div class="metric">
                    <span class="metric-label">Success Rate</span>
                    <span class="metric-value class:status-success">{metrics['success_rate']}%
                    {'<span class="winner-badge">Most Reliable</span>' if is_most_reliable else ''}
                    </span>
                </div>

                <div class="metric">
                    <span class="metric-label">Avg Response Time</span>
                    <span class="metric-value">{metrics['avg_response_time']}ms
                    {'<span class="winner-badge">Fastest</span>' if is_fastest else ''}
                    </span>
                </div>

                <div class="metric">
                    <span class="metric-label">P95 Response Time</span>
                    <span class="metric-value">{metrics['p95_response_time']}ms</span>
                </div>

                <div class="metric">
                    <span class="metric-label">Min / Max</span>
                    <span class="metric-value">{metrics['min_response_time']}ms / {metrics['max_response_time']}ms</span>
                </div>

                <div class="metric">
                    <span class="metric-label">Requests</span>
                    <span class="metric-value">{metrics['successful_requests']}/{metrics['total_requests']}</span>
                </div>
            </div>
"""

    html += """
        </div>

        <div class="comparison-table">
            <h2>Detailed Endpoint Results</h2>
            <table>
                <thead>
                    <tr>
                        <th>Endpoint</th>
                        <th>UAT</th>
                        <th>Beta</th>
                        <th>Pre-PROD</th>
                    </tr>
                </thead>
                <tbody>
"""

    # Add detailed endpoint comparison
    for endpoint in ENDPOINTS_TO_TEST:
        html += f"<tr><td><code>{endpoint}</code></td>"

        for env in comparison_data["environments"]:
            result = next((r for r in env["results"] if r["endpoint"] == endpoint), None)
            if result and result["success"]:
                html += f'<td class="status-success">{result["duration_ms"]}ms</td>'
            elif result:
                html += f'<td class="status-error">Error: {result.get("error", "Failed")}</td>'
            else:
                html += '<td class="status-error">No data</td>'

        html += "</tr>"

    html += """
                </tbody>
            </table>
        </div>
    </div>
</body>
</html>
"""

    return html


def generate_json_report(comparison_data: Dict[str, Any]) -> str:
    """Generate JSON report for programmatic access."""
    return json.dumps(comparison_data, indent=2)


async def main():
    """Main execution."""
    comparison_data = await run_comparison()

    # Generate reports
    html_report = generate_html_report(comparison_data)
    json_report = generate_json_report(comparison_data)

    # Save reports
    with open("environment_comparison.html", "w") as f:
        f.write(html_report)
    print("\n✅ HTML report saved to: environment_comparison.html")

    with open("environment_comparison.json", "w") as f:
        f.write(json_report)
    print("✅ JSON report saved to: environment_comparison.json")

    # Print summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    for env in comparison_data["environments"]:
        metrics = env["metrics"]
        print(f"\n{env['environment']} ({env['platform']})")
        print(f"  Success Rate: {metrics['success_rate']}%")
        print(f"  Avg Response: {metrics['avg_response_time']}ms")
        print(f"  P95 Response: {metrics['p95_response_time']}ms")

    print("\n🏆 Winners:")
    for category, winner in comparison_data["winner"].items():
        print(f"  {category.replace('_', ' ').title()}: {winner}")

    print("\n✨ Open environment_comparison.html in your browser to view the dashboard")


if __name__ == "__main__":
    asyncio.run(main())
