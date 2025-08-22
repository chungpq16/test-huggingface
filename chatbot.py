import streamlit as st
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.tools import tool
from langchain.agents import create_openai_tools_agent, AgentExecutor
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import HumanMessage, AIMessage

# Load environment variables
load_dotenv()

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
    return f"Hello, {name}! Nice to meet you!"

# Initialize the LLM with your custom endpoint
def initialize_llm():
    return ChatOpenAI(
        model="meta-llama/Meta-Llama-3-70B-Instruct",
        openai_api_key=os.getenv("LLAMA_API_KEY"),
        openai_api_base=os.getenv("LLAMA_BASE_URL"),
        max_tokens=2048,
        temperature=0.7,
        # Custom headers for your API
        default_headers={"KeyId": os.getenv("LLAMA_API_KEY")}
    )

# Create the agent
def create_agent():
    llm = initialize_llm()
    tools = [hello_tool]
    
    # Create a prompt template for the agent
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful assistant. You have access to tools. Use them when appropriate, or respond directly if no tools are needed."),
        MessagesPlaceholder("chat_history", optional=True),
        ("human", "{input}"),
        MessagesPlaceholder("agent_scratchpad")
    ])
    
    # Create the agent
    agent = create_openai_tools_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
    
    return agent_executor

# Streamlit UI
def main():
    st.title("🤖 Simple LLM Chatbot with Tools")
    st.write("A minimal chatbot using LangChain and your custom LLM endpoint")
    
    # Initialize session state
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "agent" not in st.session_state:
        try:
            st.session_state.agent = create_agent()
            st.success("✅ Chatbot initialized successfully!")
        except Exception as e:
            st.error(f"❌ Failed to initialize chatbot: {str(e)}")
            st.stop()
    
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("What would you like to say?"):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Get bot response
        with st.chat_message("assistant"):
            try:
                with st.spinner("Thinking..."):
                    # Prepare chat history for the agent
                    chat_history = []
                    for msg in st.session_state.messages[:-1]:  # Exclude the current message
                        if msg["role"] == "user":
                            chat_history.append(HumanMessage(content=msg["content"]))
                        else:
                            chat_history.append(AIMessage(content=msg["content"]))
                    
                    # Get response from agent
                    response = st.session_state.agent.invoke({
                        "input": prompt,
                        "chat_history": chat_history
                    })
                    
                    # Display response
                    bot_response = response["output"]
                    st.markdown(bot_response)
                    
                    # Add assistant response to chat history
                    st.session_state.messages.append({"role": "assistant", "content": bot_response})
                    
            except Exception as e:
                error_msg = f"Sorry, I encountered an error: {str(e)}"
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
            st.session_state.messages = []
            st.rerun()
        
        st.write("---")
        st.write("**Configuration:**")
        st.write(f"Model: meta-llama/Meta-Llama-3-70B-Instruct")
        st.write(f"Endpoint: {os.getenv('LLAMA_BASE_URL', 'Not configured')}")

if __name__ == "__main__":
    main()
