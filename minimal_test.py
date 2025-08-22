#!/usr/bin/env python3
"""
Ultra-minimal Python script to test Bosch Llama API
Replace YOUR_TOKEN_HERE with your actual KeyId token
"""

import requests
import json

# Configuration - REPLACE YOUR_TOKEN_HERE with actual token
API_ENDPOINT = "https://ews-esz-emea.api.bosch.com/it/application/llamashared/prod/v1/chat/completions"
KEY_ID = "YOUR_TOKEN_HERE"  # <-- Put your actual token here

# Request exactly matching the curl command
headers = {
    "accept": "application/json",
    "KeyId": KEY_ID,
    "Content-Type": "application/json"
}

payload = {
    "messages": [{"role": "user", "content": "Hello"}],
    "max_tokens": 2048,
    "model": "meta-llama/Meta-Llama-3-70B-Instruct"
}

# Make the request
response = requests.post(API_ENDPOINT, headers=headers, json=payload)

# Print results
print(f"Status: {response.status_code}")
print(f"Response: {response.text}")

if response.status_code == 200:
    result = response.json()
    ai_message = result["choices"][0]["message"]["content"]
    print(f"\nAI says: {ai_message}")
else:
    print("❌ Request failed")
