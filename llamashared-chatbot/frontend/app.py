import streamlit as st
import sys
import os
import logging
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from llm.llamashared_llm import LlamaSharedLLM
from tools.tools import AVAILABLE_TOOLS
from langgraph.prebuilt import create_react_agent

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.DEBUG if os.getenv("DEBUG", "false").lower() == "true" else logging.INFO)
logger = logging.getLogger(__name__)

def initialize_agent():
    """Initialize the LangGraph agent with LLM and tools"""
    try:
        # Get environment variables
        api_url = os.getenv("LLAMASHARED_API_URL")
        api_key = os.getenv("LLAMASHARED_API_KEY")
        model_name = os.getenv("MODEL_NAME", "meta-llama/Meta-Llama-3-70B-Instruct")
        ssl_verify = os.getenv("SSL_VERIFY", "true").lower() == "true"
        
        # Check required environment variables
        if not api_url:
            raise ValueError("LLAMASHARED_API_URL environment variable is required")
        if not api_key:
            raise ValueError("LLAMASHARED_API_KEY environment variable is required")
        
        # Initialize LLM with explicit parameters
        llm = LlamaSharedLLM(
            api_url=api_url,
            api_key=api_key,
            model_name=model_name,
            ssl_verify=ssl_verify
        )
        
        # Create ReAct agent with tools
        agent = create_react_agent(llm, AVAILABLE_TOOLS)
        
        logger.info("Agent initialized successfully")
        return agent
    
    except Exception as e:
        logger.error(f"Error initializing agent: {e}")
        st.error(f"Failed to initialize agent: {e}")
        return None

def main():
    st.set_page_config(
        page_title="LlamaShared Chatbot",
        page_icon="🦙",
        layout="wide"
    )
    
    st.title("🦙 LlamaShared Chatbot")
    st.caption("A simple chatbot using LlamaShared API with LangChain & LangGraph")
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("Configuration")
        
        # Display current settings
        api_url = os.getenv("LLAMASHARED_API_URL", "Not set")
        api_key = os.getenv("LLAMASHARED_API_KEY", "Not set")
        model_name = os.getenv("MODEL_NAME", "meta-llama/Meta-Llama-3-70B-Instruct")
        ssl_verify = os.getenv("SSL_VERIFY", "true")
        debug = os.getenv("DEBUG", "false")
        
        # Mask API key for display
        api_key_display = f"{api_key[:8]}..." if api_key and api_key != "Not set" else "Not set"
        
        st.info(f"""
        **API URL:** {api_url}
        **API Key:** {api_key_display}
        **Model:** {model_name}
        **SSL Verify:** {ssl_verify}
        **Debug:** {debug}
        """)
        
        # Show warnings for missing configuration
        if api_url == "Not set":
            st.error("⚠️ LLAMASHARED_API_URL not configured")
        if api_key == "Not set":
            st.error("⚠️ LLAMASHARED_API_KEY not configured")
        
        if api_url == "Not set" or api_key == "Not set":
            st.warning("""
            Please create a `.env` file in the frontend directory with:
            ```
            LLAMASHARED_API_URL=your_api_url
            LLAMASHARED_API_KEY=your_token
            ```
            """)
        
        st.header("Available Tools")
        st.write("• Hello Tool - Simple greeting")
        st.write("• Calculate Tool - Basic math operations")
        
        if st.button("🔄 Reinitialize Agent"):
            if 'agent' in st.session_state:
                del st.session_state.agent
            st.rerun()
    
    # Initialize agent if not already done
    if 'agent' not in st.session_state:
        with st.spinner("Initializing agent..."):
            st.session_state.agent = initialize_agent()
    
    if st.session_state.agent is None:
        st.error("Agent failed to initialize. Please check your configuration.")
        return
    
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("What would you like to know?"):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    # Invoke the agent
                    response = st.session_state.agent.invoke({"messages": [("user", prompt)]})
                    
                    # Extract the response content
                    if "messages" in response and response["messages"]:
                        assistant_message = response["messages"][-1].content
                    else:
                        assistant_message = "I'm sorry, I couldn't generate a response."
                    
                    st.markdown(assistant_message)
                    
                    # Add assistant response to chat history
                    st.session_state.messages.append({"role": "assistant", "content": assistant_message})
                    
                except Exception as e:
                    error_message = f"Error: {str(e)}"
                    st.error(error_message)
                    logger.error(f"Error generating response: {e}")
                    
                    # Add error to chat history
                    st.session_state.messages.append({"role": "assistant", "content": error_message})
    
    # Clear chat button
    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.rerun()

if __name__ == "__main__":
    main()
