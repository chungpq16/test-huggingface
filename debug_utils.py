#!/usr/bin/env python3
"""
Debug utilities for the chatbot application.
This script helps with debugging and monitoring the chatbot.
"""

import os
import json
from datetime import datetime
from dotenv import load_dotenv

def check_environment():
    """Check if all required environment variables are set."""
    load_dotenv()
    
    print("🔍 Environment Check")
    print("=" * 40)
    
    required_vars = ["LLAMA_API_KEY", "LLAMA_BASE_URL"]
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            if var == "LLAMA_API_KEY":
                print(f"✅ {var}: {'*' * (len(value) - 4)}{value[-4:]}")
            else:
                print(f"✅ {var}: {value}")
        else:
            print(f"❌ {var}: Not set")
    
    print()

def test_api_connection():
    """Test connection to the LLM API endpoint."""
    import requests
    
    load_dotenv()
    
    print("🌐 API Connection Test")
    print("=" * 40)
    
    api_key = os.getenv("LLAMA_API_KEY")
    base_url = os.getenv("LLAMA_BASE_URL")
    
    if not api_key or not base_url:
        print("❌ Missing API credentials")
        return False
    
    url = f"{base_url}/chat/completions"
    headers = {
        "accept": "application/json",
        "KeyId": api_key,
        "Content-Type": "application/json"
    }
    
    payload = {
        "messages": [{"role": "user", "content": "Hello, this is a test"}],
        "max_tokens": 100,
        "model": "meta-llama/Meta-Llama-3-70B-Instruct"
    }
    
    try:
        print(f"📡 Testing endpoint: {url}")
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ API connection successful!")
            data = response.json()
            if "choices" in data and len(data["choices"]) > 0:
                content = data["choices"][0].get("message", {}).get("content", "")
                print(f"🤖 Response preview: {content[:100]}...")
            return True
        else:
            print(f"❌ API error: {response.status_code}")
            print(f"📝 Response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Request timeout (30s)")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ Connection error - check your internet and endpoint")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False

def show_log_tail(lines=20):
    """Show the last N lines of the debug log."""
    print(f"📋 Debug Log (last {lines} lines)")
    print("=" * 40)
    
    try:
        with open('chatbot_debug.log', 'r') as f:
            all_lines = f.readlines()
            recent_lines = all_lines[-lines:]
            
            for line in recent_lines:
                print(line.rstrip())
                
    except FileNotFoundError:
        print("📝 No log file found yet. Run the chatbot first to generate logs.")

def analyze_logs():
    """Analyze the debug log for common issues."""
    print("🔍 Log Analysis")
    print("=" * 40)
    
    try:
        with open('chatbot_debug.log', 'r') as f:
            content = f.read()
            
        # Count different log levels
        error_count = content.count(' - ERROR - ')
        warning_count = content.count(' - WARNING - ')
        info_count = content.count(' - INFO - ')
        debug_count = content.count(' - DEBUG - ')
        
        print(f"📊 Log Statistics:")
        print(f"   🔴 Errors: {error_count}")
        print(f"   🟡 Warnings: {warning_count}")
        print(f"   🔵 Info: {info_count}")
        print(f"   🟢 Debug: {debug_count}")
        
        # Look for common issues
        if "Failed to initialize" in content:
            print("\n⚠️  Found initialization failures")
            
        if "timeout" in content.lower():
            print("⚠️  Found timeout issues")
            
        if "connection" in content.lower():
            print("⚠️  Found connection issues")
            
        if error_count == 0:
            print("\n✅ No errors found in logs")
            
    except FileNotFoundError:
        print("📝 No log file found yet.")

def main():
    """Run all debug checks."""
    print("🤖 Chatbot Debug Utility")
    print("=" * 50)
    print()
    
    # Check environment
    check_environment()
    
    # Test API connection
    test_api_connection()
    print()
    
    # Show recent logs
    show_log_tail(10)
    print()
    
    # Analyze logs
    analyze_logs()

if __name__ == "__main__":
    main()
