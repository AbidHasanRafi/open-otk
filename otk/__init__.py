"""
Open OTK (Open Ollama Toolkit)
Professional Python library for building AI applications with Ollama models

This library provides a complete development toolkit for integrating Ollama's local LLM models
into production-ready Python applications with full customization, experimentation, and GUI tools.

Author: Md. Abid Hasan Rafi (AI Extension)
License: MIT
"""

from .client import OllamaClient
from .models import ModelManager
from .chat import ChatSession
from .utils import (
    format_response,
    estimate_tokens,
    chunk_text,
    create_prompt_template
)
from .response_handlers import (
    ModelResponseHandler,
    AutoModelHandler,
    ModelType,
    ProcessedResponse,
    clean_thinking_tags,
    auto_clean_response
)
from .customization import (
    CustomizableModel,
    ModelConfig,
    ModelPresets,
    ModelBuilder,
    HookType,
    HookContext,
)
from .experimentation import (
    ModelExperiment,
    ModelPlayground,
    ABTest,
    ExperimentResult,
    ComparisonResult
)

__version__ = "1.0.0"
__author__ = "Md. Abid Hasan Rafi (AI Extension)"
__license__ = "MIT"
__project__ = "Open OTK (Open Ollama Toolkit)"

__all__ = [
    # Core
    "OllamaClient",
    "ModelManager",
    "ChatSession",
    # Utils
    "format_response",
    "estimate_tokens",
    "chunk_text",
    "create_prompt_template",
    # Response Handling
    "ModelResponseHandler",
    "AutoModelHandler",
    "ModelType",
    "ProcessedResponse",
    "clean_thinking_tags",
    "auto_clean_response",
    # Customization
    "CustomizableModel",
    "ModelConfig",
    "ModelPresets",
    "ModelBuilder",
    "HookType",
    "HookContext",
    # Experimentation
    "ModelExperiment",
    "ModelPlayground",
    "ABTest",
    "ExperimentResult",
    "ComparisonResult",
]
