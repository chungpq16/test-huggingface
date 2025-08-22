#!/usr/bin/env python3
"""
Simple test script for Bosch Llama API
Run this to verify your API connection before using the full chatbot.
"""

import requests
import json
import sys

def test_bosch_api():
    """Test the Bosch Llama API with a simple request"""
    
    # Configuration - Update these with your actual values
    API_ENDPOINT = "https://ews-esz-emea.api.bosch.com/it/application/llamashared/prod/v1/chat/completions"
    KEY_ID = input("Enter your KeyId token: ").strip()
    
    if not KEY_ID:
        print("❌ KeyId token is required!")
        return False
    
    # Headers exactly as specified in the curl command
    headers = {
        "accept": "application/json",
        "KeyId": KEY_ID,
        "Content-Type": "application/json"
    }
    
    # Payload exactly as specified in the curl command
    payload = {
        "messages": [{"role": "user", "content": "Hello"}],
        "max_tokens": 2048,
        "model": "meta-llama/Meta-Llama-3-70B-Instruct"
    }
    
    print(f"🌐 Testing API endpoint: {API_ENDPOINT}")
    print(f"🔑 Using KeyId: {KEY_ID[:10]}...")
    print(f"📦 Payload: {json.dumps(payload, indent=2)}")
    print("🚀 Making API call...")
    
    try:
        response = requests.post(
            API_ENDPOINT,
            headers=headers,
            json=payload,
            timeout=30
        )
        
        print(f"📈 Response status: {response.status_code}")
        print(f"📋 Response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ API call successful!")
            print(f"📝 Response: {json.dumps(result, indent=2)}")
            
            # Extract the actual message content
            if "choices" in result and len(result["choices"]) > 0:
                content = result["choices"][0]["message"]["content"]
                print(f"💬 AI Response: {content}")
            
            return True
        else:
            print(f"❌ API call failed with status {response.status_code}")
            print(f"📄 Response text: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out after 30 seconds")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ Connection error - check your internet connection and API endpoint")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False

def main():
    """Main function"""
    print("🤖 Bosch Llama API Test Script")
    print("=" * 40)
    
    success = test_bosch_api()
    
    if success:
        print("\n✅ Test completed successfully!")
        print("🚀 You can now run the full chatbot with: streamlit run enhanced_app.py")
    else:
        print("\n❌ Test failed!")
        print("🔧 Please check your KeyId token and network connection")
        print("📖 Refer to the curl command in bosch_config.py for reference")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
