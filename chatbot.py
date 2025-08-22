import streamlit as st
import os
import logging
import warnings
import httpx
import re
from datetime import datetime
from dotenv import load_dotenv
from typing import Dict, List, Any, Optional
from langchain_openai import ChatOpenAI
from langchain.tools import tool
from langchain.schema import HumanMessage, AIMessage

# Configuration and Setup
class Config:
    """Configuration settings for the chatbot"""
    
    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv("LLAMA_API_KEY")
        self.base_url = os.getenv("LLAMA_BASE_URL")
        self.verify_ssl = os.getenv("VERIFY_SSL", "true").lower() == "true"
        self.model = "meta-llama/Meta-Llama-3-70B-Instruct"
        self.max_tokens = 2048
        self.temperature = 0.7
    
    def validate(self):
        """Validate required configuration"""
        if not self.api_key:
            raise ValueError("LLAMA_API_KEY not configured")
        if not self.base_url:
            raise ValueError("LLAMA_BASE_URL not configured")

class LoggerSetup:
    """Setup logging configuration"""
    
    @staticmethod
    def configure_logging():
        """Configure logging with file and console handlers"""
        # Suppress warnings
        warnings.filterwarnings("ignore", message=".*ScriptRunContext.*")
        
        # File handler for detailed logging
        file_handler = logging.FileHandler('chatbot_debug.log')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        )
        
        # Console handler for important messages only
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
        
        # Configure root logger
        logging.basicConfig(
            level=logging.DEBUG,
            handlers=[file_handler, console_handler]
        )
        
        # Reduce noise from third-party libraries
        for lib in ["watchdog", "urllib3", "httpx", "httpcore", "streamlit"]:
            logging.getLogger(lib).setLevel(logging.WARNING)
        
        return logging.getLogger(__name__)

# Initialize logging
logger = LoggerSetup.configure_logging()

# Tools Definition
@tool
def hello_tool(name: str = "World") -> str:
    """
    A simple greeting tool that says hello to someone.
    
    Args:
        name: The name of the person to greet. Defaults to "World".
    
    Returns:
        A greeting message.
    """
    logger.debug(f"hello_tool called with name: {name}")
    result = f"Hello, {name}! Nice to meet you!"
    logger.info(f"🔧 Used hello_tool for: {name}")
    return result

class LLMManager:
    """Manages LLM initialization and configuration"""
    
    def __init__(self, config: Config):
        self.config = config
        self._llm = None
    
    def _create_http_client(self) -> httpx.Client:
        """Create HTTP client with SSL configuration"""
        if not self.config.verify_ssl:
            logger.warning("⚠️  SSL verification disabled - use only for development!")
            return httpx.Client(verify=False)
        return httpx.Client()
    
    def initialize(self) -> ChatOpenAI:
        """Initialize and return the LLM instance"""
        if self._llm:
            return self._llm
            
        logger.info("🔧 Initializing LLM...")
        
        try:
            self.config.validate()
            http_client = self._create_http_client()
            
            self._llm = ChatOpenAI(
                model=self.config.model,
                openai_api_key=self.config.api_key,
                openai_api_base=self.config.base_url,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                default_headers={"KeyId": self.config.api_key},
                http_client=http_client
            )
            
            logger.info("✅ LLM initialized successfully")
            return self._llm
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize LLM: {str(e)}")
            if "CERTIFICATE_VERIFY_FAILED" in str(e) or "SSL" in str(e):
                logger.error("💡 SSL Certificate error detected. Try setting VERIFY_SSL=false in your .env file for development")
            raise

# Simple agent class that works with basic LLM endpoints
class SimpleAgent:
    """A simple agent that works with basic LLM endpoints without advanced tool calling"""
    
    TOOL_CALL_PATTERN = r'TOOL_CALL:\s*(\w+)\((.*?)\)'
    
    def __init__(self, llm: ChatOpenAI, tools: List[Any]):
        self.llm = llm
        self.tools = {tool.name: tool for tool in tools}
        self.tool_descriptions = "\n".join([
            f"- {tool.name}: {tool.description}" for tool in tools
        ])
        
    def _create_system_prompt(self) -> str:
        """Create system prompt with tool information"""
        return f"""You are a helpful assistant with access to the following tools:

{self.tool_descriptions}

If the user's request can be handled by one of these tools, respond with:
TOOL_CALL: tool_name(parameter_value)

For example:
- If user says "Say hello to Alice", respond with: TOOL_CALL: hello_tool(Alice)
- If user says "Hello there", you can respond directly or use: TOOL_CALL: hello_tool(World)

Otherwise, respond naturally to the user's question.
"""
    
    def _build_messages(self, user_input: str, chat_history: List[Any]) -> List[Dict[str, str]]:
        """Build messages list for LLM"""
        messages = [{"role": "system", "content": self._create_system_prompt()}]
        
        # Add chat history
        for msg in chat_history:
            if isinstance(msg, HumanMessage):
                messages.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                messages.append({"role": "assistant", "content": msg.content})
        
        # Add current user input
        messages.append({"role": "user", "content": user_input})
        return messages
    
    def _parse_tool_call(self, response_text: str) -> Optional[tuple]:
        """Parse tool call from LLM response"""
        tool_call_match = re.search(self.TOOL_CALL_PATTERN, response_text)
        if tool_call_match:
            tool_name = tool_call_match.group(1)
            tool_param = tool_call_match.group(2).strip().strip("'\"")
            return tool_name, tool_param
        return None
    
    def _execute_tool(self, tool_name: str, tool_param: str) -> str:
        """Execute a tool with given parameters"""
        if tool_name not in self.tools:
            return f"Unknown tool: {tool_name}"
            
        logger.info(f"🔧 Calling tool: {tool_name} with parameter: {tool_param}")
        
        try:
            # Prepare tool input
            if tool_param and tool_param.lower() != "world":
                tool_input = {"name": tool_param}
            else:
                tool_input = {"name": "World"}
            
            # Execute tool
            result = self.tools[tool_name].invoke(tool_input)
            return result
            
        except Exception as e:
            logger.error(f"Error calling tool {tool_name}: {str(e)}")
            return f"Sorry, I had trouble using the {tool_name} tool."
        
    def invoke(self, input_data: Dict[str, Any]) -> Dict[str, str]:
        """Main invoke method for the agent"""
        user_input = input_data["input"]
        chat_history = input_data.get("chat_history", [])
        
        # Build messages and get LLM response
        messages = self._build_messages(user_input, chat_history)
        response = self.llm.invoke(messages)
        response_text = response.content
        
        # Check for tool calls
        tool_call = self._parse_tool_call(response_text)
        if tool_call:
            tool_name, tool_param = tool_call
            tool_result = self._execute_tool(tool_name, tool_param)
            return {"output": tool_result}
        
        # Return direct response
        return {"output": response_text}

class AgentFactory:
    """Factory for creating agents"""
    
    @staticmethod
    def create_simple_agent(config: Config) -> SimpleAgent:
        """Create a simple agent with LLM and tools"""
        logger.info("🔧 Creating simple agent...")
        
        try:
            llm_manager = LLMManager(config)
            llm = llm_manager.initialize()
            tools = [hello_tool]
            
            logger.debug(f"Available tools: {[tool.name for tool in tools]}")
            
            agent = SimpleAgent(llm, tools)
            logger.info("✅ Simple agent created successfully")
            return agent
            
        except Exception as e:
            logger.error(f"❌ Failed to create agent: {str(e)}")
            raise

class ChatbotUI:
    """Manages the Streamlit UI for the chatbot"""
    
    def __init__(self):
        self.config = Config()
    
    def _initialize_session_state(self) -> SimpleAgent:
        """Initialize session state and create agent"""
        if "messages" not in st.session_state:
            st.session_state.messages = []
            logger.debug("Initialized empty message history")
        
        if "agent" not in st.session_state:
            try:
                logger.info("🔧 Initializing agent for the first time")
                st.session_state.agent = AgentFactory.create_simple_agent(self.config)
                st.success("✅ Chatbot initialized successfully!")
                logger.info("✅ Agent initialization successful")
            except Exception as e:
                error_msg = f"❌ Failed to initialize chatbot: {str(e)}"
                st.error(error_msg)
                logger.error(f"❌ Agent initialization failed: {str(e)}")
                st.stop()
        
        return st.session_state.agent
    
    def _display_chat_history(self):
        """Display existing chat messages"""
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
    
    def _prepare_chat_history(self) -> List[Any]:
        """Prepare chat history for the agent"""
        chat_history = []
        for msg in st.session_state.messages[:-1]:  # Exclude current message
            if msg["role"] == "user":
                chat_history.append(HumanMessage(content=msg["content"]))
            else:
                chat_history.append(AIMessage(content=msg["content"]))
        return chat_history
    
    def _handle_user_input(self, prompt: str, agent: SimpleAgent):
        """Handle user input and generate response"""
        logger.info(f"💬 User: {prompt}")
        
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Get bot response
        with st.chat_message("assistant"):
            try:
                with st.spinner("Thinking..."):
                    chat_history = self._prepare_chat_history()
                    logger.debug(f"Chat history length: {len(chat_history)}")
                    
                    # Get response from agent
                    logger.info("🤖 Processing request...")
                    start_time = datetime.now()
                    
                    response = agent.invoke({
                        "input": prompt,
                        "chat_history": chat_history
                    })
                    
                    end_time = datetime.now()
                    response_time = (end_time - start_time).total_seconds()
                    logger.info(f"✅ Response received in {response_time:.2f}s")
                    
                    # Display response
                    bot_response = response["output"]
                    st.markdown(bot_response)
                    
                    # Add to chat history
                    st.session_state.messages.append({"role": "assistant", "content": bot_response})
                    
            except Exception as e:
                error_msg = f"Sorry, I encountered an error: {str(e)}"
                logger.error(f"❌ Error during chat: {str(e)}", exc_info=True)
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
    
    def _render_sidebar(self):
        """Render the sidebar with information and controls"""
        with st.sidebar:
            st.header("ℹ️ Information")
            st.write("**Available Tools:**")
            st.write("- `hello_tool`: Greets someone by name")
            
            st.write("**Example prompts:**")
            examples = [
                "'Hello there!'",
                "'Say hello to Alice'", 
                "'What is 2+2?'",
                "'Tell me a joke'"
            ]
            for example in examples:
                st.write(f"- {example}")
            
            if st.button("🔄 Clear Chat"):
                logger.info("🧹 Chat history cleared by user")
                st.session_state.messages = []
                st.rerun()
            
            st.write("---")
            st.write("**Configuration:**")
            st.write(f"Model: {self.config.model}")
            st.write(f"Endpoint: {self.config.base_url or 'Not configured'}")
            
            # Debug section
            st.write("---")
            st.write("**Debug Info:**")
            st.write(f"Messages in history: {len(st.session_state.messages)}")
            st.write(f"Agent initialized: {bool(st.session_state.get('agent'))}")
            
            # Show recent log entries
            if st.button("📋 Show Recent Logs"):
                self._show_recent_logs()
    
    def _show_recent_logs(self):
        """Display recent log entries"""
        try:
            with open('chatbot_debug.log', 'r') as f:
                lines = f.readlines()
                recent_logs = lines[-10:]
                st.text_area(
                    "Recent Log Entries:", 
                    value=''.join(recent_logs), 
                    height=200, 
                    disabled=True
                )
        except FileNotFoundError:
            st.write("No log file found yet")
    
    def run(self):
        """Main method to run the Streamlit UI"""
        st.title("🤖 Simple LLM Chatbot with Tools")
        st.write("A minimal chatbot using LangChain and your custom LLM endpoint")
        
        logger.info("🚀 Starting Streamlit application")
        
        # Initialize components
        agent = self._initialize_session_state()
        
        # Display chat history
        self._display_chat_history()
        
        # Handle user input
        if prompt := st.chat_input("What would you like to say?"):
            self._handle_user_input(prompt, agent)
        
        # Render sidebar
        self._render_sidebar()

def main():
    """Entry point for the application"""
    chatbot_ui = ChatbotUI()
    chatbot_ui.run()

if __name__ == "__main__":
    logger.info("="*50)
    logger.info("🚀 Starting chatbot application")
    logger.info("="*50)
    main()
