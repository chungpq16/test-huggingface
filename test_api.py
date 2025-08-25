#!/usr/bin/env python3
"""
Simple test script to debug LlamaShared API calls
"""

import os
import json
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_api_call():
    """Test a simple API call to debug the 400 error"""
    
    api_url = os.getenv("LLAMASHARED_API_URL")
    api_key = os.getenv("LLAMASHARED_API_KEY")
    model_name = os.getenv("MODEL_NAME", "meta-llama/Meta-Llama-3-70B-Instruct")
    ssl_verify = os.getenv("SSL_VERIFY", "true").lower() == "true"
    
    if not api_url or not api_key:
        print("❌ Missing API URL or API Key in .env file")
        return
    
    # Simple payload without tools first
    payload = {
        "messages": [{"role": "user", "content": "Hello"}],
        "model": model_name,
        "max_tokens": 100,
        "temperature": 0.7
    }
    
    headers = {
        "accept": "application/json",
        "KeyId": api_key,
        "Content-Type": "application/json"
    }
    
    print(f"🔍 Testing API call to: {api_url}")
    print(f"🔑 Using API key: {api_key[:8]}...")
    print(f"📦 Payload: {json.dumps(payload, indent=2)}")
    print("=" * 50)
    
    try:
        # Disable SSL warnings if needed
        if not ssl_verify:
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        response = requests.post(
            api_url,
            json=payload,
            headers=headers,
            verify=ssl_verify,
            timeout=30
        )
        
        print(f"📊 Response Status: {response.status_code}")
        print(f"📋 Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            print("✅ Success!")
            response_json = response.json()
            print(f"📝 Response: {json.dumps(response_json, indent=2)}")
        else:
            print(f"❌ Error {response.status_code}")
            try:
                error_json = response.json()
                print(f"💥 Error Response: {json.dumps(error_json, indent=2)}")
            except:
                print(f"💥 Error Text: {response.text}")
                
    except Exception as e:
        print(f"💥 Exception: {e}")

if __name__ == "__main__":
    test_api_call()
