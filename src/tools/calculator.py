"""
Calculator tool for basic math operations.
"""

from langchain.tools import tool
import ast
import operator


@tool
def calculator_tool(expression: str) -> str:
    """Safely evaluate mathematical expressions.
    
    Args:
        expression: A mathematical expression like "2 + 3 * 4" or "sqrt(16)"
        
    Returns:
        The result of the calculation as a string
    """
    try:
        # Define safe operations
        safe_operations = {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
            ast.Pow: operator.pow,
            ast.USub: operator.neg,
            ast.UAdd: operator.pos,
        }
        
        # Parse and evaluate safely
        def safe_eval(node):
            if isinstance(node, ast.Constant):  # Numbers
                return node.value
            elif isinstance(node, ast.BinOp):  # Binary operations
                left = safe_eval(node.left)
                right = safe_eval(node.right)
                return safe_operations[type(node.op)](left, right)
            elif isinstance(node, ast.UnaryOp):  # Unary operations
                operand = safe_eval(node.operand)
                return safe_operations[type(node.op)](operand)
            else:
                raise ValueError(f"Unsupported operation: {type(node)}")
        
        # Parse the expression
        tree = ast.parse(expression.strip(), mode='eval')
        result = safe_eval(tree.body)
        
        return f"Result: {result}"
        
    except Exception as e:
        return f"Error calculating '{expression}': {str(e)}. Please use basic math operations like +, -, *, /, ** for power."
