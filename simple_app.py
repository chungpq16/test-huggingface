import streamlit as st
import requests
import json
from datetime import datetime

# Custom Hugging Face API client
class HuggingFaceClient:
    def __init__(self, api_endpoint: str, api_key: str):
        self.api_endpoint = api_endpoint.rstrip('/')
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def chat(self, messages: list) -> str:
        """Send chat request to HuggingFace API"""
        payload = {
            "messages": messages,
            "max_tokens": 1000,
            "temperature": 0.7,
            "stream": False
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
        except requests.exceptions.RequestException as e:
            return f"API Error: {str(e)}"
        except KeyError:
            return "Error: Unexpected API response format"
        except Exception as e:
            return f"Unexpected error: {str(e)}"

# Dummy tools
class DummyTools:
    @staticmethod
    def get_weather(city: str) -> str:
        """Get dummy weather information"""
        weather_data = {
            "new york": "Sunny, 22°C (72°F), Light breeze",
            "london": "Cloudy, 15°C (59°F), Light rain expected",
            "tokyo": "Partly cloudy, 18°C (64°F), Humid",
            "paris": "Sunny, 20°C (68°F), Clear skies",
            "sydney": "Sunny, 25°C (77°F), Perfect beach weather",
            "san francisco": "Foggy, 16°C (61°F), Typical SF weather",
            "berlin": "Overcast, 12°C (54°F), Cool and breezy"
        }
        
        city_lower = city.lower().strip()
        weather = weather_data.get(city_lower, f"Weather data not available for {city}. Assume pleasant conditions!")
        return f"🌤️ Weather in {city.title()}: {weather}"
    
    @staticmethod
    def calculate(expression: str) -> str:
        """Simple calculator tool"""
        try:
            # Basic security check
            allowed_chars = set('0123456789+-*/().,')
            if not all(c in allowed_chars or c.isspace() for c in expression):
                return "❌ Error: Only basic mathematical operations (+, -, *, /, parentheses) are allowed"
            
            result = eval(expression)
            return f"🧮 Calculation: {expression} = {result}"
        except ZeroDivisionError:
            return "❌ Error: Division by zero"
        except Exception as e:
            return f"❌ Calculation error: {str(e)}"
    
    @staticmethod
    def get_current_time() -> str:
        """Get current time"""
        now = datetime.now()
        return f"🕐 Current time: {now.strftime('%Y-%m-%d %H:%M:%S')}"

def process_user_input(user_input: str, hf_client: HuggingFaceClient) -> str:
    """Process user input and determine if tools should be used"""
    user_lower = user_input.lower()
    
    # Check for tool usage patterns
    if any(keyword in user_lower for keyword in ["weather", "temperature", "forecast"]):
        # Extract city name (simple approach)
        words = user_input.split()
        city = "New York"  # default
        
        # Look for city after common prepositions
        for i, word in enumerate(words):
            if word.lower() in ["in", "for", "at", "of"] and i + 1 < len(words):
                city = words[i + 1]
                break
        
        tool_result = DummyTools.get_weather(city)
        
        # Get LLM response incorporating tool result
        messages = [
            {"role": "system", "content": "You are a helpful assistant. Use the tool result to provide a comprehensive response."},
            {"role": "user", "content": f"User asked: {user_input}"},
            {"role": "user", "content": f"Tool result: {tool_result}"}
        ]
        
    elif any(keyword in user_lower for keyword in ["calculate", "math", "compute"]) or any(op in user_input for op in ["+", "-", "*", "/", "="]):
        # Extract mathematical expression
        import re
        # Find mathematical expressions
        math_pattern = r'[\d\+\-\*/\(\)\s\.]+'
        expressions = re.findall(math_pattern, user_input)
        
        if expressions:
            expression = expressions[0].strip()
            tool_result = DummyTools.calculate(expression)
        else:
            tool_result = "Could not identify mathematical expression"
        
        messages = [
            {"role": "system", "content": "You are a helpful assistant. Use the calculation result to provide a comprehensive response."},
            {"role": "user", "content": f"User asked: {user_input}"},
            {"role": "user", "content": f"Calculation result: {tool_result}"}
        ]
        
    elif any(keyword in user_lower for keyword in ["time", "date", "clock"]):
        tool_result = DummyTools.get_current_time()
        
        messages = [
            {"role": "system", "content": "You are a helpful assistant. Use the time information to provide a comprehensive response."},
            {"role": "user", "content": f"User asked: {user_input}"},
            {"role": "user", "content": f"Time info: {tool_result}"}
        ]
        
    else:
        # Regular chat without tools
        messages = [
            {"role": "system", "content": "You are a helpful and friendly AI assistant."},
            {"role": "user", "content": user_input}
        ]
    
    return hf_client.chat(messages)

# Streamlit App
def main():
    st.set_page_config(
        page_title="HuggingFace AI Chatbot",
        page_icon="🤖",
        layout="centered",
        initial_sidebar_state="expanded"
    )
    
    # Main title
    st.title("🤖 HuggingFace AI Chatbot")
    st.markdown("*Chat with your private AI model with enhanced tools*")
    
    # Sidebar configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        api_endpoint = st.text_input(
            "API Endpoint",
            value=st.session_state.get("api_endpoint", "http://localhost:8000"),
            help="Your HuggingFace model API endpoint (without /v1/chat/completions)"
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
        
        # Tools information
        st.subheader("🛠️ Available Tools")
        st.markdown("""
        - **Weather**: Ask about weather in any city
        - **Calculator**: Perform math calculations  
        - **Time**: Get current date and time
        """)
        
        st.markdown("---")
        
        if st.button("🗑️ Clear Chat History", use_container_width=True):
            st.session_state.messages = []
            st.rerun()
    
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask me anything..."):
        # Check if API is configured
        if not api_endpoint or not api_key:
            st.error("Please configure your API endpoint and key in the sidebar!")
            return
        
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate and display assistant response
        with st.chat_message("assistant"):
            with st.spinner("🤔 Thinking..."):
                try:
                    hf_client = HuggingFaceClient(api_endpoint, api_key)
                    response = process_user_input(prompt, hf_client)
                    st.markdown(response)
                except Exception as e:
                    error_msg = f"Error: {str(e)}"
                    st.error(error_msg)
                    response = error_msg
        
        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response})
    
    # Show example prompts if no conversation started
    if len(st.session_state.messages) == 0:
        st.markdown("### 💡 Try these examples:")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("What's the weather in Tokyo?", use_container_width=True):
                st.session_state.example_prompt = "What's the weather in Tokyo?"
                st.rerun()
            
            if st.button("Calculate 25 * 4 + 10", use_container_width=True):
                st.session_state.example_prompt = "Calculate 25 * 4 + 10"
                st.rerun()
        
        with col2:
            if st.button("What time is it?", use_container_width=True):
                st.session_state.example_prompt = "What time is it?"
                st.rerun()
            
            if st.button("Tell me a joke", use_container_width=True):
                st.session_state.example_prompt = "Tell me a joke"
                st.rerun()
        
        # Handle example prompt
        if "example_prompt" in st.session_state:
            example = st.session_state.example_prompt
            del st.session_state.example_prompt
            st.session_state.messages.append({"role": "user", "content": example})
            st.rerun()

if __name__ == "__main__":
    main()
