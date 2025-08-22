# Simple AI Agent Chatbot

A clean and efficient AI agent chatbot built with LangChain and Streamlit. Uses intelligent pattern matching for tool routing that works with any OpenAI-compatible endpoint.

## Features

- 🤖 **Simple Architecture**: Reliable pattern-matching agent that works with any LLM endpoint
- 🔧 **Intelligent Tool Routing**: Smart tool detection and execution
- 🎨 **Streamlit UI**: Clean, interactive web interface
- 🌐 **Universal Compatibility**: Works with any OpenAI-compatible API endpoint
- 📝 **Comprehensive Logging**: File and console logging with configurable levels
- 🔒 **SSL Configuration**: Configurable SSL verification for development
- ⚡ **Multiple Tools**: Hello, weather, and calculator tools included

## Architecture

```
src/
├── __init__.py              # Package initialization
├── main.py                  # Application entry point
├── config/
│   ├── __init__.py
│   └── settings.py          # Configuration management
├── utils/
│   ├── __init__.py
│   └── logging.py           # Logging setup
├── tools/
│   ├── __init__.py
│   ├── hello.py             # Hello/greeting tool
│   ├── weather.py           # Weather information tool
│   ├── calculator.py        # Math calculation tool
│   └── registry.py          # Tool registry
├── llm/
│   ├── __init__.py
│   └── manager.py           # LLM initialization and management
├── agents/
│   ├── __init__.py
│   └── simple_agent.py      # Pattern-matching agent implementation
└── ui/
    ├── __init__.py
    └── streamlit_ui.py       # Streamlit interface
```

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your API credentials
   ```

3. **Run the application:**
   ```bash
   streamlit run app.py
   ```

## Environment Variables

Create a `.env` file with the following variables:

```env
# LLM Configuration
API_KEY=your_api_key_here
BASE_URL=https://your-endpoint.com/v1
MODEL_NAME=Meta-Llama-3-70B-Instruct

# SSL Configuration (for development)
VERIFY_SSL=false

# Logging Configuration
LOG_LEVEL=INFO
```

## Usage

1. **Basic Chat**: Simply type messages and get responses
2. **Tool Usage**: The agent automatically determines when to use tools:
   - "Hello there!" or "Say hello to Alice" (greeting tool)
   - "What's the weather in Tokyo?" (weather tool)
   - "Calculate 15 * 8 + 12" (calculator tool)
   - "What can you help me with?" (general assistance)

## Development

### Adding New Tools

1. Create a new tool file in `src/tools/`:
   ```python
   from langchain.tools import tool
   
   @tool
   def my_tool(input_text: str) -> str:
       """Description of what this tool does."""
       return f"Tool result: {input_text}"
   ```

2. Register the tool in `src/tools/registry.py`:
   ```python
   from .my_tool import my_tool
   
   class ToolRegistry:
       def get_all_tools(self):
           return [hello_tool, my_tool]  # Add your tool here
   ```

### Customizing the Agent

The `SimpleAgent` class in `src/agents/simple_agent.py` handles tool calling through intelligent pattern matching. You can customize:

- Tool call patterns and recognition
- Response formatting and style
- Error handling and fallback behavior
- Chat history management and context

### Configuration

The `Config` class in `src/config/settings.py` manages all configuration. Add new settings by:

1. Adding the environment variable
2. Adding a property to the Config class
3. Adding validation if needed

## Troubleshooting

### SSL Certificate Errors

Set `VERIFY_SSL=false` in your `.env` file for development environments.

### Tool Calling

The agent uses intelligent pattern matching to detect when to use tools. This approach works with any LLM endpoint and doesn't require special function calling support. The agent looks for phrases like:

- Greetings → Uses hello tool
- Weather queries → Uses weather tool  
- Math expressions → Uses calculator tool

### Debug Logging

Check the `logs/` directory for detailed debug information. Logs are organized by date.

## Dependencies

- **LangChain**: LLM integration and tool management
- **Streamlit**: Web interface
- **httpx**: HTTP client with SSL configuration
- **python-dotenv**: Environment variable management

## License

MIT License - see LICENSE file for details.
