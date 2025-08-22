# Simple LLM Chatbot

A minimal chatbot using LangChain, Streamlit, and your custom LLM endpoint.

## Features
- LangChain integration with custom OpenAI-compatible API
- Streamlit web interface
- Simple hello tool that the LLM can use
- Agent that decides when to use tools vs direct response

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

## Example Interactions

- **Tool usage**: "Say hello to John" → Uses hello_tool
- **Direct response**: "What is 2+2?" → Direct LLM response
- **General chat**: "Tell me a joke" → Direct LLM response
