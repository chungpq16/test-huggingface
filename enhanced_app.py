import streamlit as st
import requests
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
import re

# LangChain imports for tool binding
from langchain.tools import BaseTool, tool
from langchain.schema import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain.callbacks.manager import CallbackManagerForToolRun
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.memory import ConversationBufferMemory
from langchain_core.language_models import BaseChatModel
from langchain_core.outputs import ChatResult, ChatGeneration
from langchain_core.messages import BaseMessage as CoreBaseMessage
from pydantic import BaseModel, Field

# Custom LLM wrapper for HuggingFace API that supports tool calling
class HuggingFaceChatModel(BaseChatModel):
    """Custom LangChain-compatible LLM for HuggingFace API"""
    
    api_endpoint: str
    api_key: str
    model_name: str = "huggingface-model"
    max_tokens: int = 1000
    temperature: float = 0.7
    
    def __init__(self, api_endpoint: str, api_key: str, **kwargs):
        super().__init__(**kwargs)
        self.api_endpoint = api_endpoint.rstrip('/')
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    @property
    def _llm_type(self) -> str:
        return "huggingface-custom"
    
    def _generate(self, messages: List[CoreBaseMessage], **kwargs) -> ChatResult:
        """Generate response from HuggingFace API"""
        formatted_messages = []
        
        for msg in messages:
            if hasattr(msg, 'content'):
                content = msg.content
                if hasattr(msg, 'type'):
                    if msg.type == "human":
                        formatted_messages.append({"role": "user", "content": content})
                    elif msg.type == "ai":
                        formatted_messages.append({"role": "assistant", "content": content})
                    elif msg.type == "system":
                        formatted_messages.append({"role": "system", "content": content})
                else:
                    # Fallback based on class type
                    if isinstance(msg, HumanMessage):
                        formatted_messages.append({"role": "user", "content": content})
                    elif isinstance(msg, AIMessage):
                        formatted_messages.append({"role": "assistant", "content": content})
                    elif isinstance(msg, SystemMessage):
                        formatted_messages.append({"role": "system", "content": content})
        
        payload = {
            "messages": formatted_messages,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature
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
            content = result["choices"][0]["message"]["content"]
            
            # Create ChatGeneration
            message = AIMessage(content=content)
            generation = ChatGeneration(message=message)
            
            return ChatResult(generations=[generation])
            
        except Exception as e:
            error_content = f"Error calling HuggingFace API: {str(e)}"
            message = AIMessage(content=error_content)
            generation = ChatGeneration(message=message)
            return ChatResult(generations=[generation])

# Define tools using LangChain's @tool decorator
@tool
def get_weather(city: str) -> str:
    """Get current weather information for a given city.
    
    Args:
        city: The name of the city to get weather for
        
    Returns:
        Weather information as a string
    """
    weather_data = {
        "new york": "Sunny, 22°C (72°F), Light breeze from the west",
        "london": "Cloudy, 15°C (59°F), Light rain expected in the evening", 
        "tokyo": "Partly cloudy, 18°C (64°F), Humid with 70% humidity",
        "paris": "Sunny, 20°C (68°F), Clear skies, perfect for sightseeing",
        "sydney": "Sunny, 25°C (77°F), Perfect beach weather with light winds",
        "san francisco": "Foggy, 16°C (61°F), Typical SF morning fog clearing by noon",
        "berlin": "Overcast, 12°C (54°F), Cool and breezy, light jacket recommended",
        "mumbai": "Hot and humid, 32°C (90°F), Monsoon season with scattered showers",
        "singapore": "Tropical, 28°C (82°F), High humidity with afternoon thunderstorms"
    }
    
    city_lower = city.lower().strip()
    weather = weather_data.get(city_lower, f"Weather data not available for {city}. Assume pleasant conditions with moderate temperature.")
    
    return f"🌤️ Weather in {city.title()}: {weather}"

@tool  
def calculate_math(expression: str) -> str:
    """Perform mathematical calculations on a given expression.
    
    Args:
        expression: Mathematical expression to evaluate (e.g., "2 + 3 * 4")
        
    Returns:
        The calculation result as a string
    """
    try:
        # Security check - only allow safe mathematical operations
        allowed_chars = set('0123456789+-*/().,')
        if not all(c in allowed_chars or c.isspace() for c in expression):
            return "❌ Error: Only basic mathematical operations (+, -, *, /, parentheses) and numbers are allowed"
        
        # Evaluate the expression safely
        result = eval(expression.strip())
        return f"🧮 Calculation: {expression} = {result}"
        
    except ZeroDivisionError:
        return "❌ Error: Division by zero is not allowed"
    except SyntaxError:
        return "❌ Error: Invalid mathematical expression"
    except Exception as e:
        return f"❌ Calculation error: {str(e)}"

@tool
def get_current_time() -> str:
    """Get the current date and time.
    
    Returns:
        Current date and time as a formatted string
    """
    now = datetime.now()
    formatted_time = now.strftime('%A, %B %d, %Y at %I:%M %p')
    return f"🕐 Current time: {formatted_time}"

@tool
def search_dummy_database(query: str) -> str:
    """Search a dummy database for information.
    
    Args:
        query: Search query string
        
    Returns:
        Search results from the dummy database
    """
    dummy_data = {
        "python": "Python is a high-level programming language known for its simplicity and readability.",
        "ai": "Artificial Intelligence (AI) refers to the simulation of human intelligence in machines.",
        "machine learning": "Machine Learning is a subset of AI that enables computers to learn without being explicitly programmed.",
        "langchain": "LangChain is a framework for developing applications powered by language models.",
        "streamlit": "Streamlit is an open-source app framework for Machine Learning and Data Science projects."
    }
    
    query_lower = query.lower()
    for key, value in dummy_data.items():
        if key in query_lower:
            return f"📚 Found information about '{key}': {value}"
    
    return f"📚 No specific information found for '{query}'. This is a dummy database with limited data."

# Create the agent with bound tools
def create_agent_with_tools(llm, tools):
    """Create an agent with tools bound to the LLM"""
    
    # Create a prompt template for the agent
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a helpful AI assistant with access to several tools. 
        When a user asks for something that could be answered using a tool, use the appropriate tool.
        
        Available tools:
        - get_weather: Get weather information for cities
        - calculate_math: Perform mathematical calculations  
        - get_current_time: Get current date and time
        - search_dummy_database: Search for information in a dummy database
        
        Always provide helpful, accurate responses and use tools when appropriate."""),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad")
    ])
    
    # Bind tools to the LLM (this creates a tool-calling LLM)
    llm_with_tools = llm.bind_tools(tools)
    
    # Create the agent
    agent = create_tool_calling_agent(llm_with_tools, tools, prompt)
    
    # Create agent executor
    agent_executor = AgentExecutor(
        agent=agent, 
        tools=tools, 
        verbose=True,
        handle_parsing_errors=True,
        max_iterations=3
    )
    
    return agent_executor

# Streamlit App
def main():
    st.set_page_config(
        page_title="Enhanced HuggingFace Chatbot",
        page_icon="🤖",
        layout="centered",
        initial_sidebar_state="expanded"
    )
    
    # Main title
    st.title("🤖 Enhanced HuggingFace AI Chatbot")
    st.markdown("*AI Assistant with LangChain Tool Binding*")
    
    # Sidebar configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        api_endpoint = st.text_input(
            "API Endpoint",
            value=st.session_state.get("api_endpoint", "http://localhost:8000"),
            help="Your HuggingFace model API endpoint"
        )
        
        api_key = st.text_input(
            "API Key",
            type="password", 
            value=st.session_state.get("api_key", ""),
            help="Your authentication API key"
        )
        
        # Save configuration
        st.session_state["api_endpoint"] = api_endpoint
        st.session_state["api_key"] = api_key
        
        st.markdown("---")
        
        # Tool information
        st.subheader("🛠️ Bound Tools")
        st.markdown("""
        **✅ Weather Tool**  
        Get weather for any city
        
        **✅ Calculator Tool**  
        Perform math calculations
        
        **✅ Time Tool**  
        Get current date/time
        
        **✅ Database Search**  
        Search dummy database
        """)
        
        st.markdown("---")
        
        # Agent settings
        st.subheader("🤖 Agent Settings")
        
        use_agent = st.checkbox(
            "Use LangChain Agent", 
            value=st.session_state.get("use_agent", True),
            help="Enable tool binding with LangChain agent"
        )
        st.session_state["use_agent"] = use_agent
        
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.messages = []
            if "memory" in st.session_state:
                st.session_state.memory.clear()
            st.rerun()
    
    # Initialize chat history and memory
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "memory" not in st.session_state:
        st.session_state.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask me anything..."):
        # Check configuration
        if not api_endpoint or not api_key:
            st.error("Please configure your API endpoint and key in the sidebar!")
            return
        
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate response
        with st.chat_message("assistant"):
            with st.spinner("🤔 Thinking..."):
                try:
                    # Initialize LLM
                    llm = HuggingFaceChatModel(api_endpoint=api_endpoint, api_key=api_key)
                    
                    if st.session_state.get("use_agent", True):
                        # Use agent with bound tools - let LLM decide when to use tools
                        tools = [get_weather, calculate_math, get_current_time, search_dummy_database]
                        agent_executor = create_agent_with_tools(llm, tools)
                        
                        # Get chat history for context
                        chat_history = []
                        for msg in st.session_state.messages[-6:]:  # Last 6 messages for context
                            if msg["role"] == "user":
                                chat_history.append(HumanMessage(content=msg["content"]))
                            else:
                                chat_history.append(AIMessage(content=msg["content"]))
                        
                        # Let the agent decide when to use tools
                        result = agent_executor.invoke({
                            "input": prompt,
                            "chat_history": chat_history
                        })
                        response = result["output"]
                    else:
                        # Direct LLM call without tools
                        messages = [HumanMessage(content=prompt)]
                        result = llm._generate(messages)
                        response = result.generations[0].message.content
                    
                    st.markdown(response)
                    
                except Exception as e:
                    error_msg = f"Error: {str(e)}"
                    st.error(error_msg)
                    response = error_msg
        
        # Add to chat history
        st.session_state.messages.append({"role": "assistant", "content": response})
        
        # Update memory
        st.session_state.memory.chat_memory.add_user_message(prompt)
        st.session_state.memory.chat_memory.add_ai_message(response)
    
    # Example prompts
    if len(st.session_state.messages) == 0:
        st.markdown("### 💡 Try these tool-enabled examples:")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🌤️ Weather in Tokyo", use_container_width=True):
                st.session_state.example_prompt = "What's the weather like in Tokyo?"
                st.rerun()
            
            if st.button("🧮 Calculate 127 * 83", use_container_width=True):
                st.session_state.example_prompt = "Calculate 127 * 83"
                st.rerun()
        
        with col2:
            if st.button("🕐 Current time", use_container_width=True):
                st.session_state.example_prompt = "What time is it right now?"
                st.rerun()
            
            if st.button("📚 Search for AI", use_container_width=True):
                st.session_state.example_prompt = "Tell me about artificial intelligence"
                st.rerun()
        
        # Handle example prompts
        if "example_prompt" in st.session_state:
            example = st.session_state.example_prompt
            del st.session_state.example_prompt
            st.session_state.messages.append({"role": "user", "content": example})
            st.rerun()

if __name__ == "__main__":
    main()
