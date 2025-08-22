"""
LLM management and initialization.
"""

import httpx
from langchain_openai import ChatOpenAI
from ..config.settings import Config
from ..utils.logging import get_logger

logger = get_logger(__name__)


class LLMManager:
    """Manages LLM initialization and configuration"""
    
    def __init__(self, config: Config):
        self.config = config
        self._llm = None
    
    def _create_http_client(self) -> httpx.Client:
        """Create HTTP client with SSL configuration"""
        if not self.config.verify_ssl:
            logger.warning("⚠️  SSL verification disabled - use only for development!")
            return httpx.Client(verify=False)
        return httpx.Client()
    
    def initialize(self) -> ChatOpenAI:
        """Initialize and return the LLM instance"""
        if self._llm:
            return self._llm
            
        logger.info("🔧 Initializing LLM...")
        
        try:
            self.config.validate()
            http_client = self._create_http_client()
            
            self._llm = ChatOpenAI(
                model=self.config.model,
                openai_api_key=self.config.api_key,
                openai_api_base=self.config.base_url,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                default_headers={"KeyId": self.config.api_key},
                http_client=http_client
            )
            
            logger.info("✅ LLM initialized successfully")
            return self._llm
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize LLM: {str(e)}")
            if "CERTIFICATE_VERIFY_FAILED" in str(e) or "SSL" in str(e):
                logger.error("💡 SSL Certificate error detected. Try setting VERIFY_SSL=false in your .env file for development")
            raise
    
    def get_llm(self) -> ChatOpenAI:
        """Get the initialized LLM instance"""
        if not self._llm:
            return self.initialize()
        return self._llm
