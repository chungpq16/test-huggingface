from langchain_core.tools import tool
import logging

logger = logging.getLogger(__name__)

@tool
def hello_tool(name: str = "World") -> str:
    """
    A simple hello tool that greets someone.
    
    Args:
        name: The name to greet (default: "World")
    
    Returns:
        A greeting message
    """
    logger.debug(f"Hello tool called with name: {name}")
    return f"Hello, {name}! Nice to meet you!"

@tool
def calculate_tool(operation: str, a: float, b: float) -> str:
    """
    A simple calculator tool that performs basic math operations.
    
    Args:
        operation: The operation to perform (add, subtract, multiply, divide)
        a: First number
        b: Second number
    
    Returns:
        The result of the calculation
    """
    logger.debug(f"Calculate tool called: {operation} {a} {b}")
    
    try:
        if operation.lower() == "add":
            result = a + b
        elif operation.lower() == "subtract":
            result = a - b
        elif operation.lower() == "multiply":
            result = a * b
        elif operation.lower() == "divide":
            if b == 0:
                return "Error: Division by zero is not allowed"
            result = a / b
        else:
            return f"Error: Unknown operation '{operation}'. Supported: add, subtract, multiply, divide"
        
        return f"The result of {operation}ing {a} and {b} is: {result}"
    
    except Exception as e:
        logger.error(f"Error in calculate_tool: {e}")
        return f"Error performing calculation: {str(e)}"

# List of all available tools
AVAILABLE_TOOLS = [hello_tool, calculate_tool]
