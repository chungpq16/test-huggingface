import streamlit as st
import os
import logging
from datetime import datetime
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.tools import tool
from langchain.agents import create_openai_tools_agent, AgentExecutor
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import HumanMessage, AIMessage

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('chatbot_debug.log'),
        logging.StreamHandler()
    ]
)
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
    logger.debug(f"hello_tool returning: {result}")
    return result

# Initialize the LLM with your custom endpoint
def initialize_llm():
    logger.info("Initializing LLM...")
    
    api_key = os.getenv("LLAMA_API_KEY")
    base_url = os.getenv("LLAMA_BASE_URL")
    
    logger.debug(f"API Base URL: {base_url}")
    logger.debug(f"API Key present: {bool(api_key)}")
    
    if not api_key:
        logger.error("LLAMA_API_KEY not found in environment variables")
        raise ValueError("LLAMA_API_KEY not configured")
    
    if not base_url:
        logger.error("LLAMA_BASE_URL not found in environment variables")
        raise ValueError("LLAMA_BASE_URL not configured")
    
    try:
        llm = ChatOpenAI(
            model="meta-llama/Meta-Llama-3-70B-Instruct",
            openai_api_key=api_key,
            openai_api_base=base_url,
            max_tokens=2048,
            temperature=0.7,
            # Custom headers for your API
            default_headers={"KeyId": api_key}
        )
        logger.info("LLM initialized successfully")
        return llm
    except Exception as e:
        logger.error(f"Failed to initialize LLM: {str(e)}")
        raise

# Create the agent
def create_agent():
    logger.info("Creating agent...")
    
    try:
        llm = initialize_llm()
        tools = [hello_tool]
        
        logger.debug(f"Available tools: {[tool.name for tool in tools]}")
        
        # Create a prompt template for the agent
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a helpful assistant. You have access to tools. Use them when appropriate, or respond directly if no tools are needed."),
            MessagesPlaceholder("chat_history", optional=True),
            ("human", "{input}"),
            MessagesPlaceholder("agent_scratchpad")
        ])
        
        logger.debug("Prompt template created")
        
        # Create the agent
        agent = create_openai_tools_agent(llm, tools, prompt)
        agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
        
        logger.info("Agent created successfully")
        return agent_executor
        
    except Exception as e:
        logger.error(f"Failed to create agent: {str(e)}")
        raise

# Streamlit UI
def main():
    st.title("🤖 Simple LLM Chatbot with Tools")
    st.write("A minimal chatbot using LangChain and your custom LLM endpoint")
    
    logger.info("Starting Streamlit application")
    
    # Initialize session state
    if "messages" not in st.session_state:
        st.session_state.messages = []
        logger.debug("Initialized empty message history")
    
    if "agent" not in st.session_state:
        try:
            logger.info("Initializing agent for the first time")
            st.session_state.agent = create_agent()
            st.success("✅ Chatbot initialized successfully!")
            logger.info("Agent initialization successful")
        except Exception as e:
            error_msg = f"❌ Failed to initialize chatbot: {str(e)}"
            st.error(error_msg)
            logger.error(f"Agent initialization failed: {str(e)}")
            st.stop()
    
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("What would you like to say?"):
        logger.info(f"User input received: {prompt}")
        
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
                    logger.info("Invoking agent with user input")
                    start_time = datetime.now()
                    
                    response = st.session_state.agent.invoke({
                        "input": prompt,
                        "chat_history": chat_history
                    })
                    
                    end_time = datetime.now()
                    response_time = (end_time - start_time).total_seconds()
                    logger.info(f"Agent response received in {response_time:.2f} seconds")
                    
                    # Display response
                    bot_response = response["output"]
                    logger.debug(f"Agent output: {bot_response}")
                    
                    st.markdown(bot_response)
                    
                    # Add assistant response to chat history
                    st.session_state.messages.append({"role": "assistant", "content": bot_response})
                    logger.debug("Response added to chat history")
                    
            except Exception as e:
                error_msg = f"Sorry, I encountered an error: {str(e)}"
                logger.error(f"Error during chat interaction: {str(e)}", exc_info=True)
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
            logger.info("Chat history cleared by user")
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
    logger.info("Starting chatbot application")
    logger.info("="*50)
    main()
