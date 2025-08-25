import logging
from typing import List
from langchain.agents import create_react_agent, AgentExecutor
from langchain.prompts import PromptTemplate
from langchain.tools import BaseTool
from llm import CustomLLM
from tools import get_available_tools

logger = logging.getLogger(__name__)

class LLMAgent:
    """LLM Agent using ReAct pattern with custom tools"""
    
    def __init__(self):
        """Initialize the LLM Agent"""
        logger.info("Initializing LLM Agent...")
        
        # Initialize LLM
        self.llm = CustomLLM()
        
        # Get available tools
        self.tools = get_available_tools()
        
        # Create the ReAct prompt template
        self.prompt = PromptTemplate.from_template("""
You are a helpful AI assistant that can use tools to help answer questions and perform tasks.

You have access to the following tools:
{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!

Question: {input}
Thought: {agent_scratchpad}
""")
        
        # Create the ReAct agent
        self.agent = create_react_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=self.prompt
        )
        
        # Create agent executor
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=5,
            return_intermediate_steps=True
        )
        
        logger.info(f"LLM Agent initialized with {len(self.tools)} tools")
    
    def process_message(self, message: str) -> dict:
        """Process a user message and return the agent's response"""
        logger.info(f"Processing message: {message}")
        
        try:
            # Execute the agent
            result = self.agent_executor.invoke({"input": message})
            
            logger.info("Agent execution completed successfully")
            logger.debug(f"Agent result: {result}")
            
            # Extract the response
            response = {
                "output": result.get("output", "No response generated"),
                "intermediate_steps": result.get("intermediate_steps", []),
                "success": True
            }
            
            return response
            
        except Exception as e:
            logger.error(f"Error in agent execution: {e}")
            return {
                "output": f"Sorry, I encountered an error: {str(e)}",
                "intermediate_steps": [],
                "success": False,
                "error": str(e)
            }
    
    def get_tool_info(self) -> List[dict]:
        """Get information about available tools"""
        tool_info = []
        for tool in self.tools:
            tool_info.append({
                "name": tool.name,
                "description": tool.description,
                "args_schema": tool.args_schema.schema() if tool.args_schema else None
            })
        return tool_info
