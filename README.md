# LlamaShared Chatbot

A minimal chatbot application using LlamaShared API with LangChain, LangGraph, and Streamlit.

## Features

- 🦙 Custom LangChain LLM for LlamaShared API
- 🛠️ Tool integration with LangGraph ReAct agent
- 🌐 Streamlit web interface
- 🔧 SSL certificate verification options
- 📝 Debug logging support
- 🏗️ Modular folder structure

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your actual API credentials
   ```

3. **Run the application:**
   ```bash
   cd frontend
   streamlit run app.py
   ```

## Environment Variables

- `LLAMASHARED_API_URL`: Your LlamaShared API endpoint
- `LLAMASHARED_API_KEY`: Your API token  
- `SSL_VERIFY`: Enable/disable SSL verification (true/false)
- `MODEL_NAME`: Model to use (default: meta-llama/Meta-Llama-3-70B-Instruct)
- `DEBUG`: Enable debug logging (true/false)

## Project Structure

```
llamashared-chatbot/
├── llm/                    # LLM integration
│   └── llamashared_llm.py  # Custom LangChain LLM
├── tools/                  # Tool definitions
│   └── tools.py           # Hello & Calculator tools
├── frontend/              # Streamlit interface
│   └── app.py            # Main application
├── requirements.txt       # Dependencies
├── .env.example          # Environment template
└── README.md            # This file
```

## Available Tools

1. **Hello Tool**: Simple greeting function
2. **Calculate Tool**: Basic math operations (add, subtract, multiply, divide)

## Tool Choice Behavior

The application sets `"tool_choice": "auto"` in the API payload, allowing the LLM to:
- Decide whether to use tools or respond directly
- Choose which tool to use based on the user's input
- Call multiple tools if needed

## Usage Examples

- "Hello there!" → Direct LLM response
- "Say hello to Alice" → Uses hello_tool
- "Calculate 15 + 27" → Uses calculate_tool
- "What's 100 divided by 5?" → Uses calculate_tool

## Debug Mode

Enable debug logging by setting `DEBUG=true` in your `.env` file to see:
- API request/response details
- Tool invocations
- Agent decision making

## SSL Configuration

If you need to disable SSL verification (not recommended for production):
```bash
SSL_VERIFY=false
```
