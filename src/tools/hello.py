"""
Hello tool for greeting users.
"""

from langchain.tools import tool
from ..utils.logging import get_logger

logger = get_logger(__name__)


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
