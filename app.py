import streamlit as st
import requests
import json
from typing import Dict, Any, List
from langchain.tools import BaseTool
from langchain.schema import BaseMessage, HumanMessage, AIMessage
from langchain.callbacks.manager import CallbackManagerForToolRun
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.memory import ConversationBufferMemory
from langchain.schema.runnable import RunnablePassthrough
import os
from datetime import datetime

# Custom LLM class for Hugging Face API
class HuggingFaceLLM:
    def __init__(self, api_endpoint: str, api_key: str):
        self.api_endpoint = api_endpoint
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def invoke(self, messages: List[BaseMessage]) -> str:
        """Convert messages to API format and get response"""
        formatted_messages = []
        for msg in messages:
            if isinstance(msg, HumanMessage):
                formatted_messages.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                formatted_messages.append({"role": "assistant", "content": msg.content})
            else:
                formatted_messages.append({"role": "system", "content": msg.content})
        
        payload = {
            "messages": formatted_messages,
            "max_tokens": 1000,
            "temperature": 0.7
        }
        
        try:
            response = requests.post(
                f"{self.api_endpoint}/v1/chat/completions",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"]
        except Exception as e:
            return f"Error calling API: {str(e)}"

# Dummy tool for demonstration
class WeatherTool(BaseTool):
    name: str = "get_weather"
    description: str = "Get current weather information for a given city. Input should be the city name."
    
    def _run(
        self, 
        city: str, 
        run_manager: CallbackManagerForToolRun = None
    ) -> str:
        """Get weather information for a city (dummy implementation)"""
        # This is a dummy implementation
        weather_data = {
            "New York": "Sunny, 22°C",
            "London": "Cloudy, 15°C", 
            "Tokyo": "Rainy, 18°C",
            "Paris": "Partly cloudy, 20°C",
            "Sydney": "Sunny, 25°C"
        }
        
        city_clean = city.strip().title()
        weather = weather_data.get(city_clean, f"Weather data not available for {city_clean}. Assume it's pleasant!")
        return f"Weather in {city_clean}: {weather}"

class CalculatorTool(BaseTool):
    name: str = "calculator"
    description: str = "Perform basic mathematical calculations. Input should be a mathematical expression like '2 + 3' or '10 * 5'."
    
    def _run(
        self, 
        expression: str, 
        run_manager: CallbackManagerForToolRun = None
    ) -> str:
        """Calculate mathematical expressions (dummy implementation)"""
        try:
            # Simple eval for basic math (in production, use a safer math parser)
            allowed_chars = set('0123456789+-*/().,')
            if all(c in allowed_chars or c.isspace() for c in expression):
                result = eval(expression)
                return f"Result: {result}"
            else:
                return "Error: Only basic mathematical operations are allowed"
        except Exception as e:
            return f"Error calculating: {str(e)}"

# Streamlit app configuration
st.set_page_config(
    page_title="HuggingFace Chatbot",
    page_icon="🤖",
    layout="centered"
)

# App title
st.title("🤖 HuggingFace AI Chatbot")
st.markdown("Chat with your private AI model with enhanced capabilities!")

# Sidebar for configuration
with st.sidebar:
    st.header("Configuration")
    api_endpoint = st.text_input(
        "API Endpoint", 
        value="http://localhost:8000",
        help="Your HuggingFace model API endpoint"
    )
    api_key = st.text_input(
        "API Key", 
        type="password",
        help="Your API key for authentication"
    )
    
    if st.button("Clear Chat History"):
        if "messages" in st.session_state:
            st.session_state.messages = []
        if "memory" in st.session_state:
            st.session_state.memory.clear()
        st.rerun()

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "memory" not in st.session_state:
    st.session_state.memory = ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True
    )

# Initialize LLM and tools
if api_endpoint and api_key:
    llm = HuggingFaceLLM(api_endpoint, api_key)
    tools = [WeatherTool(), CalculatorTool()]
    
    # Create a simple chat interface without complex agent setup
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("What would you like to know?"):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Process the message
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                # Check if the user is asking for tool usage
                prompt_lower = prompt.lower()
                
                # Simple tool routing
                if "weather" in prompt_lower:
                    # Extract city from prompt (simple approach)
                    words = prompt.split()
                    city = "New York"  # default
                    for i, word in enumerate(words):
                        if word.lower() in ["in", "for", "at"] and i + 1 < len(words):
                            city = words[i + 1]
                            break
                    
                    weather_tool = WeatherTool()
                    tool_result = weather_tool._run(city)
                    
                    # Get LLM response with tool result
                    messages = [
                        HumanMessage(content=f"User asked: {prompt}\nWeather tool result: {tool_result}\nPlease provide a helpful response based on this information.")
                    ]
                    response = llm.invoke(messages)
                    
                elif any(op in prompt_lower for op in ["calculate", "math", "+", "-", "*", "/", "="]):
                    # Extract mathematical expression
                    calc_tool = CalculatorTool()
                    # Simple extraction - in production, use better parsing
                    import re
                    math_pattern = r'[\d\+\-\*/\(\)\s\.]+'
                    math_expressions = re.findall(math_pattern, prompt)
                    
                    if math_expressions:
                        expression = math_expressions[0].strip()
                        tool_result = calc_tool._run(expression)
                    else:
                        tool_result = "Could not extract mathematical expression"
                    
                    messages = [
                        HumanMessage(content=f"User asked: {prompt}\nCalculator result: {tool_result}\nPlease provide a helpful response.")
                    ]
                    response = llm.invoke(messages)
                    
                else:
                    # Regular chat without tools
                    messages = [HumanMessage(content=prompt)]
                    response = llm.invoke(messages)
                
                st.markdown(response)
        
        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response})

else:
    st.warning("Please configure your API endpoint and key in the sidebar to start chatting!")
    
    # Show example usage
    st.markdown("""
    ### Available Features:
    - **Weather Information**: Ask about weather in different cities
      - Example: "What's the weather in Tokyo?"
    - **Calculator**: Perform mathematical calculations
      - Example: "Calculate 15 * 7 + 3"
    - **General Chat**: Ask any questions and have conversations
    
    ### Setup Instructions:
    1. Enter your HuggingFace model API endpoint in the sidebar
    2. Provide your API key
    3. Start chatting!
    """)
