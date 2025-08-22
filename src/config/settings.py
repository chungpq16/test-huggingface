"""
Configuration settings for the chatbot application.
"""

import os
from dotenv import load_dotenv


class Config:
    """Configuration settings for the chatbot"""
    
    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv("LLAMA_API_KEY")
        self.base_url = os.getenv("LLAMA_BASE_URL")
        self.verify_ssl = os.getenv("VERIFY_SSL", "true").lower() == "true"
        self.model = "meta-llama/Meta-Llama-3-70B-Instruct"
        self.max_tokens = 2048
        self.temperature = 0.7
    
    def validate(self):
        """Validate required configuration"""
        if not self.api_key:
            raise ValueError("LLAMA_API_KEY not configured")
        if not self.base_url:
            raise ValueError("LLAMA_BASE_URL not configured")
    
    def __repr__(self):
        return f"Config(model={self.model}, base_url={self.base_url}, ssl_verify={self.verify_ssl})"
