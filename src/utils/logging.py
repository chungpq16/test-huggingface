"""
Logging configuration and utilities.
"""

import logging
import warnings


class LoggerSetup:
    """Setup logging configuration"""
    
    def __init__(self):
        self.configure_logging()
    
    def configure_logging(self):
        """Configure logging with file and console handlers"""
        # Suppress warnings
        warnings.filterwarnings("ignore", message=".*ScriptRunContext.*")
        
        # File handler for detailed logging
        file_handler = logging.FileHandler('chatbot_debug.log')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        )
        
        # Console handler for important messages only
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
        
        # Configure root logger
        logging.basicConfig(
            level=logging.DEBUG,
            handlers=[file_handler, console_handler]
        )
        
        # Reduce noise from third-party libraries
        for lib in ["watchdog", "urllib3", "httpx", "httpcore", "streamlit"]:
            logging.getLogger(lib).setLevel(logging.WARNING)
    
    def get_logger(self, name: str = None) -> logging.Logger:
        """Get a logger instance"""
        return logging.getLogger(name or __name__)


def get_logger(name: str = None) -> logging.Logger:
    """Get a logger instance"""
    return logging.getLogger(name or __name__)
