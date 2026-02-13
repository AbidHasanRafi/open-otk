"""
Main client wrapper for Ollama API
"""

import ollama
from typing import Dict, List, Optional, Generator, Any
import json


class OllamaClient:
    """
    Simplified client for interacting with Ollama models
    
    Example:
        >>> client = OllamaClient()
        >>> response = client.generate("llama2", "Tell me a joke")
        >>> print(response)
    """
    
    def __init__(self, host: Optional[str] = None):
        """
        Initialize the Ollama client
        
        Args:
            host: Optional custom host URL (default: http://localhost:11434)
        """
        self.client = ollama.Client(host=host) if host else ollama.Client()
        self.host = host or "http://localhost:11434"
    
    def generate(
        self,
        model: str,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        """
        Generate a response from a model
        
        Args:
            model: Name of the model to use
            prompt: The prompt to send to the model
            system: Optional system message
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters to pass to the API
            
        Returns:
            Generated text response
        """
        options = {
            "temperature": temperature,
        }
        
        if max_tokens:
            options["num_predict"] = max_tokens
            
        options.update(kwargs.get("options", {}))
        
        response = self.client.generate(
            model=model,
            prompt=prompt,
            system=system,
            options=options
        )
        
        return response['response']
    
    def stream_generate(
        self,
        model: str,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        **kwargs
    ) -> Generator[str, None, None]:
        """
        Stream a response from a model
        
        Args:
            model: Name of the model to use
            prompt: The prompt to send to the model
            system: Optional system message
            temperature: Sampling temperature
            **kwargs: Additional parameters
            
        Yields:
            Chunks of generated text
        """
        options = {"temperature": temperature}
        options.update(kwargs.get("options", {}))
        
        stream = self.client.generate(
            model=model,
            prompt=prompt,
            system=system,
            stream=True,
            options=options
        )
        
        for chunk in stream:
            yield chunk['response']
    
    def chat(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """
        Send a chat completion request
        
        Args:
            model: Name of the model to use
            messages: List of message dictionaries with 'role' and 'content'
            temperature: Sampling temperature
            **kwargs: Additional parameters
            
        Returns:
            Assistant's response
        """
        options = {"temperature": temperature}
        options.update(kwargs.get("options", {}))
        
        response = self.client.chat(
            model=model,
            messages=messages,
            options=options
        )
        
        return response['message']['content']
    
    def stream_chat(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        **kwargs
    ) -> Generator[str, None, None]:
        """
        Stream a chat completion response
        
        Args:
            model: Name of the model to use
            messages: List of message dictionaries
            temperature: Sampling temperature
            **kwargs: Additional parameters
            
        Yields:
            Chunks of the assistant's response
        """
        options = {"temperature": temperature}
        options.update(kwargs.get("options", {}))
        
        stream = self.client.chat(
            model=model,
            messages=messages,
            stream=True,
            options=options
        )
        
        for chunk in stream:
            if 'message' in chunk and 'content' in chunk['message']:
                yield chunk['message']['content']
    
    def embeddings(self, model: str, text: str) -> List[float]:
        """
        Generate embeddings for text
        
        Args:
            model: Name of the embedding model
            text: Text to generate embeddings for
            
        Returns:
            List of embedding values
        """
        response = self.client.embeddings(model=model, prompt=text)
        return response['embedding']
    
    def is_running(self) -> bool:
        """
        Check if Ollama is running
        
        Returns:
            True if Ollama is accessible, False otherwise
        """
        try:
            self.client.list()
            return True
        except Exception:
            return False
