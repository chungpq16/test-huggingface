"""
LlamaShared Chatbot - Main Application
A simple chatbot using LlamaShared API with LangChain & LangGraph
"""

import streamlit as st
import os
import logging
from dotenv import load_dotenv
from llm.llamashared_llm import LlamaSharedLLM
from tools.tools import AVAILABLE_TOOLS
from langgraph.prebuilt import create_react_agent

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if os.getenv("DEBUG", "false").lower() == "true" else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ChatbotApp:
    """Main Chatbot Application Class"""
    
    def __init__(self):
        self.agent = None
        self.setup_page_config()
    
    def setup_page_config(self):
        """Configure Streamlit page"""
        st.set_page_config(
            page_title="LlamaShared Chatbot",
            page_icon="🦙",
            layout="wide",
            initial_sidebar_state="expanded"
        )
    
    def get_environment_config(self):
        """Get configuration from environment variables"""
        return {
            'api_url': os.getenv("LLAMASHARED_API_URL"),
            'api_key': os.getenv("LLAMASHARED_API_KEY"),
            'model_name': os.getenv("MODEL_NAME", "meta-llama/Meta-Llama-3-70B-Instruct"),
            'ssl_verify': os.getenv("SSL_VERIFY", "true").lower() == "true",
            'debug': os.getenv("DEBUG", "false").lower() == "true"
        }
    
    def validate_config(self, config):
        """Validate required configuration"""
        missing_configs = []
        
        if not config['api_url']:
            missing_configs.append("LLAMASHARED_API_URL")
        if not config['api_key']:
            missing_configs.append("LLAMASHARED_API_KEY")
        
        return missing_configs
    
    def initialize_agent(self):
        """Initialize the LangGraph agent with LLM and tools"""
        try:
            config = self.get_environment_config()
            missing_configs = self.validate_config(config)
            
            if missing_configs:
                raise ValueError(f"Missing required environment variables: {', '.join(missing_configs)}")
            
            # Initialize LLM
            llm = LlamaSharedLLM(
                api_url=config['api_url'],
                api_key=config['api_key'],
                model_name=config['model_name'],
                ssl_verify=config['ssl_verify']
            )
            
            # Create ReAct agent with tools
            agent = create_react_agent(llm, AVAILABLE_TOOLS)
            
            logger.info("Agent initialized successfully")
            return agent
        
        except Exception as e:
            logger.error(f"Error initializing agent: {e}")
            st.error(f"Failed to initialize agent: {e}")
            return None
    
    def render_sidebar(self):
        """Render the configuration sidebar"""
        with st.sidebar:
            st.header("🔧 Configuration")
            
            config = self.get_environment_config()
            
            # Mask API key for display
            api_key_display = (
                f"{config['api_key'][:8]}..." 
                if config['api_key'] and len(config['api_key']) > 8 
                else "Not set"
            )
            
            # Display current settings
            st.info(f"""
            **API URL:** {config['api_url'] or 'Not set'}
            **API Key:** {api_key_display}
            **Model:** {config['model_name']}
            **SSL Verify:** {config['ssl_verify']}
            **Debug:** {config['debug']}
            """)
            
            # Show warnings for missing configuration
            missing_configs = self.validate_config(config)
            if missing_configs:
                for missing in missing_configs:
                    st.error(f"⚠️ {missing} not configured")
                
                st.warning("""
                **Setup Instructions:**
                1. Create a `.env` file in the project root
                2. Add your configuration:
                ```
                LLAMASHARED_API_URL=your_api_url
                LLAMASHARED_API_KEY=your_token
                SSL_VERIFY=false
                DEBUG=true
                ```
                3. Restart the application
                """)
            
            st.divider()
            
            # Available tools section
            st.header("🛠️ Available Tools")
            st.markdown("""
            • **Hello Tool** - Simple greeting function
            • **Calculate Tool** - Basic math operations
              - Add, subtract, multiply, divide
              - Example: "Calculate 15 + 27"
            """)
            
            st.divider()
            
            # Control buttons
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 Reinitialize", use_container_width=True):
                    if 'agent' in st.session_state:
                        del st.session_state.agent
                    st.rerun()
            
            with col2:
                if st.button("🗑️ Clear Chat", use_container_width=True):
                    st.session_state.messages = []
                    st.rerun()
    
    def render_main_content(self):
        """Render the main chat interface"""
        st.title("🦙 LlamaShared Chatbot")
        st.caption("A simple chatbot using LlamaShared API with LangChain & LangGraph")
        
        # Initialize agent if not already done
        if 'agent' not in st.session_state:
            with st.spinner("🚀 Initializing agent..."):
                st.session_state.agent = self.initialize_agent()
        
        if st.session_state.agent is None:
            st.error("❌ Agent failed to initialize. Please check your configuration in the sidebar.")
            return
        
        # Initialize chat history
        if "messages" not in st.session_state:
            st.session_state.messages = []
        
        # Display welcome message if no chat history
        if not st.session_state.messages:
            with st.chat_message("assistant"):
                st.markdown("""
                👋 Hello! I'm your LlamaShared chatbot assistant. I can:
                
                - Answer questions and have conversations
                - Greet people using the hello tool
                - Perform basic calculations
                
                Try asking me something like:
                - "Hello there!"
                - "Say hello to Alice"
                - "Calculate 25 * 4"
                - "What's 100 divided by 5?"
                """)
        
        # Display chat history
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        # Chat input
        if prompt := st.chat_input("💬 What would you like to know?"):
            self.handle_user_input(prompt)
    
    def handle_user_input(self, prompt):
        """Handle user input and generate response"""
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate response
        with st.chat_message("assistant"):
            with st.spinner("🤔 Thinking..."):
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
                    error_message = f"❌ Error: {str(e)}"
                    st.error(error_message)
                    logger.error(f"Error generating response: {e}")
                    
                    # Add error to chat history
                    st.session_state.messages.append({"role": "assistant", "content": error_message})
    
    def run(self):
        """Run the Streamlit application"""
        self.render_sidebar()
        self.render_main_content()


def main():
    """Main application entry point"""
    app = ChatbotApp()
    app.run()


if __name__ == "__main__":
    main()
