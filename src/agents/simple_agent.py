"""
Simple agent implementation that works with basic LLM endpoints.
"""

import re
import inspect
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
        # Generate dynamic examples based on available tools
        tool_examples = []
        for tool_name, tool in self.tools.items():
            if tool_name == "hello_tool":
                tool_examples.append(f'- For greetings: "Say hello to Alice" → TOOL_CALL: {tool_name}(Alice)')
            elif tool_name == "weather_tool":
                tool_examples.append(f'- For weather queries: "What\'s the weather in Tokyo?" → TOOL_CALL: {tool_name}(Tokyo)')
            elif tool_name == "calculator_tool":
                tool_examples.append(f'- For calculations: "Calculate 15 * 8 + 12" → TOOL_CALL: {tool_name}(15 * 8 + 12)')
            else:
                # Generic example for unknown tools
                tool_examples.append(f'- For {tool_name}: Use relevant input → TOOL_CALL: {tool_name}(parameter)')
        
        examples_text = "\n".join(tool_examples) if tool_examples else "- TOOL_CALL: tool_name(parameter)"
        
        return f"""You are a helpful AI assistant with access to specialized tools for enhanced capabilities.

Available Tools:
{self.tool_descriptions}

Tool Usage Protocol:
When a user request can be handled by one of these tools, respond with the exact format:
TOOL_CALL: tool_name(parameter_value)

Examples:
{examples_text}

Guidelines:
1. Analyze the user's intent to determine if a tool is needed
2. Use tools when they can provide more accurate or specialized responses
3. Extract the relevant parameter from the user's request
4. If no tool is appropriate, respond naturally with your general knowledge
5. Always use the exact TOOL_CALL format when invoking tools

Remember: You are intelligent enough to understand context and choose the right tool for the task.
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
    
    def _get_tool_parameter_name(self, tool_name: str) -> str:
        """Get the primary parameter name for a tool by inspecting its signature"""
        if tool_name not in self.tools:
            return "input"
            
        tool = self.tools[tool_name]
        try:
            # Get the function signature
            if hasattr(tool, 'func'):
                sig = inspect.signature(tool.func)
            else:
                sig = inspect.signature(tool)
            
            # Get the first parameter (excluding 'self' if present)
            params = list(sig.parameters.keys())
            if params and params[0] != 'self':
                return params[0]
            elif len(params) > 1:
                return params[1]  # Skip 'self'
                
        except Exception as e:
            logger.debug(f"Could not inspect {tool_name} signature: {e}")
        
        # Fallback mapping for known tools
        tool_param_mapping = {
            "hello_tool": "name",
            "weather_tool": "location", 
            "calculator_tool": "expression"
        }
        
        return tool_param_mapping.get(tool_name, "input")
    
    def _execute_tool(self, tool_name: str, tool_param: str) -> str:
        """Execute a tool with given parameters"""
        if tool_name not in self.tools:
            return f"Unknown tool: {tool_name}"
            
        logger.info(f"🔧 Calling tool: {tool_name} with parameter: {tool_param}")
        
        try:
            # Get the appropriate parameter name for this tool
            param_name = self._get_tool_parameter_name(tool_name)
            
            # Special handling for hello_tool default
            if tool_name == "hello_tool" and (not tool_param or tool_param.lower() == "world"):
                tool_input = {param_name: "World"}
            else:
                tool_input = {param_name: tool_param}
            
            logger.debug(f"Tool input: {tool_input}")
            
            # Execute tool
            result = self.tools[tool_name].invoke(tool_input)
            return result
            
        except Exception as e:
            logger.error(f"Error calling tool {tool_name}: {str(e)}")
            return f"Sorry, I had trouble using the {tool_name} tool: {str(e)}"
        
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
    
    def get_capabilities_summary(self) -> str:
        """Get a human-readable summary of the agent's capabilities"""
        if not self.tools:
            return "I'm a basic AI assistant without specialized tools."
        
        capabilities = ["I'm an AI assistant with the following specialized capabilities:"]
        
        for tool_name, tool in self.tools.items():
            # Clean up tool name for display
            display_name = tool_name.replace("_tool", "").replace("_", " ").title()
            capabilities.append(f"• **{display_name}**: {tool.description}")
        
        capabilities.append("\nJust ask me naturally, and I'll use the right tool for your request!")
        return "\n".join(capabilities)
