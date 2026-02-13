"""
Response handlers for different model formats and structures

Different Ollama models may have different response formats:
- Some models (like DeepSeek-R1) include <think>...</think> tags
- Some models use different formatting conventions
- Some models have special tokens or markers

This module provides utilities to handle these differences transparently.
"""

import re
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum


class ModelType(Enum):
    """Known model types with special response formats"""
    STANDARD = "standard"  # Standard models without special formatting
    THINKING = "thinking"  # Models that show reasoning (e.g., DeepSeek-R1)
    CODE = "code"  # Code-focused models
    CUSTOM = "custom"  # Custom handler


@dataclass
class ProcessedResponse:
    """Container for a processed model response"""
    content: str  # The main response content
    thinking: Optional[List[str]] = None  # Extracted thinking/reasoning
    metadata: Optional[Dict[str, Any]] = None  # Additional metadata
    raw_content: Optional[str] = None  # Original unprocessed content


class ModelResponseHandler:
    """
    Handle different model response formats intelligently
    
    Example:
        >>> handler = ModelResponseHandler()
        >>> response = handler.process("<think>reasoning</think>Answer here")
        >>> print(response.content)  # "Answer here"
        >>> print(response.thinking)  # ["reasoning"]
    """
    
    def __init__(self, model_type: ModelType = ModelType.STANDARD, custom_patterns: Optional[Dict] = None):
        """
        Initialize response handler
        
        Args:
            model_type: Type of model (determines which processing to apply)
            custom_patterns: Optional custom regex patterns for specific processing
        """
        self.model_type = model_type
        self.custom_patterns = custom_patterns or {}
        
    def process(self, raw_response: str, **kwargs) -> ProcessedResponse:
        """
        Process a raw model response based on model type
        
        Args:
            raw_response: Raw text from the model
            **kwargs: Additional processing options
            
        Returns:
            ProcessedResponse with cleaned content and extracted metadata
        """
        if self.model_type == ModelType.THINKING:
            return self._process_thinking_model(raw_response, **kwargs)
        elif self.model_type == ModelType.CODE:
            return self._process_code_model(raw_response, **kwargs)
        elif self.model_type == ModelType.CUSTOM:
            return self._process_custom(raw_response, **kwargs)
        else:
            return self._process_standard(raw_response, **kwargs)
    
    def _process_standard(self, raw_response: str, **kwargs) -> ProcessedResponse:
        """Process standard model responses"""
        cleaned = self._basic_cleanup(raw_response)
        return ProcessedResponse(
            content=cleaned,
            raw_content=raw_response,
            metadata={'model_type': 'standard'}
        )
    
    def _process_thinking_model(self, raw_response: str, **kwargs) -> ProcessedResponse:
        """
        Process models that include thinking/reasoning tags
        (e.g., DeepSeek-R1, or models using <think> tags)
        """
        # Extract thinking content between <think> and </think>
        thinking_blocks = []
        thinking_pattern = r'<think>(.*?)</think>'
        
        for match in re.finditer(thinking_pattern, raw_response, flags=re.DOTALL):
            thinking_blocks.append(match.group(1).strip())
        
        # Remove thinking tags and their content
        cleaned = re.sub(thinking_pattern, '', raw_response, flags=re.DOTALL)
        
        # Remove other common reasoning tags
        cleaned = re.sub(r'<reasoning>(.*?)</reasoning>', '', cleaned, flags=re.DOTALL)
        cleaned = re.sub(r'<thought>(.*?)</thought>', '', cleaned, flags=re.DOTALL)
        
        # Remove leading XML-style tags
        cleaned = re.sub(r'^<[^>]+>\s*', '', cleaned)
        
        # Basic cleanup
        cleaned = self._basic_cleanup(cleaned)
        
        return ProcessedResponse(
            content=cleaned,
            thinking=thinking_blocks if thinking_blocks else None,
            raw_content=raw_response,
            metadata={'model_type': 'thinking', 'thinking_blocks_count': len(thinking_blocks)}
        )
    
    def _process_code_model(self, raw_response: str, **kwargs) -> ProcessedResponse:
        """Process code-focused model responses"""
        cleaned = self._basic_cleanup(raw_response)
        
        # Extract code blocks
        code_blocks = self._extract_code_blocks(raw_response)
        
        return ProcessedResponse(
            content=cleaned,
            raw_content=raw_response,
            metadata={
                'model_type': 'code',
                'code_blocks': code_blocks,
                'code_blocks_count': len(code_blocks)
            }
        )
    
    def _process_custom(self, raw_response: str, **kwargs) -> ProcessedResponse:
        """Process with custom patterns"""
        cleaned = raw_response
        extracted_data = {}
        
        for pattern_name, pattern in self.custom_patterns.items():
            matches = re.findall(pattern, cleaned, flags=re.DOTALL)
            if matches:
                extracted_data[pattern_name] = matches
                cleaned = re.sub(pattern, '', cleaned, flags=re.DOTALL)
        
        cleaned = self._basic_cleanup(cleaned)
        
        return ProcessedResponse(
            content=cleaned,
            raw_content=raw_response,
            metadata={
                'model_type': 'custom',
                'extracted': extracted_data
            }
        )
    
    def _basic_cleanup(self, text: str) -> str:
        """Apply basic text cleanup"""
        # Remove excessive newlines
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Remove trailing whitespace from lines
        text = '\n'.join(line.rstrip() for line in text.split('\n'))
        
        # Remove leading/trailing whitespace
        text = text.strip()
        
        return text
    
    def _extract_code_blocks(self, text: str) -> List[Dict[str, str]]:
        """Extract code blocks from markdown-formatted text"""
        pattern = r'```(\w+)?\n(.*?)```'
        matches = re.findall(pattern, text, re.DOTALL)
        
        code_blocks = []
        for language, code in matches:
            code_blocks.append({
                'language': language or 'text',
                'code': code.strip()
            })
        
        return code_blocks


class AutoModelHandler:
    """
    Automatically detect and handle different model response formats
    
    Example:
        >>> handler = AutoModelHandler()
        >>> response = handler.process_response(raw_text, model_name="deepseek-r1")
    """
    
    # Known models and their types
    MODEL_TYPE_MAP = {
        'deepseek-r1': ModelType.THINKING,
        'qwen': ModelType.THINKING,
        'codellama': ModelType.CODE,
        'starcoder': ModelType.CODE,
        'phind-codellama': ModelType.CODE,
    }
    
    def __init__(self):
        """Initialize auto handler with cache of handlers"""
        self._handlers_cache: Dict[str, ModelResponseHandler] = {}
    
    def get_handler(self, model_name: str) -> ModelResponseHandler:
        """
        Get or create a handler for a specific model
        
        Args:
            model_name: Name of the model
            
        Returns:
            Appropriate ModelResponseHandler
        """
        if model_name in self._handlers_cache:
            return self._handlers_cache[model_name]
        
        # Detect model type
        model_type = self._detect_model_type(model_name)
        handler = ModelResponseHandler(model_type)
        
        self._handlers_cache[model_name] = handler
        return handler
    
    def _detect_model_type(self, model_name: str) -> ModelType:
        """
        Detect the model type based on model name
        
        Args:
            model_name: Name of the model
            
        Returns:
            ModelType enum value
        """
        # Check exact matches first
        for pattern, model_type in self.MODEL_TYPE_MAP.items():
            if pattern in model_name.lower():
                return model_type
        
        # Default to standard
        return ModelType.STANDARD
    
    def process_response(
        self,
        raw_response: str,
        model_name: str,
        **kwargs
    ) -> ProcessedResponse:
        """
        Auto-detect and process a model response
        
        Args:
            raw_response: Raw response text from model
            model_name: Name of the model that generated the response
            **kwargs: Additional processing options
            
        Returns:
            ProcessedResponse with processed content
        """
        handler = self.get_handler(model_name)
        return handler.process(raw_response, **kwargs)
    
    def register_model_type(self, model_pattern: str, model_type: ModelType):
        """
        Register a custom model type mapping
        
        Args:
            model_pattern: Pattern to match in model name
            model_type: Type to assign to matching models
        """
        self.MODEL_TYPE_MAP[model_pattern] = model_type
        # Clear cache to force re-detection
        self._handlers_cache.clear()


# Convenience functions for quick use
def clean_thinking_tags(text: str) -> Tuple[str, List[str]]:
    """
    Quick utility to remove thinking tags from response
    
    Args:
        text: Text with potential thinking tags
        
    Returns:
        Tuple of (cleaned_text, thinking_blocks)
    """
    handler = ModelResponseHandler(ModelType.THINKING)
    result = handler.process(text)
    return result.content, result.thinking or []


def auto_clean_response(text: str, model_name: str) -> str:
    """
    Quick utility to auto-clean a response based on model name
    
    Args:
        text: Raw response text
        model_name: Name of the model
        
    Returns:
        Cleaned response content
    """
    auto_handler = AutoModelHandler()
    result = auto_handler.process_response(text, model_name)
    return result.content
