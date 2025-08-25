#!/usr/bin/env python3
"""
Test tool conversion to OpenAI format
"""

import json
from tools.tools import AVAILABLE_TOOLS

def test_tool_conversion():
    """Test converting LangChain tools to OpenAI format"""
    
    print("🔧 Testing tool conversion...")
    
    for i, tool in enumerate(AVAILABLE_TOOLS):
        print(f"\n--- Tool {i+1}: {tool.name} ---")
        print(f"Description: {tool.description}")
        
        # Test different conversion methods
        tool_schema = None
        
        if hasattr(tool, 'to_openai_tool'):
            print("✅ Using to_openai_tool method")
            tool_schema = tool.to_openai_tool()
        elif hasattr(tool, 'to_openai_format'):
            print("✅ Using to_openai_format method")
            tool_schema = tool.to_openai_format()
        else:
            print("🔄 Using manual conversion")
            tool_schema = {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                }
            }
            
            # Add parameters if available
            if hasattr(tool, 'args_schema') and tool.args_schema:
                try:
                    schema = tool.args_schema.schema()
                    print(f"Raw schema: {json.dumps(schema, indent=2)}")
                    
                    # Convert pydantic schema to OpenAI function parameters format
                    if 'properties' in schema:
                        tool_schema["function"]["parameters"] = {
                            "type": "object",
                            "properties": schema['properties'],
                            "required": schema.get('required', [])
                        }
                except Exception as e:
                    print(f"❌ Schema extraction failed: {e}")
                    tool_schema["function"]["parameters"] = {"type": "object", "properties": {}}
            else:
                tool_schema["function"]["parameters"] = {"type": "object", "properties": {}}
        
        print(f"Final tool schema: {json.dumps(tool_schema, indent=2)}")

if __name__ == "__main__":
    test_tool_conversion()
