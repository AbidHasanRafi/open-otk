"""
Chat session utilities for maintaining conversation context
"""

from typing import List, Dict, Optional
from .client import OllamaClient
from .response_handlers import AutoModelHandler, ProcessedResponse


class ChatSession:
    """
    Maintain a chat session with conversation history
    
    Example:
        >>> session = ChatSession("llama2")
        >>> response = session.send("Hello!")
        >>> response = session.send("How are you?")
        >>> session.clear_history()
    """
    
    def __init__(
        self,
        model: str,
        system_message: Optional[str] = None,
        client: Optional[OllamaClient] = None,
        temperature: float = 0.7,
        max_history: int = 50,
        auto_process: bool = True
    ):
        """
        Initialize a chat session
        
        Args:
            model: Name of the model to use
            system_message: Optional system message to set context
            client: Optional OllamaClient instance
            temperature: Sampling temperature
            max_history: Maximum number of messages to keep in history
            auto_process: Whether to automatically process responses based on model type
        """
        self.model = model
        self.client = client or OllamaClient()
        self.temperature = temperature
        self.max_history = max_history
        self.auto_process = auto_process
        self.response_handler = AutoModelHandler() if auto_process else None
        self.messages: List[Dict[str, str]] = []
        self.last_processed_response: Optional[ProcessedResponse] = None
        
        if system_message:
            self.messages.append({
                "role": "system",
                "content": system_message
            })
    
    def send(self, message: str, stream: bool = False) -> str:
        """
        Send a message and get a response
        
        Args:
            message: User message to send
            stream: Whether to stream the response
            
        Returns:
            Assistant's response (processed if auto_process is enabled)
        """
        # Add user message
        self.messages.append({
            "role": "user",
            "content": message
        })
        
        # Trim history if needed
        self._trim_history()
        
        # Get response
        if stream:
            response_text = ""
            for chunk in self.client.stream_chat(
                model=self.model,
                messages=self.messages,
                temperature=self.temperature
            ):
                print(chunk, end='', flush=True)
                response_text += chunk
            print()  # New line after streaming
        else:
            response_text = self.client.chat(
                model=self.model,
                messages=self.messages,
                temperature=self.temperature
            )
        
        # Process response if auto_process is enabled
        if self.auto_process and self.response_handler:
            processed = self.response_handler.process_response(response_text, self.model)
            self.last_processed_response = processed
            final_response = processed.content
            
            # Store thinking in metadata if available
            if processed.thinking:
                print(f"\n💭 [Model showed {len(processed.thinking)} thinking step(s)]")
        else:
            final_response = response_text
            self.last_processed_response = None
        
        # Add assistant response to history
        self.messages.append({
            "role": "assistant",
            "content": final_response
        })
        
        return final_response
    
    def send_stream(self, message: str):
        """
        Send a message and stream the response
        
        Args:
            message: User message to send
            
        Yields:
            Chunks of the assistant's response
        """
        # Add user message
        self.messages.append({
            "role": "user",
            "content": message
        })
        
        # Trim history if needed
        self._trim_history()
        
        # Stream response
        response_text = ""
        for chunk in self.client.stream_chat(
            model=self.model,
            messages=self.messages,
            temperature=self.temperature
        ):
            response_text += chunk
            yield chunk
        
        # Add complete response to history
        self.messages.append({
            "role": "assistant",
            "content": response_text
        })
    
    def clear_history(self, keep_system: bool = True):
        """
        Clear conversation history
        
        Args:
            keep_system: Whether to keep the system message
        """
        if keep_system and self.messages and self.messages[0]['role'] == 'system':
            system_msg = self.messages[0]
            self.messages = [system_msg]
        else:
            self.messages = []
    
    def get_history(self) -> List[Dict[str, str]]:
        """
        Get the conversation history
        
        Returns:
            List of message dictionaries
        """
        return self.messages.copy()
    
    def get_last_thinking(self) -> Optional[List[str]]:
        """
        Get the thinking/reasoning from the last response (if available)
        
        Returns:
            List of thinking blocks from the last response, or None
        """
        if self.last_processed_response and self.last_processed_response.thinking:
            return self.last_processed_response.thinking
        return None
    
    def get_last_metadata(self) -> Optional[Dict]:
        """
        Get metadata from the last processed response
        
        Returns:
            Metadata dictionary, or None
        """
        if self.last_processed_response:
            return self.last_processed_response.metadata
        return None
    
    def set_system_message(self, message: str):
        """
        Set or update the system message
        
        Args:
            message: New system message
        """
        # Remove old system message if exists
        if self.messages and self.messages[0]['role'] == 'system':
            self.messages.pop(0)
        
        # Add new system message at the beginning
        self.messages.insert(0, {
            "role": "system",
            "content": message
        })
    
    def _trim_history(self):
        """
        Trim history to max_history length, keeping system message
        """
        if len(self.messages) <= self.max_history:
            return
        
        # Check if first message is system message
        has_system = self.messages and self.messages[0]['role'] == 'system'
        
        if has_system:
            # Keep system message + most recent messages
            system_msg = self.messages[0]
            recent_messages = self.messages[-(self.max_history - 1):]
            self.messages = [system_msg] + recent_messages
        else:
            # Keep most recent messages
            self.messages = self.messages[-self.max_history:]
    
    def export_history(self, filepath: str):
        """
        Export conversation history to a JSON file
        
        Args:
            filepath: Path to save the history
        """
        import json
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump({
                'model': self.model,
                'temperature': self.temperature,
                'messages': self.messages
            }, f, indent=2, ensure_ascii=False)
    
    def load_history(self, filepath: str):
        """
        Load conversation history from a JSON file
        
        Args:
            filepath: Path to load the history from
        """
        import json
        
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.model = data.get('model', self.model)
            self.temperature = data.get('temperature', self.temperature)
            self.messages = data.get('messages', [])
