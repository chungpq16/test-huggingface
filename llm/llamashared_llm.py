import os
import logging
import requests
from typing import List, Dict, Any, Optional
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.callbacks.manager import CallbackManagerForLLMRun
from langchain_core.outputs import ChatResult, ChatGeneration
from langchain_core.utils import get_from_dict_or_env
from pydantic import Field
import json

# Configure logging
logging.basicConfig(level=logging.DEBUG if os.getenv("DEBUG", "false").lower() == "true" else logging.INFO)
logger = logging.getLogger(__name__)

class LlamaSharedLLM(BaseChatModel):
    """Custom LangChain LLM for LlamaShared API"""
    
    api_url: str = Field(...)
    api_key: str = Field(...)
    model_name: str = Field(default="meta-llama/Meta-Llama-3-70B-Instruct")
    max_tokens: int = Field(default=2048)
    temperature: float = Field(default=0.7)
    ssl_verify: bool = Field(default=True)
    
    def __init__(self, api_url: str = None, api_key: str = None, **kwargs):
        # Get values from parameters or environment
        if api_url is None:
            api_url = os.getenv("LLAMASHARED_API_URL")
        if api_key is None:
            api_key = os.getenv("LLAMASHARED_API_KEY")
        
        if not api_url:
            raise ValueError("api_url is required. Set LLAMASHARED_API_URL environment variable or pass api_url parameter.")
        if not api_key:
            raise ValueError("api_key is required. Set LLAMASHARED_API_KEY environment variable or pass api_key parameter.")
        
        # Set defaults for other fields
        model_name = kwargs.get("model_name", "meta-llama/Meta-Llama-3-70B-Instruct")
        max_tokens = kwargs.get("max_tokens", 2048)
        temperature = kwargs.get("temperature", 0.7)
        ssl_verify = kwargs.get("ssl_verify", str(os.getenv("SSL_VERIFY", "true")).lower() == "true")
        
        # Call parent constructor with all required fields
        super().__init__(
            api_url=api_url,
            api_key=api_key,
            model_name=model_name,
            max_tokens=max_tokens,
            temperature=temperature,
            ssl_verify=ssl_verify,
            **kwargs
        )
        
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
            try:
                # Convert tools to OpenAI format
                tools_list = []
                for tool in self.bound_tools:
                    if hasattr(tool, 'to_openai_format'):
                        tools_list.append(tool.to_openai_format())
                    elif hasattr(tool, 'to_openai_tool'):
                        tools_list.append(tool.to_openai_tool())
                    else:
                        # Fallback: create tool format manually
                        tools_list.append({
                            "type": "function",
                            "function": {
                                "name": tool.name,
                                "description": tool.description,
                                "parameters": tool.args_schema.schema() if hasattr(tool, 'args_schema') else {}
                            }
                        })
                
                payload["tools"] = tools_list
                logger.debug(f"Added {len(tools_list)} tools to payload")
            except Exception as e:
                logger.warning(f"Failed to add tools: {e}")
                # Continue without tools if there's an issue
        
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
            
            # Extract content from response
            if "choices" not in response_json or not response_json["choices"]:
                raise ValueError("No choices in response")
            
            choice = response_json["choices"][0]
            if "message" not in choice:
                raise ValueError("No message in choice")
            
            message = choice["message"]
            content = message.get("content", "")
            
            # Handle tool calls if present
            tool_calls = message.get("tool_calls")
            if tool_calls:
                logger.debug(f"Received tool calls: {tool_calls}")
                # For now, just include the content - tool handling is done by LangGraph
            
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
