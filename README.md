# Simple LLM Chatbot

A minimal chatbot using LangChain, Streamlit, and your custom LLM endpoint.

## Features
- LangChain integration with custom OpenAI-compatible API
- Streamlit web interface
- Simple hello tool that the LLM can use
- Agent that decides when to use tools vs direct response
- **Comprehensive debug logging**

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure your API credentials in `.env`:
```
LLAMA_API_KEY=your_actual_token_here
LLAMA_BASE_URL=https://dummy.chat/it/application/llamashared/prod/v1
```

3. Run the chatbot:
```bash
streamlit run chatbot.py
```

## Usage

The chatbot will automatically decide whether to:
- Use the hello tool when appropriate (e.g., "Say hello to Alice")
- Respond directly for general questions

## Debug Features

### Debug Logging
- All interactions are logged to `chatbot_debug.log`
- Logs include API calls, tool usage, errors, and response times
- View recent logs directly in the Streamlit sidebar

### Debug Utility
Run the debug utility to check your setup:
```bash
python debug_utils.py
```

This will:
- ✅ Check environment variables
- 🌐 Test API connection
- 📋 Show recent log entries
- 🔍 Analyze logs for common issues

### Log Levels
- **ERROR**: Critical issues that prevent operation
- **INFO**: General application flow
- **DEBUG**: Detailed information for troubleshooting

### Common Debug Scenarios

1. **API Connection Issues**:
   - Check logs for "Failed to initialize LLM"
   - Verify API credentials in `.env`
   - Run `python debug_utils.py` to test connection

2. **Tool Usage**:
   - Look for "hello_tool called with name:" in logs
   - Check if agent is choosing tools vs direct response

3. **Performance**:
   - Response times are logged for each interaction
   - Monitor for timeout issues

## Example Interactions

- **Tool usage**: "Say hello to John" → Uses hello_tool
- **Direct response**: "What is 2+2?" → Direct LLM response
- **General chat**: "Tell me a joke" → Direct LLM response
