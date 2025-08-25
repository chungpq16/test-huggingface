import requests
import json
import logging
from typing import Dict, List, Any, Optional
from langchain.llms.base import LLM
from langchain.callbacks.manager import CallbackManagerForLLMRun
from config import config

logger = logging.getLogger(__name__)

class CustomLLM(LLM):
    """Custom LLM implementation for the LLM farm API"""
    
    api_url: str
    api_key: str
    model: str
    max_tokens: int
    temperature: float
    top_p: float
    verify_ssl: bool
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.api_url = config.LLM_API_URL
        self.api_key = config.LLM_API_KEY
        self.model = config.LLM_MODEL
        self.max_tokens = config.MAX_TOKENS
        self.temperature = config.TEMPERATURE
        self.top_p = config.TOP_P
        self.verify_ssl = config.VERIFY_SSL
        
        logger.info(f"Initialized CustomLLM with model: {self.model}")
        logger.debug(f"API URL: {self.api_url}")
        logger.debug(f"SSL Verification: {self.verify_ssl}")
    
    @property
    def _llm_type(self) -> str:
        return "custom_llm_farm"
    
    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        """Call the LLM API"""
        
        headers = {
            "accept": "application/json",
            "KeyId": self.api_key,
            "Content-Type": "application/json"
        }
        
        # Prepare the payload based on the full API specification
        payload = {
            "messages": [{"role": "user", "content": prompt}],
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "n": 1,
            "stream": False,
            "frequency_penalty": 0,
            "presence_penalty": 0,
            "logprobs": False,
            "echo": False,
            "stop": stop if stop else None,
            "seed": None,
            "top_k": -1,
            "min_p": 0,
            "repetition_penalty": 1,
            "length_penalty": 1,
            "early_stopping": False,
            "ignore_eos": False,
            "min_tokens": 0,
            "skip_special_tokens": True,
            "spaces_between_special_tokens": True,
            "add_generation_prompt": True,
            "add_special_tokens": False,
            "include_stop_str_in_output": False
        }
        
        # Remove None values to keep payload clean
        payload = {k: v for k, v in payload.items() if v is not None}
        
        logger.debug(f"Sending request to {self.api_url}")
        logger.debug(f"Payload: {json.dumps(payload, indent=2)}")
        
        try:
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                verify=self.verify_ssl,
                timeout=60
            )
            
            logger.debug(f"Response status: {response.status_code}")
            logger.debug(f"Response headers: {dict(response.headers)}")
            
            response.raise_for_status()
            
            result = response.json()
            logger.debug(f"Response JSON: {json.dumps(result, indent=2)}")
            
            # Extract the response content
            if "choices" in result and len(result["choices"]) > 0:
                content = result["choices"][0].get("message", {}).get("content", "")
                if not content:
                    # Fallback for different response formats
                    content = result["choices"][0].get("text", "")
                
                logger.info(f"Successfully received response of length: {len(content)}")
                return content
            else:
                logger.warning("No choices found in response")
                return "Error: No response content found"
                
        except requests.exceptions.SSLError as e:
            logger.error(f"SSL Error: {e}")
            return f"SSL Error: {e}. Try setting VERIFY_SSL=false in your .env file"
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {e}")
            return f"Request Error: {e}"
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            logger.error(f"Response text: {response.text}")
            return f"JSON Error: {e}"
            
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return f"Unexpected Error: {e}"
    
    @property
    def _identifying_params(self) -> Dict[str, Any]:
        """Get the identifying parameters."""
        return {
            "model": self.model,
            "api_url": self.api_url,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "top_p": self.top_p,
        }
