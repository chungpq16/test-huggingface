import streamlit as st
import os
import logging
import warnings
import ssl
import httpx
from datetime import datetime
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.tools import tool
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import HumanMessage, AIMessage
import re

# Suppress warnings
warnings.filterwarnings("ignore", message=".*ScriptRunContext.*")

# Load environment variables
load_dotenv()

# Configure logging with less verbose console output
file_handler = logging.FileHandler('chatbot_debug.log')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)  # Only INFO and above to console
console_handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))

# Configure root logger
logging.basicConfig(
    level=logging.DEBUG,
    handlers=[file_handler, console_handler]
)

# Reduce noise from third-party libraries
logging.getLogger("watchdog").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("streamlit").setLevel(logging.ERROR)

logger = logging.getLogger(__name__)

# Define a simple hello tool
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

# Initialize the LLM with your custom endpoint
def initialize_llm():
    logger.info("🔧 Initializing LLM...")
    
    api_key = os.getenv("LLAMA_API_KEY")
    base_url = os.getenv("LLAMA_BASE_URL")
    verify_ssl = os.getenv("VERIFY_SSL", "true").lower() == "true"
    
    logger.debug(f"API Base URL: {base_url}")
    logger.debug(f"API Key present: {bool(api_key)}")
    logger.debug(f"SSL Verification: {verify_ssl}")
    
    if not api_key:
        logger.error("LLAMA_API_KEY not found in environment variables")
        raise ValueError("LLAMA_API_KEY not configured")
    
    if not base_url:
        logger.error("LLAMA_BASE_URL not found in environment variables")
        raise ValueError("LLAMA_BASE_URL not configured")
    
    try:
        # Create custom HTTP client with SSL configuration
        if not verify_ssl:
            logger.warning("⚠️  SSL verification disabled - use only for development!")
            # Create httpx client with SSL verification disabled
            http_client = httpx.Client(verify=False)
        else:
            # Create httpx client with default SSL verification
            http_client = httpx.Client()
        
        llm = ChatOpenAI(
            model="meta-llama/Meta-Llama-3-70B-Instruct",
            openai_api_key=api_key,
            openai_api_base=base_url,
            max_tokens=2048,
            temperature=0.7,
            # Custom headers for your API
            default_headers={"KeyId": api_key},
            # Custom HTTP client for SSL handling
            http_client=http_client
        )
        logger.info("✅ LLM initialized successfully")
        return llm
    except Exception as e:
        logger.error(f"❌ Failed to initialize LLM: {str(e)}")
        # If SSL error, provide helpful guidance
        if "CERTIFICATE_VERIFY_FAILED" in str(e) or "SSL" in str(e):
            logger.error("💡 SSL Certificate error detected. Try setting VERIFY_SSL=false in your .env file for development")
        raise

# Simple agent class that works with basic LLM endpoints
class SimpleAgent:
    def __init__(self, llm, tools):
        self.llm = llm
        self.tools = {tool.name: tool for tool in tools}
        self.tool_descriptions = "\n".join([
            f"- {tool.name}: {tool.description}" for tool in tools
        ])
        
    def invoke(self, input_data):
        user_input = input_data["input"]
        chat_history = input_data.get("chat_history", [])
        
        # Create system prompt with tool information
        system_prompt = f"""You are a helpful assistant with access to the following tools:

{self.tool_descriptions}

If the user's request can be handled by one of these tools, respond with:
TOOL_CALL: tool_name(parameter_value)

For example:
- If user says "Say hello to Alice", respond with: TOOL_CALL: hello_tool(Alice)
- If user says "Hello there", you can respond directly or use: TOOL_CALL: hello_tool(World)

Otherwise, respond naturally to the user's question.
"""
        
        # Build messages
        messages = [
            {"role": "system", "content": system_prompt}
        ]
        
        # Add chat history
        for msg in chat_history:
            if isinstance(msg, HumanMessage):
                messages.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                messages.append({"role": "assistant", "content": msg.content})
        
        # Add current user input
        messages.append({"role": "user", "content": user_input})
        
        # Get LLM response
        response = self.llm.invoke(messages)
        response_text = response.content
        
        # Check if LLM wants to call a tool
        tool_call_match = re.search(r'TOOL_CALL:\s*(\w+)\((.*?)\)', response_text)
        
        if tool_call_match:
            tool_name = tool_call_match.group(1)
            tool_param = tool_call_match.group(2).strip().strip("'\"")
            
            if tool_name in self.tools:
                logger.info(f"🔧 Calling tool: {tool_name} with parameter: {tool_param}")
                try:
                    # Call the tool
                    if tool_param and tool_param.lower() != "world":
                        tool_result = self.tools[tool_name](tool_param)
                    else:
                        tool_result = self.tools[tool_name]()
                    
                    return {"output": tool_result}
                except Exception as e:
                    logger.error(f"Error calling tool {tool_name}: {str(e)}")
                    return {"output": f"Sorry, I had trouble using the {tool_name} tool. {response_text}"}
        
        # Return direct response if no tool call
        return {"output": response_text}

# Create the agent
def create_agent():
    logger.info("🔧 Creating simple agent...")
    
    try:
        llm = initialize_llm()
        tools = [hello_tool]
        
        logger.debug(f"Available tools: {[tool.name for tool in tools]}")
        
        # Create simple agent
        agent = SimpleAgent(llm, tools)
        
        logger.info("✅ Simple agent created successfully")
        return agent
        
    except Exception as e:
        logger.error(f"❌ Failed to create agent: {str(e)}")
        raise

# Streamlit UI
def main():
    st.title("🤖 Simple LLM Chatbot with Tools")
    st.write("A minimal chatbot using LangChain and your custom LLM endpoint")
    
    logger.info("🚀 Starting Streamlit application")
    
    # Initialize session state
    if "messages" not in st.session_state:
        st.session_state.messages = []
        logger.debug("Initialized empty message history")
    
    if "agent" not in st.session_state:
        try:
            logger.info("🔧 Initializing agent for the first time")
            st.session_state.agent = create_agent()
            st.success("✅ Chatbot initialized successfully!")
            logger.info("✅ Agent initialization successful")
        except Exception as e:
            error_msg = f"❌ Failed to initialize chatbot: {str(e)}"
            st.error(error_msg)
            logger.error(f"❌ Agent initialization failed: {str(e)}")
            st.stop()
    
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("What would you like to say?"):
        logger.info(f"💬 User: {prompt}")
        
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Get bot response
        with st.chat_message("assistant"):
            try:
                with st.spinner("Thinking..."):
                    logger.debug("Preparing chat history for agent")
                    
                    # Prepare chat history for the agent
                    chat_history = []
                    for i, msg in enumerate(st.session_state.messages[:-1]):  # Exclude the current message
                        if msg["role"] == "user":
                            chat_history.append(HumanMessage(content=msg["content"]))
                        else:
                            chat_history.append(AIMessage(content=msg["content"]))
                    
                    logger.debug(f"Chat history length: {len(chat_history)}")
                    
                    # Get response from agent
                    logger.info("🤖 Processing request...")
                    start_time = datetime.now()
                    
                    response = st.session_state.agent.invoke({
                        "input": prompt,
                        "chat_history": chat_history
                    })
                    
                    end_time = datetime.now()
                    response_time = (end_time - start_time).total_seconds()
                    logger.info(f"✅ Response received in {response_time:.2f}s")
                    
                    # Display response
                    bot_response = response["output"]
                    logger.debug(f"Agent output: {bot_response}")
                    
                    st.markdown(bot_response)
                    
                    # Add assistant response to chat history
                    st.session_state.messages.append({"role": "assistant", "content": bot_response})
                    logger.debug("Response added to chat history")
                    
            except Exception as e:
                error_msg = f"Sorry, I encountered an error: {str(e)}"
                logger.error(f"❌ Error during chat: {str(e)}", exc_info=True)
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
    
    # Sidebar with info
    with st.sidebar:
        st.header("ℹ️ Information")
        st.write("**Available Tools:**")
        st.write("- `hello_tool`: Greets someone by name")
        
        st.write("**Example prompts:**")
        st.write("- 'Hello there!'")
        st.write("- 'Say hello to Alice'")
        st.write("- 'What is 2+2?'")
        st.write("- 'Tell me a joke'")
        
        if st.button("🔄 Clear Chat"):
            logger.info("🧹 Chat history cleared by user")
            st.session_state.messages = []
            st.rerun()
        
        st.write("---")
        st.write("**Configuration:**")
        st.write(f"Model: meta-llama/Meta-Llama-3-70B-Instruct")
        st.write(f"Endpoint: {os.getenv('LLAMA_BASE_URL', 'Not configured')}")
        
        # Debug section
        st.write("---")
        st.write("**Debug Info:**")
        st.write(f"Messages in history: {len(st.session_state.messages)}")
        st.write(f"Agent initialized: {bool(st.session_state.get('agent'))}")
        
        # Show recent log entries
        if st.button("📋 Show Recent Logs"):
            try:
                with open('chatbot_debug.log', 'r') as f:
                    lines = f.readlines()
                    recent_logs = lines[-10:]  # Last 10 lines
                    st.text_area("Recent Log Entries:", 
                               value=''.join(recent_logs), 
                               height=200, 
                               disabled=True)
            except FileNotFoundError:
                st.write("No log file found yet")

if __name__ == "__main__":
    logger.info("="*50)
    logger.info("🚀 Starting chatbot application")
    logger.info("="*50)
    main()
