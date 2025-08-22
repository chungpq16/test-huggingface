"""
Main application entry point for the Simple LangChain Chatbot.
"""

import os
from src.config.settings import Config
from src.utils.logging import LoggerSetup
from src.tools.registry import ToolRegistry
from src.llm.manager import LLMManager
from src.agents.simple_agent import SimpleAgent
from src.ui.streamlit_ui import ChatbotUI


def main():
    """Main application function"""
    try:
        # Initialize configuration
        config = Config()
        
        # Setup logging
        logger_setup = LoggerSetup()
        logger = logger_setup.get_logger(__name__)
        
        logger.info("🚀 Starting Simple LangChain Chatbot...")
        
        # Initialize tool registry
        tool_registry = ToolRegistry()
        tools = tool_registry.get_all_tools()
        logger.info(f"📦 Loaded {len(tools)} tools")
        
        # Initialize LLM manager
        llm_manager = LLMManager(config)
        llm = llm_manager.get_llm()
        
        # Test API connection
        api_status = llm_manager.test_connection()
        logger.info(f"🌐 API Status: {api_status}")
        
        # Initialize agent
        agent = SimpleAgent(llm=llm, tools=tools)
        logger.info("🤖 Agent initialized")
        
        # Initialize and run UI
        ui = ChatbotUI(agent)
        ui.update_api_status(api_status)
        
        logger.info("🎨 Starting Streamlit UI...")
        ui.run()
        
    except Exception as e:
        print(f"❌ Failed to start application: {str(e)}")
        raise


if __name__ == "__main__":
    main()
