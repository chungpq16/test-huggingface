"""
Streamlit UI components for the chatbot.
"""

import streamlit as st
from langchain.schema import HumanMessage, AIMessage
from typing import List, Any
from ..utils.logging import get_logger

logger = get_logger(__name__)


class ChatbotUI:
    """Streamlit UI for the chatbot"""
    
    def __init__(self, agent: Any):
        self.agent = agent
        self._initialize_session_state()
    
    def _initialize_session_state(self):
        """Initialize Streamlit session state variables"""
        if "messages" not in st.session_state:
            st.session_state.messages = []
        if "api_status" not in st.session_state:
            st.session_state.api_status = "Unknown"
    
    def _display_sidebar(self):
        """Display sidebar with status and controls"""
        with st.sidebar:
            st.title("🤖 Chatbot Controls")
            
            # API Status
            status_color = "🟢" if st.session_state.api_status == "Connected" else "🔴"
            st.write(f"**API Status:** {status_color} {st.session_state.api_status}")
            
            # Clear chat button
            if st.button("🗑️ Clear Chat"):
                st.session_state.messages = []
                st.rerun()
            
            # Info section
            with st.expander("ℹ️ About"):
                st.write("""
                This chatbot uses:
                - **LangChain** for LLM integration
                - **Meta-Llama-3-70B-Instruct** model
                - **Custom tool system** for enhanced capabilities
                
                Try saying:
                - "Hello there!"
                - "Say hello to Alice"
                - "What can you help me with?"
                """)
    
    def _display_chat_messages(self):
        """Display chat message history"""
        for message in st.session_state.messages:
            if isinstance(message, HumanMessage):
                with st.chat_message("user"):
                    st.markdown(message.content)
            elif isinstance(message, AIMessage):
                with st.chat_message("assistant"):
                    st.markdown(message.content)
    
    def _get_chat_history(self) -> List[Any]:
        """Get chat history for the agent"""
        return st.session_state.messages[-10:]  # Keep last 10 messages for context
    
    def _process_user_input(self, user_input: str) -> str:
        """Process user input through the agent"""
        try:
            logger.info(f"📝 User input: {user_input}")
            
            # Prepare input for agent
            agent_input = {
                "input": user_input,
                "chat_history": self._get_chat_history()
            }
            
            # Get response from agent
            result = self.agent.invoke(agent_input)
            response = result["output"]
            
            logger.info(f"🤖 Bot response: {response}")
            
            # Update session state
            st.session_state.messages.append(HumanMessage(content=user_input))
            st.session_state.messages.append(AIMessage(content=response))
            
            return response
            
        except Exception as e:
            error_msg = f"Sorry, I encountered an error: {str(e)}"
            logger.error(f"Error processing user input: {str(e)}")
            
            # Still add to session state for consistency
            st.session_state.messages.append(HumanMessage(content=user_input))
            st.session_state.messages.append(AIMessage(content=error_msg))
            
            return error_msg
    
    def run(self):
        """Main UI loop"""
        # Page configuration
        st.set_page_config(
            page_title="Simple Chatbot",
            page_icon="🤖",
            layout="wide"
        )
        
        # Main title
        st.title("🤖 Simple LangChain Chatbot")
        st.markdown("*Powered by Meta-Llama-3-70B-Instruct with custom tools*")
        
        # Display sidebar
        self._display_sidebar()
        
        # Display chat messages
        self._display_chat_messages()
        
        # Chat input
        if user_input := st.chat_input("Type your message here..."):
            # Display user message immediately
            with st.chat_message("user"):
                st.markdown(user_input)
            
            # Process and display assistant response
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    response = self._process_user_input(user_input)
                    st.markdown(response)
    
    def update_api_status(self, status: str):
        """Update API connection status"""
        st.session_state.api_status = status
