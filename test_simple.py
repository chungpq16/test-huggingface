#!/usr/bin/env python3
"""
Minimal Python script to test Bosch Llama API
Equivalent to the curl command provided
"""

import requests
import json
import sys

def test_bosch_api():
    """Test the Bosch Llama API with minimal setup"""
    
    # Configuration - Replace with your actual token
    API_ENDPOINT = "https://ews-esz-emea.api.bosch.com/it/application/llamashared/prod/v1/chat/completions"
    KEY_ID = input("Enter your KeyId token: ").strip()
    
    if not KEY_ID:
        print("❌ KeyId token is required!")
        return False
    
    # Headers exactly as in curl
    headers = {
        "accept": "application/json",
        "KeyId": KEY_ID,
        "Content-Type": "application/json"
    }
    
    # Payload exactly as in curl
    payload = {
        "messages": [{"role": "user", "content": "Hello"}],
        "max_tokens": 2048,
        "model": "meta-llama/Meta-Llama-3-70B-Instruct"
    }
    
    print(f"🚀 Making API call to: {API_ENDPOINT}")
    print(f"📦 Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(
            API_ENDPOINT,
            headers=headers,
            json=payload,
            timeout=30
        )
        
        print(f"📈 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Success!")
            print(f"📄 Full Response: {json.dumps(result, indent=2)}")
            
            # Extract AI message
            if "choices" in result and len(result["choices"]) > 0:
                ai_message = result["choices"][0]["message"]["content"]
                print(f"\n💬 AI Response: {ai_message}")
            
            return True
        else:
            print(f"❌ Failed with status {response.status_code}")
            print(f"📄 Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ JSON decode error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    print("🤖 Bosch Llama API Test")
    print("=" * 30)
    success = test_bosch_api()
    sys.exit(0 if success else 1)
