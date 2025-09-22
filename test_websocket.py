#!/usr/bin/env python3
"""Test WebSocket chat with async intent detection"""

import asyncio
import websockets
import json

async def test_chat():
    uri = "ws://localhost:5024/chat/ws"

    async with websockets.connect(uri) as websocket:
        # Wait for connection message
        response = await websocket.recv()
        print(f"Connected: {response}")

        # Send a test message about products
        message = {
            "type": "message",
            "message": "What indica strains do you recommend for sleep?",
            "user_id": "test-user-123"
        }

        await websocket.send(json.dumps(message))
        print(f"Sent: {message['message']}")

        # Receive responses (typing indicator and actual response)
        while True:
            response = await websocket.recv()
            response_data = json.loads(response)
            print(f"Received: {response_data}")

            # Break after receiving the actual message
            if response_data.get("type") == "message":
                break

if __name__ == "__main__":
    asyncio.run(test_chat())