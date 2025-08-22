import streamlit as st
import requests
import json
from typing import List, Dict, Any
from datetime import datetime
import re

# Simple tool binding approach without complex LangChain agents
class ToolRegistry:
    """Simple registry for tools that can be bound to LLM"""
    
    def __init__(self):
        self.tools = {}
        self.register_default_tools()
    
    def register_tool(self, name: str, func: callable, description: str, keywords: List[str]):
        """Register a tool with the registry"""
        self.tools[name] = {
            'function': func,
            'description': description,
            'keywords': keywords
        }
    
    def register_default_tools(self):
        """Register default tools"""
        # Weather tool
        self.register_tool(
            name="weather",
            func=self.get_weather,
            description="Get weather information for cities",
            keywords=["weather", "temperature", "climate", "forecast", "hot", "cold", "rain", "sunny"]
        )
        
        # Calculator tool
        self.register_tool(
            name="calculator", 
            func=self.calculate,
            description="Perform mathematical calculations",
            keywords=["calculate", "math", "compute", "+", "-", "*", "/", "=", "plus", "minus", "times", "divide"]
        )
        
        # Time tool
        self.register_tool(
            name="time",
            func=self.get_time,
            description="Get current date and time", 
            keywords=["time", "date", "clock", "when", "now", "today", "current"]
        )
        
        # Information tool
        self.register_tool(
            name="info",
            func=self.get_info,
            description="Search for general information",
            keywords=["what", "who", "how", "why", "tell me", "explain", "about", "search", "find"]
        )
    
    def get_weather(self, city: str = "New York") -> str:
        """Weather tool implementation"""
        weather_db = {
            "new york": "☀️ Sunny, 22°C (72°F), gentle breeze",
            "london": "🌧️ Light rain, 15°C (59°F), cloudy skies", 
            "tokyo": "⛅ Partly cloudy, 18°C (64°F), humid conditions",
            "paris": "☀️ Clear skies, 20°C (68°F), perfect weather",
            "sydney": "🌞 Sunny, 25°C (77°F), ideal beach weather",
            "san francisco": "🌫️ Foggy, 16°C (61°F), typical SF morning",
            "berlin": "☁️ Overcast, 12°C (54°F), cool and breezy",
            "mumbai": "🌡️ Hot & humid, 32°C (90°F), monsoon season",
            "singapore": "🌦️ Tropical, 28°C (82°F), afternoon storms"
        }
        
        city_key = city.lower().strip()
        weather = weather_db.get(city_key, f"Weather info not available for {city}")
        return f"Weather in {city.title()}: {weather}"
    
    def calculate(self, expression: str) -> str:
        """Calculator tool implementation"""
        try:
            # Security check
            allowed = set('0123456789+-*/().,')
            if not all(c in allowed or c.isspace() for c in expression):
                return "❌ Only basic math operations allowed"
            
            result = eval(expression.strip())
            return f"🧮 {expression} = {result}"
        
        except ZeroDivisionError:
            return "❌ Division by zero error"
        except Exception as e:
            return f"❌ Math error: {str(e)}"
    
    def get_time(self) -> str:
        """Time tool implementation"""
        now = datetime.now()
        return f"🕐 {now.strftime('%A, %B %d, %Y at %I:%M %p')}"
    
    def get_info(self, query: str) -> str:
        """Information search tool implementation"""
        info_db = {
            "python": "🐍 Python is a high-level programming language known for simplicity and readability.",
            "ai": "🤖 Artificial Intelligence simulates human intelligence in machines.",
            "machine learning": "📊 ML enables computers to learn without explicit programming.",
            "langchain": "🔗 LangChain is a framework for developing LLM-powered applications.",
            "streamlit": "⚡ Streamlit is an app framework for ML and Data Science projects.",
            "hugging face": "🤗 Hugging Face provides ML models and datasets.",
            "tools": "🛠️ Tools extend LLM capabilities by providing specific functions.",
            "chatbot": "💬 A chatbot is an AI program designed to simulate conversation."
        }
        
        query_lower = query.lower()
        for key, value in info_db.items():
            if key in query_lower:
                return f"ℹ️ {value}"
        
        return f"ℹ️ Limited info available. This is a demo database."
    
    def detect_tools(self, user_input: str) -> List[str]:
        """Detect which tools should be used based on user input"""
        detected = []
        input_lower = user_input.lower()
        
        for tool_name, tool_info in self.tools.items():
            for keyword in tool_info['keywords']:
                if keyword in input_lower:
                    if tool_name not in detected:
                        detected.append(tool_name)
                    break
        
        return detected
    
    def execute_tool(self, tool_name: str, user_input: str) -> str:
        """Execute a specific tool"""
        if tool_name not in self.tools:
            return f"Tool '{tool_name}' not found"
        
        tool_func = self.tools[tool_name]['function']
        
        try:
            if tool_name == "weather":
                city = self.extract_city(user_input)
                return tool_func(city)
            elif tool_name == "calculator":
                expression = self.extract_math(user_input)
                return tool_func(expression) if expression else "No math expression found"
            elif tool_name == "time":
                return tool_func()
            elif tool_name == "info":
                return tool_func(user_input)
            else:
                return tool_func(user_input)
        
        except Exception as e:
            return f"Error executing {tool_name}: {str(e)}"
    
    def extract_city(self, text: str) -> str:
        """Extract city name from text"""
        words = text.split()
        cities = ["tokyo", "london", "paris", "new york", "sydney", "berlin", "mumbai", "singapore", "san francisco"]
        
        # Look after prepositions
        for i, word in enumerate(words):
            if word.lower() in ["in", "for", "at"] and i + 1 < len(words):
                return words[i + 1].strip(".,!?")
        
        # Look for known cities
        text_lower = text.lower()
        for city in cities:
            if city in text_lower:
                return city.title()
        
        return "New York"
    
    def extract_math(self, text: str) -> str:
        """Extract mathematical expression from text"""
        # Find mathematical patterns
        math_pattern = r'[\d\+\-\*/\(\)\s\.]+'
        matches = re.findall(math_pattern, text)
        
        if matches:
            return max(matches, key=len).strip()
        return ""

class HuggingFaceLLM:
    """Simple HuggingFace API client"""
    
    def __init__(self, api_endpoint: str, api_key: str):
        self.api_endpoint = api_endpoint.rstrip('/')
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def chat(self, messages: List[Dict]) -> str:
        """Send chat request to API"""
        payload = {
            "messages": messages,
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
            return response.json()["choices"][0]["message"]["content"]
        
        except Exception as e:
            return f"API Error: {str(e)}"

class BoundLLM:
    """LLM with bound tools"""
    
    def __init__(self, llm: HuggingFaceLLM, tool_registry: ToolRegistry):
        self.llm = llm
        self.tools = tool_registry
        
    def chat_with_tools(self, user_input: str, chat_history: List[Dict] = None) -> str:
        """Process user input with automatic tool calling"""
        if chat_history is None:
            chat_history = []
        
        # Detect applicable tools
        detected_tools = self.tools.detect_tools(user_input)
        
        # Execute tools if detected
        tool_results = []
        for tool_name in detected_tools:
            result = self.tools.execute_tool(tool_name, user_input)
            tool_results.append(f"**{tool_name.title()} Tool**: {result}")
        
        # Prepare messages for LLM
        messages = []
        
        # Add system message
        if tool_results:
            system_msg = f"""You are a helpful AI assistant with access to tools. 
Tool results for the user's query:

{chr(10).join(tool_results)}

Use these tool results to provide a comprehensive and helpful response to the user."""
        else:
            system_msg = "You are a helpful AI assistant. Provide clear and useful responses."
        
        messages.append({"role": "system", "content": system_msg})
        
        # Add chat history
        messages.extend(chat_history[-6:])  # Keep last 6 messages for context
        
        # Add current user message
        messages.append({"role": "user", "content": user_input})
        
        # Get LLM response
        response = self.llm.chat(messages)
        
        return response

# Streamlit App
def main():
    st.set_page_config(
        page_title="Tool-Bound HuggingFace Chatbot",
        page_icon="🔧",
        layout="centered"
    )
    
    st.title("🔧 Tool-Bound HuggingFace Chatbot")
    st.markdown("*LLM with automatically bound tools*")
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        api_endpoint = st.text_input(
            "API Endpoint",
            value="http://localhost:8000",
            help="HuggingFace API endpoint"
        )
        
        api_key = st.text_input(
            "API Key", 
            type="password",
            help="API authentication key"
        )
        
        st.markdown("---")
        
        st.subheader("🛠️ Bound Tools")
        
        # Initialize tool registry
        if "tool_registry" not in st.session_state:
            st.session_state.tool_registry = ToolRegistry()
        
        tools = st.session_state.tool_registry.tools
        
        for tool_name, tool_info in tools.items():
            st.markdown(f"**{tool_name.title()}**: {tool_info['description']}")
        
        st.markdown("---")
        
        if st.button("🗑️ Clear Chat"):
            st.session_state.messages = []
            st.rerun()
    
    # Initialize chat
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Display messages
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask anything - tools will be used automatically!"):
        if not api_endpoint or not api_key:
            st.error("Please configure API settings in sidebar!")
            return
        
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Process with bound LLM
        with st.chat_message("assistant"):
            with st.spinner("🔧 Processing with tools..."):
                try:
                    # Create LLM and bound LLM
                    llm = HuggingFaceLLM(api_endpoint, api_key)
                    bound_llm = BoundLLM(llm, st.session_state.tool_registry)
                    
                    # Get response with automatic tool calling
                    response = bound_llm.chat_with_tools(
                        prompt, 
                        st.session_state.messages[:-1]  # Exclude current user message
                    )
                    
                    st.markdown(response)
                    
                except Exception as e:
                    error_msg = f"Error: {str(e)}"
                    st.error(error_msg)
                    response = error_msg
        
        # Add response to history
        st.session_state.messages.append({"role": "assistant", "content": response})
    
    # Tool demonstration
    if len(st.session_state.messages) == 0:
        st.markdown("### 🚀 Tool Binding Demo")
        st.markdown("The LLM automatically detects when to use tools based on your input:")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**🌤️ Weather Tool**")
            st.code("What's the weather in Tokyo?")
            
            st.markdown("**🧮 Calculator Tool**") 
            st.code("Calculate 15 * 7 + 3")
        
        with col2:
            st.markdown("**🕐 Time Tool**")
            st.code("What time is it now?")
            
            st.markdown("**ℹ️ Info Tool**")
            st.code("Tell me about Python")

if __name__ == "__main__":
    main()
