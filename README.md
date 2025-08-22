# HuggingFace AI Chatbot

A Streamlit-based chatbot application that connects to your private HuggingFace model API with enhanced tool capabilities.

## Features

- 🤖 **AI Chat**: Connect to your private HuggingFace model via API
- 🌤️ **Weather Tool**: Get weather information for different cities
- 🧮 **Calculator Tool**: Perform mathematical calculations
- 🕐 **Time Tool**: Get current date and time
- 💬 **Clean UI**: Minimal Streamlit interface focused on chatting

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Your API

You have two app options:

#### Option A: Simple App (Recommended)
```bash
streamlit run simple_app.py
```

#### Option B: Advanced App (with LangChain)
```bash
streamlit run app.py
```

### 3. Configure in the App

1. Enter your HuggingFace API endpoint (e.g., `http://localhost:8000`)
2. Enter your API key for authentication
3. Start chatting!

## API Requirements

Your HuggingFace model should expose an endpoint at:
```
POST /v1/chat/completions
```

With the following request format:
```json
{
  "messages": [
    {"role": "user", "content": "Hello!"}
  ],
  "max_tokens": 1000,
  "temperature": 0.7
}
```

And response format:
```json
{
  "choices": [
    {
      "message": {
        "content": "Hello! How can I help you?"
      }
    }
  ]
}
```

## Tool Usage Examples

### Weather Tool
- "What's the weather in Tokyo?"
- "How's the weather in Paris today?"
- "Tell me about the weather in New York"

### Calculator Tool
- "Calculate 15 + 25"
- "What's 12 * 8?"
- "Compute (100 - 25) / 5"

### Time Tool
- "What time is it?"
- "What's the current date?"
- "Show me the time"

## File Structure

```
test-huggingface/
├── app.py              # Advanced chatbot with LangChain
├── simple_app.py       # Simple chatbot (recommended)
├── requirements.txt    # Python dependencies
├── README.md          # This file
└── PRD.md             # Product requirements document
```

## Features Comparison

| Feature | simple_app.py | app.py |
|---------|---------------|--------|
| HuggingFace API Integration | ✅ | ✅ |
| Weather Tool | ✅ | ✅ |
| Calculator Tool | ✅ | ✅ |
| Time Tool | ✅ | ❌ |
| LangChain Integration | ❌ | ✅ |
| Complexity | Low | High |
| Maintenance | Easy | Complex |

## Troubleshooting

### Common Issues

1. **API Connection Failed**
   - Check if your API endpoint is correct
   - Verify your API key is valid
   - Ensure the model server is running

2. **Tool Not Working**
   - Tools are triggered by keywords in your message
   - Try phrases like "weather in [city]" or "calculate [expression]"

3. **Streamlit Issues**
   - Make sure you have the correct Streamlit version installed
   - Try restarting the app if it becomes unresponsive

### Testing Your API

You can test your API endpoint manually:

```bash
curl -X POST "http://localhost:8000/v1/chat/completions" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "Hello!"}],
    "max_tokens": 100,
    "temperature": 0.7
  }'
```

## Development

To extend the chatbot with additional tools:

1. Add new tool methods to the `DummyTools` class in `simple_app.py`
2. Update the `process_user_input` function to handle new keywords
3. Add documentation to this README

## License

This project is for educational and testing purposes.
