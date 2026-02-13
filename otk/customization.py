"""
Customization and hooks system for Ollama Toolkit

This module provides hooks, callbacks, and customization options
to give developers full control over model behavior and responses.
"""

from typing import Callable, Optional, Dict, Any, List
from dataclasses import dataclass, field
from enum import Enum


class HookType(Enum):
    """Types of hooks available"""
    PRE_PROCESS = "pre_process"  # Before sending to model
    POST_PROCESS = "post_process"  # After receiving from model
    PRE_CLEAN = "pre_clean"  # Before response cleaning
    POST_CLEAN = "post_clean"  # After response cleaning
    ERROR = "error"  # On error
    STREAM_CHUNK = "stream_chunk"  # On each streaming chunk


@dataclass
class HookContext:
    """Context passed to hooks"""
    model: str
    input_text: Optional[str] = None
    output_text: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[Exception] = None


class CustomizableModel:
    """
    Wrapper around model interactions with full customization support
    
    Example:
        >>> model = CustomizableModel("llama2")
        >>> model.add_hook(HookType.POST_PROCESS, lambda ctx: print(f"Got: {ctx.output_text}"))
        >>> response = model.generate("Hello")
    """
    
    def __init__(
        self,
        model_name: str,
        client: Optional[Any] = None,
        config: Optional[Dict] = None
    ):
        """
        Initialize customizable model
        
        Args:
            model_name: Name of the model
            client: Optional OllamaClient instance
            config: Optional configuration dictionary
        """
        self.model_name = model_name
        self.config = config or {}
        self.hooks: Dict[HookType, List[Callable]] = {hook: [] for hook in HookType}
        
        # Import here to avoid circular imports
        from .client import OllamaClient
        self.client = client or OllamaClient()
        
        # Custom processing functions
        self.custom_pre_processor: Optional[Callable] = None
        self.custom_post_processor: Optional[Callable] = None
        self.custom_error_handler: Optional[Callable] = None
    
    def add_hook(self, hook_type: HookType, callback: Callable[[HookContext], None]):
        """
        Add a hook callback
        
        Args:
            hook_type: Type of hook
            callback: Function to call (receives HookContext)
        """
        self.hooks[hook_type].append(callback)
    
    def remove_hooks(self, hook_type: Optional[HookType] = None):
        """
        Remove hooks
        
        Args:
            hook_type: Type to remove, or None to remove all
        """
        if hook_type:
            self.hooks[hook_type] = []
        else:
            self.hooks = {hook: [] for hook in HookType}
    
    def _run_hooks(self, hook_type: HookType, context: HookContext):
        """Run all hooks for a given type"""
        for hook in self.hooks[hook_type]:
            try:
                hook(context)
            except Exception as e:
                print(f"Hook error ({hook_type}): {e}")
    
    def set_pre_processor(self, func: Callable[[str], str]):
        """Set custom pre-processing function"""
        self.custom_pre_processor = func
    
    def set_post_processor(self, func: Callable[[str], str]):
        """Set custom post-processing function"""
        self.custom_post_processor = func
    
    def set_error_handler(self, func: Callable[[Exception], str]):
        """Set custom error handler"""
        self.custom_error_handler = func
    
    def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Generate with full customization support
        
        Args:
            prompt: Input prompt
            system: Optional system message
            **kwargs: Additional generation parameters
            
        Returns:
            Generated text (processed through hooks)
        """
        # Pre-process hook
        context = HookContext(model=self.model_name, input_text=prompt)
        self._run_hooks(HookType.PRE_PROCESS, context)
        
        # Custom pre-processor
        if self.custom_pre_processor:
            prompt = self.custom_pre_processor(prompt)
        
        try:
            # Generate
            response = self.client.generate(
                self.model_name,
                prompt,
                system=system,
                **{**self.config, **kwargs}
            )
            
            # Pre-clean hook
            context = HookContext(
                model=self.model_name,
                input_text=prompt,
                output_text=response
            )
            self._run_hooks(HookType.PRE_CLEAN, context)
            
            # Custom post-processor
            if self.custom_post_processor:
                response = self.custom_post_processor(response)
            
            # Post-clean hook
            context.output_text = response
            self._run_hooks(HookType.POST_CLEAN, context)
            
            # Post-process hook
            self._run_hooks(HookType.POST_PROCESS, context)
            
            return response
            
        except Exception as e:
            # Error hook
            context = HookContext(
                model=self.model_name,
                input_text=prompt,
                error=e
            )
            self._run_hooks(HookType.ERROR, context)
            
            # Custom error handler
            if self.custom_error_handler:
                return self.custom_error_handler(e)
            raise
    
    def stream_generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        **kwargs
    ):
        """
        Stream generate with hooks
        
        Args:
            prompt: Input prompt
            system: Optional system message
            **kwargs: Additional parameters
            
        Yields:
            Generated text chunks
        """
        # Pre-process
        if self.custom_pre_processor:
            prompt = self.custom_pre_processor(prompt)
        
        try:
            for chunk in self.client.stream_generate(
                self.model_name,
                prompt,
                system=system,
                **{**self.config, **kwargs}
            ):
                # Chunk hook
                context = HookContext(
                    model=self.model_name,
                    output_text=chunk
                )
                self._run_hooks(HookType.STREAM_CHUNK, context)
                
                yield chunk
                
        except Exception as e:
            context = HookContext(model=self.model_name, error=e)
            self._run_hooks(HookType.ERROR, context)
            
            if self.custom_error_handler:
                yield self.custom_error_handler(e)
            else:
                raise


@dataclass
class ModelConfig:
    """Configuration for model behavior"""
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    top_p: float = 0.9
    top_k: int = 40
    repeat_penalty: float = 1.1
    stop_sequences: List[str] = field(default_factory=list)
    custom_options: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to Ollama options format"""
        options = {
            'temperature': self.temperature,
            'top_p': self.top_p,
            'top_k': self.top_k,
            'repeat_penalty': self.repeat_penalty,
        }
        
        if self.max_tokens:
            options['num_predict'] = self.max_tokens
        
        if self.stop_sequences:
            options['stop'] = self.stop_sequences
        
        options.update(self.custom_options)
        return options


class ModelPresets:
    """Pre-configured model settings for common use cases"""
    
    @staticmethod
    def creative() -> ModelConfig:
        """High creativity settings"""
        return ModelConfig(temperature=0.9, top_p=0.95)
    
    @staticmethod
    def factual() -> ModelConfig:
        """Factual, deterministic settings"""
        return ModelConfig(temperature=0.2, top_p=0.5, repeat_penalty=1.2)
    
    @staticmethod
    def balanced() -> ModelConfig:
        """Balanced settings"""
        return ModelConfig(temperature=0.7, top_p=0.9)
    
    @staticmethod
    def code() -> ModelConfig:
        """Settings optimized for code generation"""
        return ModelConfig(
            temperature=0.2,
            top_p=0.95,
            repeat_penalty=1.05,
            stop_sequences=['```\n\n']
        )
    
    @staticmethod
    def conversational() -> ModelConfig:
        """Natural conversation settings"""
        return ModelConfig(temperature=0.8, top_p=0.92, repeat_penalty=1.1)
    
    @staticmethod
    def custom(
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> ModelConfig:
        """Create custom configuration"""
        return ModelConfig(
            temperature=temperature,
            max_tokens=max_tokens,
            custom_options=kwargs
        )


# Useful custom processors and hooks

def uppercase_hook(ctx: HookContext):
    """Example hook: Convert output to uppercase"""
    if ctx.output_text:
        ctx.output_text = ctx.output_text.upper()


def log_hook(ctx: HookContext):
    """Example hook: Log all interactions"""
    if ctx.input_text:
        print(f"[LOG] Input: {ctx.input_text[:50]}...")
    if ctx.output_text:
        print(f"[LOG] Output: {ctx.output_text[:50]}...")


def length_limiter(max_length: int) -> Callable[[str], str]:
    """Create a processor that limits response length"""
    def limiter(text: str) -> str:
        if len(text) > max_length:
            return text[:max_length] + "..."
        return text
    return limiter


def keyword_filter(keywords: List[str]) -> Callable[[str], str]:
    """Create a processor that filters out keywords"""
    def filter_func(text: str) -> str:
        for keyword in keywords:
            text = text.replace(keyword, "[FILTERED]")
        return text
    return filter_func


def add_prefix(prefix: str) -> Callable[[str], str]:
    """Create a processor that adds prefix to responses"""
    def processor(text: str) -> str:
        return f"{prefix}{text}"
    return processor


def add_suffix(suffix: str) -> Callable[[str], str]:
    """Create a processor that adds suffix to responses"""
    def processor(text: str) -> str:
        return f"{text}{suffix}"
    return processor


# Builder pattern for easy customization

class ModelBuilder:
    """
    Fluent interface for building customized models
    
    Example:
        >>> model = (ModelBuilder("llama2")
        ...          .with_preset("creative")
        ...          .with_hook(HookType.POST_PROCESS, log_hook)
        ...          .with_post_processor(length_limiter(500))
        ...          .build())
    """
    
    def __init__(self, model_name: str):
        self.model_name = model_name
        self._config = ModelConfig()
        self._hooks: List[tuple] = []
        self._pre_processor = None
        self._post_processor = None
        self._error_handler = None
    
    def with_config(self, config: ModelConfig):
        """Set configuration"""
        self._config = config
        return self
    
    def with_preset(self, preset_name: str):
        """Use a preset configuration"""
        presets = {
            'creative': ModelPresets.creative,
            'factual': ModelPresets.factual,
            'balanced': ModelPresets.balanced,
            'code': ModelPresets.code,
            'conversational': ModelPresets.conversational,
        }
        if preset_name in presets:
            self._config = presets[preset_name]()
        return self
    
    def with_temperature(self, temp: float):
        """Set temperature"""
        self._config.temperature = temp
        return self
    
    def with_max_tokens(self, max_tokens: int):
        """Set max tokens"""
        self._config.max_tokens = max_tokens
        return self
    
    def with_hook(self, hook_type: HookType, callback: Callable):
        """Add a hook"""
        self._hooks.append((hook_type, callback))
        return self
    
    def with_pre_processor(self, func: Callable):
        """Set pre-processor"""
        self._pre_processor = func
        return self
    
    def with_post_processor(self, func: Callable):
        """Set post-processor"""
        self._post_processor = func
        return self
    
    def with_error_handler(self, func: Callable):
        """Set error handler"""
        self._error_handler = func
        return self
    
    def build(self) -> CustomizableModel:
        """Build the customizable model"""
        model = CustomizableModel(
            self.model_name,
            config=self._config.to_dict()
        )
        
        # Add hooks
        for hook_type, callback in self._hooks:
            model.add_hook(hook_type, callback)
        
        # Set processors
        if self._pre_processor:
            model.set_pre_processor(self._pre_processor)
        if self._post_processor:
            model.set_post_processor(self._post_processor)
        if self._error_handler:
            model.set_error_handler(self._error_handler)
        
        return model
