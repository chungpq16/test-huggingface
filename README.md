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

You have three app options:

#### Option A: Tool-Bound App (Recommended for Tool Binding)
```bash
streamlit run tool_bound_app.py
```
**Features**: Automatic tool detection and binding, simple architecture

#### Option B: Enhanced App (LangChain Integration)
```bash
streamlit run enhanced_app.py
```
**Features**: Full LangChain integration with proper tool binding

#### Option C: Simple App (Basic Functionality)
```bash
streamlit run simple_app.py
```
**Features**: Manual tool routing, no binding

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

## Tool Binding Explanation

### What is Tool Binding?

Tool binding allows the LLM to automatically detect when to use specific tools based on user input and execute them seamlessly. Instead of manually routing requests, the LLM intelligently determines which tools are needed.

### How It Works

1. **Tool Registration**: Tools are registered with descriptions and trigger keywords
2. **Automatic Detection**: The system analyzes user input for tool-relevant keywords  
3. **Tool Execution**: Matching tools are automatically executed
4. **Context Integration**: Tool results are provided to the LLM for comprehensive responses

### Available Bound Tools

#### 🌤️ Weather Tool
- **Triggers**: "weather", "temperature", "climate", "forecast"
- **Function**: Returns weather information for cities
- **Example**: "What's the weather in Tokyo?" → Automatically calls weather tool

#### 🧮 Calculator Tool  
- **Triggers**: "calculate", "math", "+", "-", "*", "/"
- **Function**: Performs mathematical calculations
- **Example**: "Calculate 15 * 7" → Automatically calls calculator tool

#### 🕐 Time Tool
- **Triggers**: "time", "date", "clock", "now"
- **Function**: Returns current date and time
- **Example**: "What time is it?" → Automatically calls time tool

#### ℹ️ Information Tool
- **Triggers**: "what", "tell me", "about", "explain"
- **Function**: Searches knowledge database
- **Example**: "Tell me about Python" → Automatically calls info tool

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
├── tool_bound_app.py      # Tool-bound chatbot (recommended)
├── enhanced_app.py        # LangChain-based tool binding
├── simple_app.py          # Basic chatbot (manual routing)
├── app.py                 # Original LangChain version
├── requirements.txt       # Python dependencies
├── config_template.py     # Configuration template
├── start.sh              # Quick start script
├── README.md             # This file
└── PRD.md                # Product requirements
```

## Features Comparison

| Feature | tool_bound_app.py | enhanced_app.py | simple_app.py | app.py |
|---------|-------------------|-----------------|---------------|--------|
| HuggingFace API | ✅ | ✅ | ✅ | ✅ |
| **Tool Binding** | ✅ **Auto** | ✅ **LangChain** | ❌ Manual | ❌ Manual |
| Weather Tool | ✅ | ✅ | ✅ | ✅ |
| Calculator Tool | ✅ | ✅ | ✅ | ✅ |
| Time Tool | ✅ | ✅ | ✅ | ❌ |
| Info/Search Tool | ✅ | ✅ | ❌ | ❌ |
| Complexity | Low | High | Low | Medium |
| Performance | Fast | Medium | Fast | Medium |
| **Recommended** | ✅ | For LangChain users | Basic use | Legacy |

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
