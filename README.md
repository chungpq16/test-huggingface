# LLM Agent Chat Application

A minimal Streamlit application that integrates with a custom LLM farm API using LangChain's ReAct agent pattern.

## Features

- 🤖 **Custom LLM Integration**: Connects to your LLM farm API endpoint
- 🛠️ **Tool Support**: Includes hello tool and calculator tool
- 🔧 **ReAct Agent**: Uses LangChain's create_react_agent for intelligent tool usage
- 🔒 **SSL Configuration**: Option to disable SSL verification
- 📋 **Debug Logging**: Comprehensive logging for troubleshooting
- 🎨 **Clean UI**: Modern Streamlit interface

## Project Structure

```
.
├── app.py                 # Main Streamlit application
├── config/
│   └── __init__.py       # Configuration management
├── llm/
│   └── __init__.py       # Custom LLM implementation
├── tools/
│   └── __init__.py       # Tool definitions
├── agent/
│   └── __init__.py       # ReAct agent implementation
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables template
├── .gitignore           # Git ignore rules
└── README.md            # This file
```

## Setup

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your actual values
   ```

3. **Set Environment Variables**
   ```bash
   # Required
   LLM_API_URL=https://your-llm-farm-endpoint/v1/chat/completions
   LLM_API_KEY=your_api_key_here
   
   # Optional
   LLM_MODEL=meta-llama/Meta-Llama-3-70B-Instruct
   VERIFY_SSL=false
   DEBUG=true
   MAX_TOKENS=2048
   TEMPERATURE=0.7
   ```

4. **Run the Application**
   ```bash
   streamlit run app.py
   ```

## Configuration Options

### Environment Variables

- `LLM_API_URL`: Your LLM farm API endpoint
- `LLM_API_KEY`: API key for authentication (used as KeyId header)
- `LLM_MODEL`: Model name to use
- `VERIFY_SSL`: Set to `false` to disable SSL verification
- `DEBUG`: Enable debug logging
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)
- `MAX_TOKENS`: Maximum tokens for response
- `TEMPERATURE`: Model temperature (0.0-1.0)
- `TOP_P`: Model top_p parameter

### Jira Configuration (Optional)

To connect to a real Jira instance:

```bash
JIRA_SERVER_URL=https://your-company.atlassian.net
JIRA_USERNAME=your-email@company.com
JIRA_API_TOKEN=your_jira_api_token
```

**Note**: If Jira is not configured, the tool will use mock data for demonstration.

### SSL Configuration

If you're using a self-signed certificate or need to disable SSL verification:

```bash
VERIFY_SSL=false
```

## Available Tools

### Hello Tool
- **Name**: `hello_tool`
- **Description**: A simple greeting tool
- **Usage**: "Say hello to John" or "Greet me"

### Calculator Tool
- **Name**: `calculator_tool`
- **Description**: Performs basic mathematical calculations
- **Usage**: "Calculate 2+2" or "What's 15*7?"

### Jira Issues Tool
- **Name**: `jira_get_issues`
- **Description**: Retrieves Jira issues with optional project filtering
- **Usage**: 
  - "Show me all Jira issues"
  - "Get issues from project DEMO"
  - "List tickets from ABC project"

## API Integration

The application integrates with LLM farm APIs that are compatible with OpenAI's chat completions format. It supports:

- Custom headers (KeyId for authentication)
- Full payload specification including advanced parameters
- SSL configuration options
- Comprehensive error handling

## Debugging

### Enable Debug Mode
```bash
DEBUG=true
LOG_LEVEL=DEBUG
```

### View Logs
- Check `app.log` file for detailed logs
- Use the "Show Logs" button in the Streamlit sidebar
- Monitor the console output

### Common Issues

1. **SSL Certificate Errors**
   - Set `VERIFY_SSL=false` in your .env file

2. **API Key Issues**
   - Ensure `LLM_API_KEY` is set correctly
   - Check if your API endpoint is accessible

3. **Model Not Found**
   - Verify the `LLM_MODEL` name matches your API's available models

## Usage Examples

1. **Simple Chat**
   ```
   User: Hello!
   Agent: Hello! How can I help you today?
   ```

2. **Using Tools**
   ```
   User: Calculate 15 * 23
   Agent: I'll calculate that for you.
   [Uses calculator tool]
   Result: 15 * 23 = 345
   ```

3. **Greeting**
   ```
   User: Say hello to Alice
   Agent: I'll greet Alice for you.
   [Uses hello tool]
   Result: Hello, Alice! Nice to meet you! 👋
   ```

## Development

### Adding New Tools

1. Create a new tool class in `tools/__init__.py`:
   ```python
   class MyNewTool(BaseTool):
       name = "my_new_tool"
       description = "Description of what the tool does"
       
       def _run(self, input_param: str) -> str:
           # Tool logic here
           return "Tool result"
   ```

2. Add the tool to `get_available_tools()` function

### Customizing the LLM

Modify the `CustomLLM` class in `llm/__init__.py` to:
- Change request format
- Add custom headers
- Modify response parsing
- Add retry logic

## License

MIT License
