import streamlit as st
import logging
import json
from datetime import datetime
from config import config
from agent import LLMAgent

# Configure Streamlit page
st.set_page_config(
    page_title="LLM Agent Chat",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize logging
logger = logging.getLogger(__name__)

@st.cache_resource
def initialize_agent():
    """Initialize the LLM Agent (cached for performance)"""
    try:
        return LLMAgent()
    except Exception as e:
        st.error(f"Failed to initialize agent: {e}")
        logger.error(f"Agent initialization failed: {e}")
        return None

def main():
    """Main Streamlit application"""
    
    st.title("🤖 LLM Agent Chat")
    st.markdown("Chat with an AI agent that can use tools to help answer your questions!")
    
    # Sidebar configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Display current configuration
        st.subheader("Current Settings")
        st.text(f"Model: {config.LLM_MODEL}")
        st.text(f"Max Tokens: {config.MAX_TOKENS}")
        st.text(f"Temperature: {config.TEMPERATURE}")
        st.text(f"SSL Verify: {config.VERIFY_SSL}")
        st.text(f"Debug Mode: {config.DEBUG}")
        
        # Configuration validation
        if config.validate_config():
            st.success("✅ Configuration is valid")
        else:
            st.error("❌ Configuration is invalid. Please check your .env file.")
            st.stop()
        
        st.divider()
        
        # Tools information
        st.subheader("🛠️ Available Tools")
        agent = initialize_agent()
        if agent:
            tools_info = agent.get_tool_info()
            for tool in tools_info:
                with st.expander(f"🔧 {tool['name']}"):
                    st.write(tool['description'])
        
        st.divider()
        
        # Debug options
        if st.button("🔍 Show Logs"):
            try:
                with open("app.log", "r") as f:
                    logs = f.read()
                st.text_area("Application Logs", logs, height=300)
            except FileNotFoundError:
                st.info("No log file found yet")
        
        if st.button("🗑️ Clear Chat History"):
            st.session_state.messages = []
            st.rerun()
    
    # Initialize agent
    agent = initialize_agent()
    if not agent:
        st.error("Failed to initialize the agent. Please check your configuration.")
        st.stop()
    
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
        # Add welcome message
        st.session_state.messages.append({
            "role": "assistant",
            "content": "Hello! I'm your AI assistant. I can help you with various tasks and answer questions. I have access to tools like a calculator and can greet people. How can I help you today?",
            "timestamp": datetime.now().isoformat()
        })
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            
            # Show intermediate steps for assistant messages if available
            if message["role"] == "assistant" and "intermediate_steps" in message:
                if message["intermediate_steps"]:
                    with st.expander("🔍 Agent Reasoning Steps"):
                        for i, (action, observation) in enumerate(message["intermediate_steps"]):
                            st.write(f"**Step {i+1}:**")
                            st.write(f"Action: {action.tool}")
                            st.write(f"Input: {action.tool_input}")
                            st.write(f"Output: {observation}")
                            st.divider()
    
    # Chat input
    if prompt := st.chat_input("Type your message here..."):
        # Add user message to chat history
        st.session_state.messages.append({
            "role": "user",
            "content": prompt,
            "timestamp": datetime.now().isoformat()
        })
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate assistant response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    # Process the message with the agent
                    response = agent.process_message(prompt)
                    
                    if response["success"]:
                        st.markdown(response["output"])
                        
                        # Show intermediate steps if available
                        if response["intermediate_steps"]:
                            with st.expander("🔍 Agent Reasoning Steps"):
                                for i, (action, observation) in enumerate(response["intermediate_steps"]):
                                    st.write(f"**Step {i+1}:**")
                                    st.write(f"Action: {action.tool}")
                                    st.write(f"Input: {action.tool_input}")
                                    st.write(f"Output: {observation}")
                                    st.divider()
                        
                        # Add assistant message to chat history
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": response["output"],
                            "intermediate_steps": response["intermediate_steps"],
                            "timestamp": datetime.now().isoformat()
                        })
                    else:
                        error_msg = f"Sorry, I encountered an error: {response.get('error', 'Unknown error')}"
                        st.error(error_msg)
                        
                        # Add error message to chat history
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": error_msg,
                            "timestamp": datetime.now().isoformat()
                        })
                        
                except Exception as e:
                    error_msg = f"An unexpected error occurred: {str(e)}"
                    st.error(error_msg)
                    logger.error(f"Streamlit error: {e}")
                    
                    # Add error message to chat history
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": error_msg,
                        "timestamp": datetime.now().isoformat()
                    })

if __name__ == "__main__":
    main()
