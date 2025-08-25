import logging
from datetime import datetime
from typing import Optional, Type
from langchain.tools import BaseTool
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class HelloToolInput(BaseModel):
    """Input for hello tool"""
    name: str = Field(description="Name to greet", default="World")

class HelloTool(BaseTool):
    """A simple hello tool that greets users"""
    
    name: str = "hello_tool"
    description: str = "A simple greeting tool that says hello to someone. Use this when user asks for greetings or wants to say hello."
    args_schema: Type[BaseModel] = HelloToolInput
    
    def _run(self, name: str = "World") -> str:
        """Execute the hello tool"""
        logger.info(f"Hello tool called with name: {name}")
        result = f"Hello, {name}! Nice to meet you! 👋"
        logger.debug(f"Hello tool result: {result}")
        return result

class CalculatorToolInput(BaseModel):
    """Input for calculator tool"""
    expression: str = Field(description="Mathematical expression to calculate (e.g., '2+2', '10*5', '100/4')")

class CalculatorTool(BaseTool):
    """A simple calculator tool that evaluates mathematical expressions"""
    
    name: str = "calculator_tool"
    description: str = "A calculator tool that can perform basic mathematical operations. Use this when user asks for calculations or mathematical operations."
    args_schema: Type[BaseModel] = CalculatorToolInput
    
    def _run(self, expression: str) -> str:
        """Execute the calculator tool"""
        logger.info(f"Calculator tool called with expression: {expression}")
        
        try:
            # Simple safety check - only allow basic mathematical operations
            allowed_chars = set("0123456789+-*/.() ")
            if not all(c in allowed_chars for c in expression):
                logger.warning(f"Invalid characters in expression: {expression}")
                return "Error: Expression contains invalid characters. Only numbers and basic operators (+, -, *, /, parentheses) are allowed."
            
            # Evaluate the expression
            result = eval(expression)
            logger.info(f"Calculator result: {expression} = {result}")
            return f"{expression} = {result}"
            
        except ZeroDivisionError:
            logger.error(f"Division by zero in expression: {expression}")
            return "Error: Division by zero is not allowed."
            
        except Exception as e:
            logger.error(f"Error evaluating expression '{expression}': {e}")
            return f"Error: Could not evaluate the expression '{expression}'. Please check your syntax."

# Export the tools
def get_available_tools():
    """Get list of available tools"""
    tools = [
        HelloTool(),
        CalculatorTool()
    ]
    logger.info(f"Available tools: {[tool.name for tool in tools]}")
    return tools
