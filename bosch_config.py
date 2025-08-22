# Bosch Llama API Configuration
"""
Configuration template for Bosch Llama API chatbot.
Copy this file to config.py and fill in your actual values.
"""

# Bosch API Configuration
BOSCH_API_ENDPOINT = "https://ews-esz-emea.api.bosch.com/it/application/llamashared/prod/v1/chat/completions"
BOSCH_KEY_ID = "your-key-id-token-here"  # Replace with your actual KeyId token

# Model Configuration
DEFAULT_MODEL = "meta-llama/Meta-Llama-3-70B-Instruct"
DEFAULT_MAX_TOKENS = 2048
DEFAULT_TEMPERATURE = 0.7

# Streamlit Configuration
APP_TITLE = "Bosch Llama AI Chatbot"
APP_ICON = "🤖"

# Debug Configuration
DEBUG_MODE = False
VERBOSE_LOGGING = True

# Example curl command for reference:
"""
curl -X 'POST' \
 'https://ews-esz-emea.api.bosch.com/it/application/llamashared/prod/v1/chat/completions' \
 -H 'accept: application/json' \
 -H 'KeyId: <your-token>' \
 -H 'Content-Type: application/json' \
 -d '{
 "messages": [{"role": "user", "content": "Hello"}],
 "max_tokens": 2048,
 "model": "meta-llama/Meta-Llama-3-70B-Instruct"
 }'
"""
