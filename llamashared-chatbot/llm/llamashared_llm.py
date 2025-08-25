import os
import logging
import requests
from typing import List, Dict, Any, Optional
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.callbacks.manager import CallbackManagerForLLMRun
from langchain_core.outputs import ChatResult, ChatGeneration
from langchain_core.utils import get_from_dict_or_env
import json

# Configure logging
logging.basicConfig(level=logging.DEBUG if os.getenv("DEBUG", "false").lower() == "true" else logging.INFO)
logger = logging.getLogger(__name__)

class LlamaSharedLLM(BaseChatModel):
    """Custom LangChain LLM for LlamaShared API"""
    
    api_url: str
    api_key: str
    model_name: str = "meta-llama/Meta-Llama-3-70B-Instruct"
    max_tokens: int = 2048
    temperature: float = 0.7
    ssl_verify: bool = True
    
    def __init__(self, api_url: str = None, api_key: str = None, **kwargs):
        # Get values from parameters or environment
        self.api_url = api_url or get_from_dict_or_env(kwargs, "api_url", "LLAMASHARED_API_URL")
        self.api_key = api_key or get_from_dict_or_env(kwargs, "api_key", "LLAMASHARED_API_KEY")
        self.model_name = kwargs.get("model_name", self.model_name)
        self.ssl_verify = kwargs.get("ssl_verify", str(os.getenv("SSL_VERIFY", "true")).lower() == "true")
        
        # Call parent constructor
        super().__init__(**kwargs)
        
        logger.debug(f"Initialized LlamaSharedLLM with URL: {self.api_url}")
        logger.debug(f"SSL Verify: {self.ssl_verify}")
    
    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """Generate chat response"""
        
        # Convert LangChain messages to API format
        api_messages = []
        for msg in messages:
            if isinstance(msg, HumanMessage):
                api_messages.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                api_messages.append({"role": "assistant", "content": msg.content})
            elif isinstance(msg, SystemMessage):
                api_messages.append({"role": "system", "content": msg.content})
        
        # Prepare payload
        payload = {
            "messages": api_messages,
            "model": self.model_name,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "tool_choice": "auto",  # Enable tool calling
        }
        
        # Add tools if bound
        if hasattr(self, 'bound_tools') and self.bound_tools:
            payload["tools"] = [tool.to_openai_format() for tool in self.bound_tools]
            logger.debug(f"Added {len(self.bound_tools)} tools to payload")
        
        # Add any additional kwargs
        payload.update(kwargs)
        
        headers = {
            "accept": "application/json",
            "KeyId": self.api_key,
            "Content-Type": "application/json"
        }
        
        logger.debug(f"Sending request to {self.api_url}")
        logger.debug(f"Payload: {json.dumps(payload, indent=2)}")
        
        try:
            # Disable SSL warnings if SSL verification is disabled
            if not self.ssl_verify:
                import urllib3
                urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            
            response = requests.post(
                self.api_url,
                json=payload,
                headers=headers,
                verify=self.ssl_verify,
                timeout=60
            )
            
            logger.debug(f"Response status: {response.status_code}")
            response.raise_for_status()
            
            response_json = response.json()
            logger.debug(f"Response: {json.dumps(response_json, indent=2)}")
            
            # Extract content
            content = response_json["choices"][0]["message"]["content"]
            
            # Create ChatGeneration
            generation = ChatGeneration(message=AIMessage(content=content))
            
            return ChatResult(generations=[generation])
            
        except Exception as e:
            logger.error(f"Error calling LlamaShared API: {e}")
            raise e
    
    @property
    def _llm_type(self) -> str:
        return "llamashared"
    
    def bind_tools(self, tools):
        """Bind tools to the LLM"""
        self.bound_tools = tools
        return self
