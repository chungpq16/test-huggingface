"""
Tool registry for managing available tools.
"""

from typing import List, Any
from .hello import hello_tool


class ToolRegistry:
    """Registry for managing available tools"""
    
    def __init__(self):
        self._tools = []
        self._register_default_tools()
    
    def _register_default_tools(self):
        """Register default tools"""
        self.register(hello_tool)
    
    def register(self, tool: Any):
        """Register a new tool"""
        self._tools.append(tool)
    
    def get_all_tools(self) -> List[Any]:
        """Get all registered tools"""
        return self._tools.copy()
    
    def get_tool_by_name(self, name: str) -> Any:
        """Get a tool by its name"""
        for tool in self._tools:
            if tool.name == name:
                return tool
        return None
    
    def list_tool_names(self) -> List[str]:
        """Get list of all tool names"""
        return [tool.name for tool in self._tools]


# Global tool registry instance
tool_registry = ToolRegistry()
