"""
Tool registry for managing available tools.
"""

from typing import List, Any
from .hello import hello_tool
from .weather import weather_tool
from .calculator import calculator_tool


class ToolRegistry:
    """Registry for managing and accessing tools"""
    
    def __init__(self):
        self._tools = [
            hello_tool,
            weather_tool,
            calculator_tool
        ]
    
    def get_all_tools(self) -> List[Any]:
        """Get all registered tools"""
        return self._tools
    
    def get_tool_by_name(self, name: str) -> Any:
        """Get a specific tool by name"""
        for tool in self._tools:
            if tool.name == name:
                return tool
        return None
    
    def get_tool_names(self) -> List[str]:
        """Get list of all tool names"""
        return [tool.name for tool in self._tools]


# Global tool registry instance
tool_registry = ToolRegistry()
