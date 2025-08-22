"""
Simple agent implementation that works with basic LLM endpoints.
"""

import re
from typing import Dict, List, Any, Optional
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, AIMessage
from ..utils.logging import get_logger

logger = get_logger(__name__)


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
