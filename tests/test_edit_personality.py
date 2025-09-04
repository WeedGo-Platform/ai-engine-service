#!/usr/bin/env python3
import requests
import json

# API base URL
BASE_URL = "http://localhost:8080/api/v1"

# Test editing a personality
def test_edit_personality():
    # First get personalities to find one to edit
    response = requests.get(f"{BASE_URL}/ai/personalities")
    print(f"GET personalities response: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        personalities = data.get("personalities", [])
        if personalities and len(personalities) > 0:
            # Edit the first personality
            personality = personalities[0]
            print(f"\nEditing personality: {personality.get('name', 'Unknown')}")
            
            # Update with all required fields including avatar
            updated_data = {
                "id": personality.get("id"),
                "name": personality.get("name", "Test Budtender"),
                "age": personality.get("age", 25),
                "gender": personality.get("gender", "neutral"),
                "communication_style": personality.get("communication_style", "friendly"),
                "knowledge_level": personality.get("knowledge_level", "expert"),
                "humor_style": personality.get("humor_style", "casual"),
                "humor_level": personality.get("humor_level", "medium"),
                "empathy_level": personality.get("empathy_level", "high"),
                "response_length": personality.get("response_length", "medium"),
                "jargon_level": personality.get("jargon_level", "moderate"),
                "sales_approach": personality.get("sales_approach", "consultative"),
                "formality": personality.get("formality", "casual"),
                "description": "Updated test description with avatar",
                "sample_responses": personality.get("sample_responses", {
                    "greeting": "Hey there! Welcome!",
                    "product_recommendation": "I think you'd love this strain!",
                    "no_stock": "Sorry, we're out of that one.",
                    "closing": "Have a great day!"
                }),
                "traits": personality.get("traits", ["friendly", "knowledgeable"]),
                "active": True,
                "avatar": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==",  # 1x1 red pixel
                "emoji": "🌿"
            }
            
            print(f"\nSending update with fields: {list(updated_data.keys())}")
            print(f"Avatar length: {len(updated_data['avatar'])} chars")
            print(f"Emoji: {updated_data['emoji']}")
            
            # Send update request
            headers = {"Content-Type": "application/json"}
            response = requests.post(
                f"{BASE_URL}/ai/personality",
                headers=headers,
                json=updated_data
            )
            
            print(f"\nPOST personality response: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                print("Update successful!")
                print(f"Response: {json.dumps(result, indent=2)}")
                
                # Verify the update by getting the personality again
                verify_response = requests.get(f"{BASE_URL}/ai/personalities")
                if verify_response.status_code == 200:
                    verify_data = verify_response.json()
                    updated_personalities = verify_data.get("personalities", [])
                    for p in updated_personalities:
                        if p.get("id") == personality.get("id"):
                            print(f"\nVerification - Avatar present: {'avatar' in p and p['avatar'] is not None}")
                            print(f"Verification - Emoji: {p.get('emoji', 'Not set')}")
                            print(f"Verification - Description: {p.get('description', 'Not set')}")
                            break
            else:
                print(f"Update failed: {response.text}")
        else:
            print("No personalities found to edit")
    else:
        print(f"Failed to get personalities: {response.text}")

if __name__ == "__main__":
    test_edit_personality()