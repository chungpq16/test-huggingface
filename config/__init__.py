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
    
    # LLM Parameters
    MAX_TOKENS: int = int(os.getenv("MAX_TOKENS", "2048"))
    TEMPERATURE: float = float(os.getenv("TEMPERATURE", "0.7"))
    TOP_P: float = float(os.getenv("TOP_P", "1.0"))
    
    @classmethod
    def setup_logging(cls):
        """Setup logging configuration"""
        log_level = getattr(logging, cls.LOG_LEVEL.upper(), logging.INFO)
        
        # Configure logging format
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        
        logging.basicConfig(
            level=log_level,
            format=log_format,
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler("app.log")
            ]
        )
        
        # Set specific loggers
        if cls.DEBUG:
            logging.getLogger("httpx").setLevel(logging.DEBUG)
            logging.getLogger("requests").setLevel(logging.DEBUG)
        else:
            logging.getLogger("httpx").setLevel(logging.WARNING)
            logging.getLogger("requests").setLevel(logging.WARNING)
    
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
