# Configuration file for HuggingFace Chatbot
# Copy this file to config.py and fill in your values

# API Configuration
API_ENDPOINT = "http://localhost:8000"  # Your HuggingFace model API endpoint
API_KEY = "your-api-key-here"           # Your API key

# App Configuration
APP_TITLE = "🤖 HuggingFace AI Chatbot"
MAX_TOKENS = 1000
TEMPERATURE = 0.7
TIMEOUT = 30

# Tool Configuration
ENABLE_WEATHER_TOOL = True
ENABLE_CALCULATOR_TOOL = True
ENABLE_TIME_TOOL = True

# Default cities for weather tool
DEFAULT_WEATHER_CITIES = [
    "New York", "London", "Tokyo", "Paris", 
    "Sydney", "San Francisco", "Berlin"
]
