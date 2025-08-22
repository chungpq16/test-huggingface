import streamlit as st
import requests
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
import re
import logging

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

# Setup logging
def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logging()

# Custom LLM wrapper for API that supports tool calling
class CustomChatModel(BaseChatModel):
    """Custom LangChain-compatible LLM for API integration"""
    
    api_endpoint: str = Field(..., description="API endpoint")
    api_key: str = Field(..., description="API key for authentication")
    model_name: str = Field(default="custom-model", description="Model name")
    max_tokens: int = Field(default=2048, description="Maximum tokens in response")
    temperature: float = Field(default=0.7, description="Temperature for generation")
    
    class Config:
        """Pydantic configuration"""
        arbitrary_types_allowed = True
    
    def __init__(self, api_endpoint: str, api_key: str, **kwargs):
        # Initialize with explicit field values
        super().__init__(
            api_endpoint=api_endpoint,
            api_key=api_key,
            **kwargs
        )
    
    @property
    def headers(self) -> Dict[str, str]:
        """Generate headers for API requests"""
        return {
            "KeyId": self.api_key,
            "Content-Type": "application/json",
            "accept": "application/json"
        }
    
    @property
    def _llm_type(self) -> str:
        return "custom-api"
    
    def _generate(self, messages: List[CoreBaseMessage], **kwargs) -> ChatResult:
        """Generate response from API"""
        logger.debug(f"🔄 Generating response for {len(messages)} messages")
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
        
        logger.debug(f"📤 Sending {len(formatted_messages)} formatted messages to API")
        
        payload = {
            "messages": formatted_messages,
            "max_tokens": self.max_tokens,
            "model": "meta-llama/Meta-Llama-3-70B-Instruct"
        }
        
        # Add temperature if specified
        if hasattr(self, 'temperature') and self.temperature != 0.7:
            payload["temperature"] = self.temperature
        
        # Debug: Log headers and payload
        logger.debug(f"🔑 API Headers: {dict(self.headers)}")
        logger.debug(f"📦 API Payload: {json.dumps(payload, indent=2)}")
        
        try:
            logger.debug(f"🌐 Making API call to {self.api_endpoint}")
            response = requests.post(
                self.api_endpoint,
                headers=self.headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            
            logger.debug(f"✅ API response received: {len(content)} characters")
            
            # Create ChatGeneration
            message = AIMessage(content=content)
            generation = ChatGeneration(message=message)
            
            return ChatResult(generations=[generation])
            
        except Exception as e:
            logger.error(f"❌ API call failed: {str(e)}")
            error_content = f"Error calling API: {str(e)}"
            message = AIMessage(content=error_content)
            generation = ChatGeneration(message=message)
            return ChatResult(generations=[generation])

# Define tools using LangChain's @tool decorator
@tool
def get_current_time() -> str:
    """Get the current date and time.
    
    Returns:
        Current date and time as a formatted string
    """
    logger.debug("🕐 Time tool called")
    now = datetime.now()
    formatted_time = now.strftime('%A, %B %d, %Y at %I:%M %p')
    result = f"🕐 Current time: {formatted_time}"
    logger.debug(f"🕐 Time tool result: {result}")
    return result

# Create the agent with bound tools
def create_agent_with_tools(llm, tools):
    """Create an agent with tools bound to the LLM"""
    logger.debug(f"🔧 Creating agent with {len(tools)} tools")
    
    try:
        # Create a prompt template for the agent
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a helpful AI assistant with access to a tool. 
            When a user asks for the time or date, use the get_current_time tool.
            
            Available tool:
            - get_current_time: Get current date and time
            
            Always provide helpful, accurate responses and use the tool when appropriate."""),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])
        
        # Check if LLM supports tool binding
        logger.debug("🔗 Attempting to bind tools to LLM")
        if hasattr(llm, 'bind_tools'):
            try:
                llm_with_tools = llm.bind_tools(tools)
                logger.debug("✅ Tools bound successfully")
            except Exception as bind_error:
                logger.warning(f"⚠️ Tool binding failed: {bind_error}")
                logger.debug("⚠️ LLM doesn't support bind_tools, using fallback")
                return None
        else:
            logger.debug("⚠️ LLM doesn't support bind_tools method, using fallback")
            return None
        
        # Create the agent
        logger.debug("🤖 Creating tool calling agent")
        try:
            agent = create_tool_calling_agent(llm_with_tools, tools, prompt)
        except Exception as agent_error:
            logger.warning(f"⚠️ Agent creation failed: {agent_error}")
            return None
        
        # Create agent executor
        logger.debug("⚙️ Creating agent executor")
        agent_executor = AgentExecutor(
            agent=agent, 
            tools=tools, 
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=3
        )
        
        logger.debug("✅ Agent created successfully")
        return agent_executor
        
    except Exception as e:
        logger.warning(f"⚠️ Failed to create agent (this is normal for non-tool-calling models): {str(e)}")
        logger.debug("🔄 Falling back to manual tool handling")
        # Return a fallback that will trigger manual tool handling
        return None

def handle_tools_manually(prompt: str, llm, tools):
    """Fallback manual tool handling when agent creation fails"""
    logger.debug("🔧 Using manual tool handling as fallback")
    prompt_lower = prompt.lower()
    
    # Tool detection and execution
    tool_results = []
    
    # Time tool detection
    if any(keyword in prompt_lower for keyword in ["time", "date", "clock", "when"]):
        time_result = get_current_time.func()
        tool_results.append(f"Time Tool: {time_result}")
    
    # Combine prompt with tool results
    if tool_results:
        enhanced_prompt = f"""User Question: {prompt}

Tool Results:
{chr(10).join(tool_results)}

Please provide a comprehensive response using the tool results above."""
    else:
        enhanced_prompt = prompt
    
    # Get LLM response
    messages = [HumanMessage(content=enhanced_prompt)]
    result = llm._generate(messages)
    return result.generations[0].message.content

# Streamlit App
def main():
    st.set_page_config(
        page_title="Simple AI Chatbot",
        page_icon="🤖",
        layout="centered",
        initial_sidebar_state="expanded"
    )
    
    # Main title
    st.title("🤖 Simple AI Chatbot")
    st.markdown("*AI Assistant with Tool Integration*")
    
    # Sidebar configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        api_endpoint = st.text_input(
            "API Endpoint",
            value=st.session_state.get("api_endpoint", "https://api.example.com/v1/chat/completions"),
            help="Your API endpoint"
        )
        
        api_key = st.text_input(
            "API Key",
            type="password", 
            value=st.session_state.get("api_key", ""),
            help="Your API authentication key"
        )
        
        # Save configuration
        st.session_state["api_endpoint"] = api_endpoint
        st.session_state["api_key"] = api_key
        
        st.markdown("---")
        
        # Tool information
        st.subheader("🛠️ Available Tool")
        st.markdown("""
        **✅ Time Tool**  
        Get current date/time
        """)
        
        st.markdown("---")
        
        # Agent settings
        st.subheader("🤖 Agent Settings")
        
        use_agent = st.checkbox(
            "Try LangChain Agent", 
            value=st.session_state.get("use_agent", False),
            help="Try LangChain agent (will fallback to manual tools if not supported)"
        )
        st.session_state["use_agent"] = use_agent
        
        # Debug settings
        debug_mode = st.checkbox(
            "Debug Mode", 
            value=st.session_state.get("debug_mode", False),
            help="Show debug logs in the interface"
        )
        st.session_state["debug_mode"] = debug_mode
        
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
                    logger.debug(f"💭 Processing user input: {prompt}")
                    
                    # Initialize LLM
                    llm = CustomChatModel(api_endpoint=api_endpoint, api_key=api_key)
                    
                    if st.session_state.get("use_agent", False):
                        logger.debug("🔧 Attempting to use LangChain agent with bound tools")
                        # Use agent with bound tools - let LLM decide when to use tools
                        tools = [get_current_time]
                        agent_executor = create_agent_with_tools(llm, tools)
                        
                        if agent_executor is not None:
                            # Get chat history for context
                            chat_history = []
                            for msg in st.session_state.messages[-6:]:  # Last 6 messages for context
                                if msg["role"] == "user":
                                    chat_history.append(HumanMessage(content=msg["content"]))
                                else:
                                    chat_history.append(AIMessage(content=msg["content"]))
                            
                            logger.debug(f"📚 Using {len(chat_history)} messages as chat history")
                            
                            # Let the agent decide when to use tools
                            logger.debug("🚀 Invoking agent executor")
                            result = agent_executor.invoke({
                                "input": prompt,
                                "chat_history": chat_history
                            })
                            response = result["output"]
                            logger.debug("✅ Agent execution completed")
                        else:
                            logger.debug("⚠️ Agent creation failed, falling back to manual tool handling")
                            tools = [get_current_time]
                            response = handle_tools_manually(prompt, llm, tools)
                    else:
                        logger.debug("🔧 Using manual tool handling (recommended)")
                        # Manual tool handling - more reliable for this API
                        tools = [get_current_time]
                        response = handle_tools_manually(prompt, llm, tools)
                    
                    # Show debug info if enabled
                    if st.session_state.get("debug_mode", False):
                        with st.expander("🐛 Debug Information"):
                            st.json({
                                "user_input": prompt,
                                "using_agent": st.session_state.get("use_agent", True),
                                "chat_history_length": len(st.session_state.messages),
                                "response_length": len(response),
                                "api_endpoint": api_endpoint[:50] + "..." if len(api_endpoint) > 50 else api_endpoint
                            })
                    
                    st.markdown(response)
                    
                except Exception as e:
                    logger.error(f"💥 Error during processing: {str(e)}")
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
        st.markdown("### 💡 Try this example:")
        
        if st.button("🕐 What time is it?", use_container_width=True):
            st.session_state.example_prompt = "What time is it right now?"
            st.rerun()
        
        # Handle example prompts
        if "example_prompt" in st.session_state:
            example = st.session_state.example_prompt
            del st.session_state.example_prompt
            st.session_state.messages.append({"role": "user", "content": example})
            st.rerun()

if __name__ == "__main__":
    main()
