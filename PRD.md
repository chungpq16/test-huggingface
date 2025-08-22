# Product Requirements Document (PRD)
## HuggingFace AI Chatbot

### Project Overview
A Streamlit-based chatbot application that interfaces with a private HuggingFace model hosted on local infrastructure, enhanced with custom tools to extend the LLM capabilities.

### Objectives
- Create a minimal, user-friendly chatbot interface
- Integrate with private HuggingFace model API using Bearer token authentication
- Extend LLM capabilities with custom tools
- Provide a clean, focused UI without unnecessary features

### Technical Requirements

#### Core Components
1. **Streamlit Frontend**
   - Minimal UI with title and chat interface
   - No sidebar add-ons or complex features
   - Clean, modern design focused on conversation

2. **LangChain Integration** (Optional)
   - Preferred framework for LLM interactions
   - Tool integration capabilities
   - Memory management for conversation history

3. **API Integration**
   - Connect to private HuggingFace model
   - Use POST method to `/v1/chat/completions`
   - Bearer token authentication with API key

#### Custom Tools
Implement dummy tools to demonstrate LLM extension capabilities:

1. **Weather Tool**
   - Get weather information for cities
   - Dummy data implementation
   - Triggered by weather-related queries

2. **Calculator Tool**
   - Perform basic mathematical calculations
   - Handle arithmetic expressions
   - Error handling for invalid inputs

3. **Time Tool**
   - Return current date and time
   - Simple utility function

### API Specifications

#### Request Format
```
POST /v1/chat/completions
Headers: 
  Authorization: Bearer {API_KEY}
  Content-Type: application/json

Body:
{
  "messages": [
    {"role": "user", "content": "user message"}
  ],
  "max_tokens": 1000,
  "temperature": 0.7
}
```

#### Response Format
```json
{
  "choices": [
    {
      "message": {
        "content": "AI response"
      }
    }
  ]
}
```

### User Interface Requirements

#### Main Interface
- Application title: "🤖 HuggingFace AI Chatbot"
- Chat input box at bottom
- Message history display
- Clean, centered layout

#### Configuration
- API endpoint input field
- API key input field (password type)
- Clear chat history button

#### Tool Integration
- Automatic tool detection based on user input keywords
- Seamless integration with chat flow
- Clear indication when tools are used

### Technical Implementation

#### File Structure
```
test-huggingface/
├── app.py              # Advanced version with LangChain
├── simple_app.py       # Simplified version (recommended)
├── requirements.txt    # Dependencies
├── README.md          # Documentation
└── PRD.md             # This document
```

#### Dependencies
- streamlit
- langchain (optional)
- requests
- Standard Python libraries

### Success Criteria
1. ✅ Successful connection to private HuggingFace API
2. ✅ Functional chat interface with message history
3. ✅ Working dummy tools (weather, calculator, time)
4. ✅ Clean, minimal UI design
5. ✅ Error handling for API failures
6. ✅ Easy configuration and deployment

### Constraints
- No complex UI features or sidebars with add-ons
- Focus on core chatbot functionality
- Minimal dependencies for easy deployment
- Compatible with local infrastructure setup

### Future Enhancements (Out of Scope)
- Advanced tool integrations
- User authentication
- Conversation persistence
- Multi-model support
- Advanced UI features