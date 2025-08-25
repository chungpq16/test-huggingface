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
    
    # Test 1: Simple payload without tools
    print("🧪 Test 1: Simple call without tools")
    test_simple_call(api_url, api_key, model_name, ssl_verify)
    
    print("\n" + "="*60 + "\n")
    
    # Test 2: Payload with tools
    print("🧪 Test 2: Call with tools")
    test_with_tools(api_url, api_key, model_name, ssl_verify)

def test_simple_call(api_url, api_key, model_name, ssl_verify):
    """Test simple API call without tools"""
    payload = {
        "messages": [{"role": "user", "content": "Hello"}],
        "model": model_name,
        "max_tokens": 100,
        "temperature": 0.7
    }
    
    make_api_call("Simple Call", payload, api_url, api_key, ssl_verify)

def test_with_tools(api_url, api_key, model_name, ssl_verify):
    """Test API call with tools"""
    
    # Define tools in OpenAI format
    tools = [
        {
            "type": "function",
            "function": {
                "name": "hello_tool",
                "description": "A simple hello tool that greets someone.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "The name to greet (default: 'World')",
                            "default": "World"
                        }
                    },
                    "required": []
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "calculate_tool",
                "description": "A simple calculator tool that performs basic math operations.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "operation": {
                            "type": "string",
                            "description": "The operation to perform (add, subtract, multiply, divide)"
                        },
                        "a": {
                            "type": "number",
                            "description": "First number"
                        },
                        "b": {
                            "type": "number", 
                            "description": "Second number"
                        }
                    },
                    "required": ["operation", "a", "b"]
                }
            }
        }
    ]
    
    payload = {
        "messages": [{"role": "user", "content": "Say hello to Alice"}],
        "model": model_name,
        "max_tokens": 100,
        "temperature": 0.7,
        "tools": tools,
        "tool_choice": "auto"
    }
    
    make_api_call("With Tools", payload, api_url, api_key, ssl_verify)

def make_api_call(test_name, payload, api_url, api_key, ssl_verify):
    """Make the actual API call"""
    headers = {
        "accept": "application/json",
        "KeyId": api_key,
        "Content-Type": "application/json"
    }
    
    print(f"🔍 {test_name}")
    print(f"📦 Payload: {json.dumps(payload, indent=2)}")
    print("-" * 40)
    
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
