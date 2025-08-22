"""
LangGraph agent implementation with tool binding.
"""

from typing import Dict, List, Any, Optional, TypedDict, Annotated
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, AIMessage, BaseMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from ..utils.logging import get_logger

logger = get_logger(__name__)


class AgentState(TypedDict):
    """State for the LangGraph agent"""
    messages: Annotated[List[BaseMessage], add_messages]
    next_action: Optional[str]


class LangGraphAgent:
    """LangGraph-based agent with tool binding"""
    
    def __init__(self, llm: ChatOpenAI, tools: List[Any]):
        self.llm = llm
        self.tools = tools
        self.tool_node = ToolNode(tools)
        
        # Bind tools to the LLM
        self.llm_with_tools = self.llm.bind_tools(tools)
        
        # Build the graph
        self.graph = self._build_graph()
        
        logger.info(f"🤖 LangGraph agent initialized with {len(tools)} tools")
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph state graph"""
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("agent", self._call_model)
        workflow.add_node("tools", self.tool_node)
        
        # Set entry point
        workflow.set_entry_point("agent")
        
        # Add conditional edges
        workflow.add_conditional_edges(
            "agent",
            self._should_continue,
            {
                "tools": "tools",
                "end": END
            }
        )
        
        # Add edge from tools back to agent
        workflow.add_edge("tools", "agent")
        
        return workflow.compile()
    
    def _call_model(self, state: AgentState) -> Dict[str, Any]:
        """Call the LLM with the current state"""
        try:
            messages = state["messages"]
            response = self.llm_with_tools.invoke(messages)
            
            # Log the interaction
            if messages:
                last_message = messages[-1]
                if isinstance(last_message, HumanMessage):
                    logger.info(f"📝 User input: {last_message.content}")
            
            logger.info(f"🤖 Model response: {response.content}")
            
            return {"messages": [response]}
            
        except Exception as e:
            logger.error(f"Error calling model: {str(e)}")
            error_message = AIMessage(content=f"Sorry, I encountered an error: {str(e)}")
            return {"messages": [error_message]}
    
    def _should_continue(self, state: AgentState) -> str:
        """Determine whether to continue to tools or end"""
        messages = state["messages"]
        last_message = messages[-1]
        
        # If there are tool calls, go to tools
        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
            logger.info(f"🔧 Tool calls detected: {[tc['name'] for tc in last_message.tool_calls]}")
            return "tools"
        
        # Otherwise, end
        return "end"
    
    def invoke(self, input_data: Dict[str, Any]) -> Dict[str, str]:
        """Main invoke method for the agent"""
        try:
            user_input = input_data["input"]
            chat_history = input_data.get("chat_history", [])
            
            # Prepare messages
            messages = []
            
            # Add chat history (keep last 10 messages for context)
            if chat_history:
                messages.extend(chat_history[-10:])
            
            # Add current user input
            messages.append(HumanMessage(content=user_input))
            
            # Create initial state
            initial_state = AgentState(messages=messages, next_action=None)
            
            # Run the graph
            final_state = self.graph.invoke(initial_state)
            
            # Get the final response
            final_messages = final_state["messages"]
            if final_messages:
                last_message = final_messages[-1]
                if isinstance(last_message, AIMessage):
                    return {"output": last_message.content}
            
            return {"output": "I'm sorry, I couldn't generate a response."}
            
        except Exception as e:
            error_msg = f"Sorry, I encountered an error: {str(e)}"
            logger.error(f"Error in LangGraph agent: {str(e)}")
            return {"output": error_msg}
    
    def get_tool_descriptions(self) -> str:
        """Get descriptions of available tools"""
        descriptions = []
        for tool in self.tools:
            descriptions.append(f"- **{tool.name}**: {tool.description}")
        return "\n".join(descriptions)
