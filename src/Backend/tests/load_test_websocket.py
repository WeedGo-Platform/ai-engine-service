#!/usr/bin/env python3
"""
WebSocket Load Testing Script
Tests WebSocket server performance with 1000+ concurrent connections

Usage:
    python load_test_websocket.py --connections 1000 --duration 60
    python load_test_websocket.py --connections 5000 --duration 300 --ramp-up 30
"""

import asyncio
import websockets
import argparse
import time
import json
import statistics
from datetime import datetime
from typing import List, Dict, Any
import sys


class WebSocketLoadTester:
    """Load tester for WebSocket connections"""

    def __init__(
        self,
        url: str,
        num_connections: int,
        duration: int,
        ramp_up: int = 10,
        message_interval: float = 5.0
    ):
        self.url = url
        self.num_connections = num_connections
        self.duration = duration
        self.ramp_up = ramp_up
        self.message_interval = message_interval

        # Metrics
        self.connections_established = 0
        self.connections_failed = 0
        self.messages_sent = 0
        self.messages_received = 0
        self.errors = []
        self.connection_times = []
        self.message_latencies = []

        # Control
        self.start_time = None
        self.end_time = None
        self.running = False

    async def connect_client(self, client_id: int) -> None:
        """Connect a single WebSocket client"""

        try:
            # Measure connection time
            connect_start = time.time()

            # For user connections, use email as identifier
            identifier = f"load_test_user_{client_id}@test.com"
            ws_url = f"{self.url}?identifier={identifier}"

            async with websockets.connect(ws_url) as websocket:
                connect_time = time.time() - connect_start
                self.connection_times.append(connect_time)
                self.connections_established += 1

                print(f"✓ Client {client_id} connected ({connect_time:.3f}s)", flush=True)

                # Keep connection alive and send periodic messages
                while self.running:
                    try:
                        # Send heartbeat message
                        send_time = time.time()
                        await websocket.send(json.dumps({
                            "type": "ping",
                            "client_id": client_id,
                            "timestamp": send_time
                        }))
                        self.messages_sent += 1

                        # Wait for response
                        try:
                            response = await asyncio.wait_for(
                                websocket.recv(),
                                timeout=10.0
                            )
                            receive_time = time.time()
                            latency = receive_time - send_time
                            self.message_latencies.append(latency)
                            self.messages_received += 1

                        except asyncio.TimeoutError:
                            print(f"⚠ Client {client_id} timeout waiting for response", flush=True)

                        # Wait before next message
                        await asyncio.sleep(self.message_interval)

                    except websockets.exceptions.ConnectionClosed:
                        print(f"✗ Client {client_id} connection closed", flush=True)
                        break

        except Exception as e:
            self.connections_failed += 1
            self.errors.append({
                "client_id": client_id,
                "error": str(e),
                "type": type(e).__name__
            })
            print(f"✗ Client {client_id} failed: {e}", flush=True)

    async def ramp_up_connections(self) -> List[asyncio.Task]:
        """Gradually ramp up connections"""

        tasks = []
        connections_per_second = self.num_connections / self.ramp_up

        print(f"\n🚀 Ramping up {self.num_connections} connections over {self.ramp_up}s", flush=True)
        print(f"   Rate: {connections_per_second:.1f} connections/second\n", flush=True)

        for i in range(self.num_connections):
            # Create task
            task = asyncio.create_task(self.connect_client(i))
            tasks.append(task)

            # Delay between connections
            if (i + 1) % int(connections_per_second) == 0:
                await asyncio.sleep(1.0)
                print(f"   {i + 1}/{self.num_connections} connections initiated...", flush=True)

        print(f"\n✓ All {self.num_connections} connection tasks created\n", flush=True)
        return tasks

    async def run_test(self) -> Dict[str, Any]:
        """Run the load test"""

        print("=" * 70)
        print("WebSocket Load Test")
        print("=" * 70)
        print(f"Target URL:        {self.url}")
        print(f"Connections:       {self.num_connections}")
        print(f"Test Duration:     {self.duration}s")
        print(f"Ramp-up Time:      {self.ramp_up}s")
        print(f"Message Interval:  {self.message_interval}s")
        print("=" * 70 + "\n")

        self.start_time = time.time()
        self.running = True

        # Ramp up connections
        tasks = await self.ramp_up_connections()

        # Wait for test duration
        print(f"⏱ Test running for {self.duration}s...\n", flush=True)

        # Print progress every 10 seconds
        elapsed = 0
        while elapsed < self.duration:
            await asyncio.sleep(10)
            elapsed += 10
            print(f"   Progress: {elapsed}s / {self.duration}s "
                  f"({self.messages_sent} sent, {self.messages_received} received)", flush=True)

        # Stop test
        print(f"\n⏸ Stopping test...", flush=True)
        self.running = False

        # Wait for all connections to close gracefully
        print(f"⏳ Waiting for connections to close...", flush=True)
        await asyncio.sleep(5)

        # Cancel remaining tasks
        for task in tasks:
            if not task.done():
                task.cancel()

        # Wait for cancellations
        await asyncio.gather(*tasks, return_exceptions=True)

        self.end_time = time.time()

        # Generate report
        return self.generate_report()

    def generate_report(self) -> Dict[str, Any]:
        """Generate test report"""

        total_time = self.end_time - self.start_time

        # Connection metrics
        connection_success_rate = (
            self.connections_established / self.num_connections * 100
            if self.num_connections > 0 else 0
        )

        # Connection time statistics
        if self.connection_times:
            avg_connection_time = statistics.mean(self.connection_times)
            min_connection_time = min(self.connection_times)
            max_connection_time = max(self.connection_times)
            p95_connection_time = statistics.quantiles(self.connection_times, n=20)[18]  # 95th percentile
        else:
            avg_connection_time = min_connection_time = max_connection_time = p95_connection_time = 0

        # Message latency statistics
        if self.message_latencies:
            avg_latency = statistics.mean(self.message_latencies)
            min_latency = min(self.message_latencies)
            max_latency = max(self.message_latencies)
            p95_latency = statistics.quantiles(self.message_latencies, n=20)[18]
        else:
            avg_latency = min_latency = max_latency = p95_latency = 0

        # Throughput
        messages_per_second = self.messages_sent / total_time if total_time > 0 else 0

        report = {
            "test_config": {
                "url": self.url,
                "target_connections": self.num_connections,
                "duration": self.duration,
                "ramp_up": self.ramp_up,
                "message_interval": self.message_interval
            },
            "test_results": {
                "total_time": total_time,
                "connections_attempted": self.num_connections,
                "connections_established": self.connections_established,
                "connections_failed": self.connections_failed,
                "connection_success_rate": connection_success_rate,
                "messages_sent": self.messages_sent,
                "messages_received": self.messages_received,
                "messages_per_second": messages_per_second,
                "total_errors": len(self.errors)
            },
            "connection_metrics": {
                "avg_time": avg_connection_time,
                "min_time": min_connection_time,
                "max_time": max_connection_time,
                "p95_time": p95_connection_time
            },
            "message_latency": {
                "avg": avg_latency,
                "min": min_latency,
                "max": max_latency,
                "p95": p95_latency
            },
            "errors": self.errors[:10]  # First 10 errors
        }

        return report

    def print_report(self, report: Dict[str, Any]) -> None:
        """Print formatted test report"""

        print("\n" + "=" * 70)
        print("TEST RESULTS")
        print("=" * 70)

        # Test configuration
        print("\n📋 Configuration:")
        print(f"   URL:                {report['test_config']['url']}")
        print(f"   Target Connections: {report['test_config']['target_connections']}")
        print(f"   Duration:           {report['test_config']['duration']}s")
        print(f"   Ramp-up:            {report['test_config']['ramp_up']}s")

        # Connection metrics
        results = report['test_results']
        print(f"\n🔌 Connection Metrics:")
        print(f"   Attempted:          {results['connections_attempted']}")
        print(f"   Established:        {results['connections_established']}")
        print(f"   Failed:             {results['connections_failed']}")
        print(f"   Success Rate:       {results['connection_success_rate']:.2f}%")

        conn_metrics = report['connection_metrics']
        print(f"\n⏱ Connection Times:")
        print(f"   Average:            {conn_metrics['avg_time']:.3f}s")
        print(f"   Min:                {conn_metrics['min_time']:.3f}s")
        print(f"   Max:                {conn_metrics['max_time']:.3f}s")
        print(f"   P95:                {conn_metrics['p95_time']:.3f}s")

        # Message metrics
        print(f"\n📨 Message Metrics:")
        print(f"   Sent:               {results['messages_sent']}")
        print(f"   Received:           {results['messages_received']}")
        print(f"   Throughput:         {results['messages_per_second']:.2f} msg/s")

        latency = report['message_latency']
        print(f"\n📊 Message Latency:")
        print(f"   Average:            {latency['avg']:.3f}s")
        print(f"   Min:                {latency['min']:.3f}s")
        print(f"   Max:                {latency['max']:.3f}s")
        print(f"   P95:                {latency['p95']:.3f}s")

        # Errors
        if results['total_errors'] > 0:
            print(f"\n❌ Errors: {results['total_errors']}")
            if report['errors']:
                print("   First 10 errors:")
                for error in report['errors']:
                    print(f"   - Client {error['client_id']}: {error['type']} - {error['error']}")

        # Performance assessment
        print(f"\n🎯 Performance Assessment:")
        if results['connection_success_rate'] >= 95:
            print("   ✅ Excellent - 95%+ connection success rate")
        elif results['connection_success_rate'] >= 90:
            print("   ✓ Good - 90-95% connection success rate")
        else:
            print("   ⚠ Needs improvement - <90% connection success rate")

        if latency['p95'] < 0.1:
            print("   ✅ Excellent - P95 latency < 100ms")
        elif latency['p95'] < 0.5:
            print("   ✓ Good - P95 latency < 500ms")
        else:
            print("   ⚠ Needs improvement - P95 latency > 500ms")

        print("\n" + "=" * 70 + "\n")


async def main():
    """Main function"""

    parser = argparse.ArgumentParser(description="WebSocket Load Testing")
    parser.add_argument(
        "--url",
        default="ws://localhost:5024/ws/notifications/user",
        help="WebSocket URL to test (default: ws://localhost:5024/ws/notifications/user)"
    )
    parser.add_argument(
        "--connections",
        type=int,
        default=1000,
        help="Number of concurrent connections (default: 1000)"
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=60,
        help="Test duration in seconds (default: 60)"
    )
    parser.add_argument(
        "--ramp-up",
        type=int,
        default=10,
        help="Ramp-up time in seconds (default: 10)"
    )
    parser.add_argument(
        "--message-interval",
        type=float,
        default=5.0,
        help="Interval between messages in seconds (default: 5.0)"
    )

    args = parser.parse_args()

    # Create load tester
    tester = WebSocketLoadTester(
        url=args.url,
        num_connections=args.connections,
        duration=args.duration,
        ramp_up=args.ramp_up,
        message_interval=args.message_interval
    )

    # Run test
    try:
        report = await tester.run_test()
        tester.print_report(report)

        # Save report to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"load_test_report_{timestamp}.json"

        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"📄 Report saved to: {filename}\n")

        # Exit with appropriate code
        if report['test_results']['connection_success_rate'] < 90:
            sys.exit(1)  # Fail if success rate < 90%

    except KeyboardInterrupt:
        print("\n\n⚠ Test interrupted by user\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {e}\n")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
