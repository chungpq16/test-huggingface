import os
import logging
from dotenv import load_dotenv
from typing import Optional

# Load environment variables
load_dotenv()

class Config:
    """Configuration class for the LLM Agent application"""
    
    # LLM API Configuration
    LLM_API_URL: str = os.getenv("LLM_API_URL", "https://dummy.chat/it/application/llamashared/prod/v1/chat/completions")
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "meta-llama/Meta-Llama-3-70B-Instruct")
    
    # SSL Configuration
    VERIFY_SSL: bool = os.getenv("VERIFY_SSL", "true").lower() == "true"
    
    # Debug Configuration
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    ENABLE_FILE_LOGGING: bool = os.getenv("ENABLE_FILE_LOGGING", "true").lower() == "true"
    
    # LLM Parameters
    MAX_TOKENS: int = int(os.getenv("MAX_TOKENS", "2048"))
    TEMPERATURE: float = float(os.getenv("TEMPERATURE", "0.7"))
    TOP_P: float = float(os.getenv("TOP_P", "1.0"))
    
    # Jira Configuration
    JIRA_SERVER_URL: str = os.getenv("JIRA_SERVER_URL", "")
    JIRA_USERNAME: str = os.getenv("JIRA_USERNAME", "")
    JIRA_API_TOKEN: str = os.getenv("JIRA_API_TOKEN", "")
    JIRA_PROJECT: str = os.getenv("JIRA_PROJECT", "")
    
    @classmethod
    def setup_logging(cls):
        """Setup logging configuration"""
        log_level = getattr(logging, cls.LOG_LEVEL.upper(), logging.INFO)
        
        # Configure logging format
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        
        # Setup handlers
        handlers = [logging.StreamHandler()]
        
        # Add file handler only if enabled
        if cls.ENABLE_FILE_LOGGING:
            # Create logs directory if it doesn't exist
            import os
            os.makedirs("logs", exist_ok=True)
            handlers.append(logging.FileHandler("logs/app.log"))
        
        logging.basicConfig(
            level=log_level,
            format=log_format,
            handlers=handlers
        )
        
        # Set specific loggers to avoid noise
        if cls.DEBUG:
            logging.getLogger("httpx").setLevel(logging.DEBUG)
            logging.getLogger("requests").setLevel(logging.DEBUG)
        else:
            logging.getLogger("httpx").setLevel(logging.WARNING)
            logging.getLogger("requests").setLevel(logging.WARNING)
        
        # Suppress watchdog logs to prevent feedback loop
        logging.getLogger("watchdog").setLevel(logging.WARNING)
        logging.getLogger("watchdog.observers").setLevel(logging.WARNING)
        logging.getLogger("watchdog.observers.inotify_buffer").setLevel(logging.WARNING)
        
        # Suppress other noisy loggers
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        logging.getLogger("asyncio").setLevel(logging.WARNING)
    
    @classmethod
    def validate_config(cls) -> bool:
        """Validate required configuration"""
        if not cls.LLM_API_KEY:
            logging.error("LLM_API_KEY is not set in environment variables")
            return False
        
        if not cls.LLM_API_URL:
            logging.error("LLM_API_URL is not set in environment variables")
            return False
            
        return True

# Initialize configuration
config = Config()
config.setup_logging()
