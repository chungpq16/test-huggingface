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
    bound_tools: Optional[List] = Field(default=None)
    
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
        
        # Extract specific parameters and remove them from kwargs to avoid conflicts
        model_name = kwargs.pop("model_name", "meta-llama/Meta-Llama-3-70B-Instruct")
        max_tokens = kwargs.pop("max_tokens", 2048)
        temperature = kwargs.pop("temperature", 0.7)
        ssl_verify = kwargs.pop("ssl_verify", str(os.getenv("SSL_VERIFY", "true")).lower() == "true")
        bound_tools = kwargs.pop("bound_tools", None)
        
        # Call parent constructor with all required fields
        super().__init__(
            api_url=api_url,
            api_key=api_key,
            model_name=model_name,
            max_tokens=max_tokens,
            temperature=temperature,
            ssl_verify=ssl_verify,
            bound_tools=bound_tools,
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
        
        # Prepare payload with only essential fields first
        payload = {
            "messages": api_messages,
            "model": self.model_name,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
        }
        
        # Add tools if bound
        if self.bound_tools and len(self.bound_tools) > 0:
            try:
                # Convert tools to OpenAI format
                tools_list = []
                for tool in self.bound_tools:
                    # Use the standard LangChain method for OpenAI tool conversion
                    if hasattr(tool, 'to_openai_tool'):
                        tools_list.append(tool.to_openai_tool())
                    elif hasattr(tool, 'to_openai_format'):
                        tools_list.append(tool.to_openai_format())
                    else:
                        # Manual conversion for LangChain @tool decorated functions
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
                                # Convert pydantic schema to OpenAI function parameters format
                                if 'properties' in schema:
                                    tool_schema["function"]["parameters"] = {
                                        "type": "object",
                                        "properties": schema['properties'],
                                        "required": schema.get('required', [])
                                    }
                            except Exception as schema_error:
                                logger.warning(f"Failed to extract schema for tool {tool.name}: {schema_error}")
                                tool_schema["function"]["parameters"] = {"type": "object", "properties": {}}
                        else:
                            tool_schema["function"]["parameters"] = {"type": "object", "properties": {}}
                        
                        tools_list.append(tool_schema)
                
                if tools_list:
                    payload["tools"] = tools_list
                    payload["tool_choice"] = "auto"  # Enable automatic tool selection
                    logger.debug(f"Added {len(tools_list)} tools to payload")
                    logger.debug(f"Tools: {json.dumps(tools_list, indent=2)}")
                else:
                    logger.warning("No tools were successfully converted")
                    
            except Exception as e:
                logger.error(f"Failed to add tools: {e}")
                # Continue without tools if there's an issue
        
        # Clean up payload - remove any None values or empty lists
        payload = {k: v for k, v in payload.items() if v is not None and v != []}
        
        # Add any additional kwargs (but filter out problematic ones)
        filtered_kwargs = {k: v for k, v in kwargs.items() 
                          if k not in ['stop'] and v is not None}  # Remove 'stop' and None values
        payload.update(filtered_kwargs)
        
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
            
            # Enhanced error handling for debugging
            if response.status_code != 200:
                logger.error(f"HTTP {response.status_code} Error")
                logger.error(f"Response headers: {dict(response.headers)}")
                try:
                    error_response = response.json()
                    logger.error(f"Error response body: {json.dumps(error_response, indent=2)}")
                except:
                    logger.error(f"Error response text: {response.text}")
                
                # Provide specific error message
                if response.status_code == 400:
                    raise ValueError(f"Bad Request (400): The API request payload is invalid. Check the logs above for details.")
                elif response.status_code == 401:
                    raise ValueError(f"Unauthorized (401): Invalid API key or authentication failed.")
                elif response.status_code == 403:
                    raise ValueError(f"Forbidden (403): Access denied to the API endpoint.")
                else:
                    raise ValueError(f"HTTP {response.status_code}: {response.text}")
            
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
        # Create a new instance with bound tools to maintain immutability
        return self.__class__(
            api_url=self.api_url,
            api_key=self.api_key,
            model_name=self.model_name,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            ssl_verify=self.ssl_verify,
            bound_tools=tools
        )
