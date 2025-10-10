#!/usr/bin/env python3
"""
Test script for verifying chat endpoints work with both legacy and unified paths.
This tests the backward compatibility layer without creating new database structures.
"""

import requests
import json
import asyncio
import websocket
import threading
import time

BASE_URL = "http://localhost:5024"

def test_rest_endpoints():
    """Test REST API endpoints for both legacy and unified paths"""

    print("=" * 60)
    print("TESTING CHAT REST ENDPOINTS")
    print("=" * 60)

    # Track test results
    results = []

    # 1. Test health endpoints
    print("\n1. Testing Health Endpoints:")
    print("-" * 40)

    # Test legacy health
    try:
        response = requests.get(f"{BASE_URL}/chat/health")
        if response.status_code == 200:
            print("✅ GET /chat/health (legacy) - Status: 200")
            results.append(("GET /chat/health", "PASSED"))
        else:
            print(f"❌ GET /chat/health (legacy) - Status: {response.status_code}")
            results.append(("GET /chat/health", f"FAILED: {response.status_code}"))
    except Exception as e:
        print(f"❌ GET /chat/health (legacy) - Error: {str(e)}")
        results.append(("GET /chat/health", f"ERROR: {str(e)}"))

    # Test unified health
    try:
        response = requests.get(f"{BASE_URL}/api/v1/chat/health")
        if response.status_code == 200:
            print("✅ GET /api/v1/chat/health (unified) - Status: 200")
            results.append(("GET /api/v1/chat/health", "PASSED"))
        else:
            print(f"❌ GET /api/v1/chat/health (unified) - Status: {response.status_code}")
            results.append(("GET /api/v1/chat/health", f"FAILED: {response.status_code}"))
    except Exception as e:
        print(f"❌ GET /api/v1/chat/health (unified) - Error: {str(e)}")
        results.append(("GET /api/v1/chat/health", f"ERROR: {str(e)}"))

    # 2. Test session creation (unified only, legacy doesn't have explicit creation)
    print("\n2. Testing Session Creation:")
    print("-" * 40)

    session_id = None
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/chat/sessions",
            json={
                "agent_id": "dispensary",
                "personality_id": "marcel",
                "language": "en"
            }
        )
        if response.status_code == 201:
            session_data = response.json()
            session_id = session_data.get("session_id")
            print(f"✅ POST /api/v1/chat/sessions - Created session: {session_id[:8]}...")
            results.append(("POST /api/v1/chat/sessions", "PASSED"))
        else:
            print(f"❌ POST /api/v1/chat/sessions - Status: {response.status_code}")
            results.append(("POST /api/v1/chat/sessions", f"FAILED: {response.status_code}"))
    except Exception as e:
        print(f"❌ POST /api/v1/chat/sessions - Error: {str(e)}")
        results.append(("POST /api/v1/chat/sessions", f"ERROR: {str(e)}"))

    # 3. Test message sending
    print("\n3. Testing Message Sending:")
    print("-" * 40)

    # Test legacy message endpoint
    try:
        response = requests.post(
            f"{BASE_URL}/chat/message",
            json={
                "message": "Hello from legacy endpoint",
                "session_id": session_id,
                "agent_id": "dispensary",
                "personality_id": "marcel"
            }
        )
        if response.status_code == 200:
            resp_data = response.json()
            print(f"✅ POST /chat/message (legacy) - Response: {resp_data.get('text', '')[:50]}...")
            results.append(("POST /chat/message", "PASSED"))
        else:
            print(f"❌ POST /chat/message (legacy) - Status: {response.status_code}")
            results.append(("POST /chat/message", f"FAILED: {response.status_code}"))
    except Exception as e:
        print(f"❌ POST /chat/message (legacy) - Error: {str(e)}")
        results.append(("POST /chat/message", f"ERROR: {str(e)}"))

    # Test unified message endpoint
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/chat/message",
            json={
                "message": "Hello from unified endpoint",
                "session_id": session_id,
                "agent_id": "dispensary",
                "personality_id": "marcel"
            }
        )
        if response.status_code == 200:
            resp_data = response.json()
            print(f"✅ POST /api/v1/chat/message (unified) - Response: {resp_data.get('text', '')[:50]}...")
            results.append(("POST /api/v1/chat/message", "PASSED"))
        else:
            print(f"❌ POST /api/v1/chat/message (unified) - Status: {response.status_code}")
            results.append(("POST /api/v1/chat/message", f"FAILED: {response.status_code}"))
    except Exception as e:
        print(f"❌ POST /api/v1/chat/message (unified) - Error: {str(e)}")
        results.append(("POST /api/v1/chat/message", f"ERROR: {str(e)}"))

    # 4. Test history endpoints
    print("\n4. Testing History Endpoints:")
    print("-" * 40)

    # Use a test user ID
    test_user_id = "test-user-123"

    # Test legacy user history
    try:
        response = requests.get(f"{BASE_URL}/chat/history/{test_user_id}")
        if response.status_code == 200:
            history = response.json()
            msg_count = len(history.get("messages", []))
            print(f"✅ GET /chat/history/{test_user_id} (legacy) - Messages: {msg_count}")
            results.append(("GET /chat/history/{user_id}", "PASSED"))
        else:
            print(f"❌ GET /chat/history/{test_user_id} (legacy) - Status: {response.status_code}")
            results.append(("GET /chat/history/{user_id}", f"FAILED: {response.status_code}"))
    except Exception as e:
        print(f"❌ GET /chat/history/{test_user_id} (legacy) - Error: {str(e)}")
        results.append(("GET /chat/history/{user_id}", f"ERROR: {str(e)}"))

    # Test unified user history
    try:
        response = requests.get(f"{BASE_URL}/api/v1/chat/history/{test_user_id}")
        if response.status_code == 200:
            history = response.json()
            msg_count = len(history.get("messages", []))
            print(f"✅ GET /api/v1/chat/history/{test_user_id} (unified) - Messages: {msg_count}")
            results.append(("GET /api/v1/chat/history/{user_id}", "PASSED"))
        else:
            print(f"❌ GET /api/v1/chat/history/{test_user_id} (unified) - Status: {response.status_code}")
            results.append(("GET /api/v1/chat/history/{user_id}", f"FAILED: {response.status_code}"))
    except Exception as e:
        print(f"❌ GET /api/v1/chat/history/{test_user_id} (unified) - Error: {str(e)}")
        results.append(("GET /api/v1/chat/history/{user_id}", f"ERROR: {str(e)}"))

    # Test session history if we have a session
    if session_id:
        # Test legacy session history
        try:
            response = requests.get(f"{BASE_URL}/chat/sessions/{session_id}/history")
            if response.status_code == 200:
                history = response.json()
                msg_count = len(history.get("messages", []))
                print(f"✅ GET /chat/sessions/{session_id[:8]}.../history (legacy) - Messages: {msg_count}")
                results.append(("GET /chat/sessions/{id}/history", "PASSED"))
            else:
                print(f"❌ GET /chat/sessions/{session_id[:8]}.../history (legacy) - Status: {response.status_code}")
                results.append(("GET /chat/sessions/{id}/history", f"FAILED: {response.status_code}"))
        except Exception as e:
            print(f"❌ GET /chat/sessions/{session_id[:8]}.../history (legacy) - Error: {str(e)}")
            results.append(("GET /chat/sessions/{id}/history", f"ERROR: {str(e)}"))

        # Test unified session history
        try:
            response = requests.get(f"{BASE_URL}/api/v1/chat/sessions/{session_id}/history")
            if response.status_code == 200:
                history = response.json()
                msg_count = len(history.get("messages", []))
                print(f"✅ GET /api/v1/chat/sessions/{session_id[:8]}.../history (unified) - Messages: {msg_count}")
                results.append(("GET /api/v1/chat/sessions/{id}/history", "PASSED"))
            else:
                print(f"❌ GET /api/v1/chat/sessions/{session_id[:8]}.../history (unified) - Status: {response.status_code}")
                results.append(("GET /api/v1/chat/sessions/{id}/history", f"FAILED: {response.status_code}"))
        except Exception as e:
            print(f"❌ GET /api/v1/chat/sessions/{session_id[:8]}.../history (unified) - Error: {str(e)}")
            results.append(("GET /api/v1/chat/sessions/{id}/history", f"ERROR: {str(e)}"))

    # 5. Test sessions list
    print("\n5. Testing Sessions List:")
    print("-" * 40)

    # Test legacy sessions list
    try:
        response = requests.get(f"{BASE_URL}/chat/sessions")
        if response.status_code == 200:
            sessions = response.json()
            session_count = sessions.get("total", 0)
            print(f"✅ GET /chat/sessions (legacy) - Active sessions: {session_count}")
            results.append(("GET /chat/sessions", "PASSED"))
        else:
            print(f"❌ GET /chat/sessions (legacy) - Status: {response.status_code}")
            results.append(("GET /chat/sessions", f"FAILED: {response.status_code}"))
    except Exception as e:
        print(f"❌ GET /chat/sessions (legacy) - Error: {str(e)}")
        results.append(("GET /chat/sessions", f"ERROR: {str(e)}"))

    # Test unified sessions list
    try:
        response = requests.get(f"{BASE_URL}/api/v1/chat/sessions")
        if response.status_code == 200:
            sessions = response.json()
            session_count = sessions.get("total", 0)
            print(f"✅ GET /api/v1/chat/sessions (unified) - Active sessions: {session_count}")
            results.append(("GET /api/v1/chat/sessions", "PASSED"))
        else:
            print(f"❌ GET /api/v1/chat/sessions (unified) - Status: {response.status_code}")
            results.append(("GET /api/v1/chat/sessions", f"FAILED: {response.status_code}"))
    except Exception as e:
        print(f"❌ GET /api/v1/chat/sessions (unified) - Error: {str(e)}")
        results.append(("GET /api/v1/chat/sessions", f"ERROR: {str(e)}"))

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in results if result == "PASSED")
    failed = sum(1 for _, result in results if "FAILED" in result or "ERROR" in result)

    print(f"\nTotal Tests: {len(results)}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")

    if failed > 0:
        print("\nFailed Tests:")
        for endpoint, result in results:
            if result != "PASSED":
                print(f"  - {endpoint}: {result}")

    return passed, failed


def test_websocket_endpoints():
    """Test WebSocket endpoints"""

    print("\n" + "=" * 60)
    print("TESTING WEBSOCKET ENDPOINTS")
    print("=" * 60)

    results = []

    # Test legacy WebSocket
    print("\n1. Testing Legacy WebSocket (/chat/ws):")
    print("-" * 40)

    try:
        ws_url = "ws://localhost:5024/chat/ws"
        ws = websocket.create_connection(ws_url)

        # Should receive connection message
        response = ws.recv()
        data = json.loads(response)

        if data.get("type") == "connection":
            print(f"✅ Connected to /chat/ws - Session: {data.get('session_id', '')[:8]}...")
            results.append(("WebSocket /chat/ws", "PASSED"))

            # Send a test message
            ws.send(json.dumps({
                "type": "message",
                "message": "Test from legacy WebSocket"
            }))

            # Wait for response
            response = ws.recv()
            data = json.loads(response)
            print(f"   Received response type: {data.get('type')}")

            ws.close()
        else:
            print(f"❌ Failed to connect to /chat/ws - Unexpected response")
            results.append(("WebSocket /chat/ws", "FAILED: Bad response"))
    except Exception as e:
        print(f"❌ WebSocket /chat/ws - Error: {str(e)}")
        results.append(("WebSocket /chat/ws", f"ERROR: {str(e)}"))

    # Test unified WebSocket
    print("\n2. Testing Unified WebSocket (/api/v1/chat/ws):")
    print("-" * 40)

    try:
        ws_url = "ws://localhost:5024/api/v1/chat/ws"
        ws = websocket.create_connection(ws_url)

        # Should receive connection message
        response = ws.recv()
        data = json.loads(response)

        if data.get("type") == "connection":
            print(f"✅ Connected to /api/v1/chat/ws - Session: {data.get('session_id', '')[:8]}...")
            results.append(("WebSocket /api/v1/chat/ws", "PASSED"))

            # Send a test message
            ws.send(json.dumps({
                "type": "message",
                "message": "Test from unified WebSocket"
            }))

            # Wait for response
            response = ws.recv()
            data = json.loads(response)
            print(f"   Received response type: {data.get('type')}")

            ws.close()
        else:
            print(f"❌ Failed to connect to /api/v1/chat/ws - Unexpected response")
            results.append(("WebSocket /api/v1/chat/ws", "FAILED: Bad response"))
    except Exception as e:
        print(f"❌ WebSocket /api/v1/chat/ws - Error: {str(e)}")
        results.append(("WebSocket /api/v1/chat/ws", f"ERROR: {str(e)}"))

    # Summary
    print("\n" + "=" * 60)
    print("WEBSOCKET TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in results if result == "PASSED")
    failed = sum(1 for _, result in results if "FAILED" in result or "ERROR" in result)

    print(f"\nTotal Tests: {len(results)}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")

    return passed, failed


if __name__ == "__main__":
    print("🚀 Starting Chat Endpoint Tests")
    print("Testing backward compatibility layer for chat endpoints")
    print("This uses existing database structures - no new tables created")
    print()

    # Test REST endpoints
    rest_passed, rest_failed = test_rest_endpoints()

    # Test WebSocket endpoints
    ws_passed, ws_failed = test_websocket_endpoints()

    # Overall summary
    print("\n" + "=" * 60)
    print("OVERALL TEST RESULTS")
    print("=" * 60)

    total_passed = rest_passed + ws_passed
    total_failed = rest_failed + ws_failed
    total_tests = total_passed + total_failed

    print(f"\nTotal Tests Run: {total_tests}")
    print(f"✅ Total Passed: {total_passed}")
    print(f"❌ Total Failed: {total_failed}")

    if total_failed == 0:
        print("\n🎉 All tests passed! Chat endpoints are working correctly.")
        print("✨ Both legacy and unified paths are operational.")
        print("📦 No new database structures were created.")
    else:
        print(f"\n⚠️  {total_failed} tests failed. Please review the errors above.")
        print("Some endpoints may need attention.")

    print("\n✅ Testing complete!")