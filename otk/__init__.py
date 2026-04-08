"""
Open OTK (Open Ollama Toolkit)
Professional Python framework for local LLM orchestration, hybrid RAG,
automated evaluation, and pipeline composition with Ollama models.

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
    chunk_text_by_tokens,
    create_prompt_template,
)
from .response_handlers import (
    ModelResponseHandler,
    AutoModelHandler,
    ModelType,
    ProcessedResponse,
    clean_thinking_tags,
    auto_clean_response,
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
    ComparisonResult,
)

# New modules — lazy-friendly re-exports
from .profiler import InferenceProfiler, TelemetryStore, InferenceMetrics
from .structured import StructuredGenerator, StructuredOutputError
from .rag import HybridRAG, RecursiveChunker, BM25Index, DenseIndex
from .evaluation import (
    LLMJudge,
    EvaluationSuite,
    EvaluationReport,
    JudgeConfig,
    StatisticalAnalysis,
    EvaluationDimension,
)
from .pipeline import (
    Pipeline,
    PipelineBuilder,
    PipelineNode,
    LLMNode,
    TransformNode,
    ConditionalNode,
    ReduceNode,
    PipelineResult,
)
from .router import ModelRouter, TaskClassifier, TaskType, RoutingDecision

__version__ = "2.0.0"
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
    "chunk_text_by_tokens",
    "create_prompt_template",
    # Response handling
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
    # Profiler
    "InferenceProfiler",
    "TelemetryStore",
    "InferenceMetrics",
    # Structured output
    "StructuredGenerator",
    "StructuredOutputError",
    # Hybrid RAG
    "HybridRAG",
    "RecursiveChunker",
    "BM25Index",
    "DenseIndex",
    # Evaluation
    "LLMJudge",
    "EvaluationSuite",
    "EvaluationReport",
    "JudgeConfig",
    "StatisticalAnalysis",
    "EvaluationDimension",
    # Pipeline
    "Pipeline",
    "PipelineBuilder",
    "PipelineNode",
    "LLMNode",
    "TransformNode",
    "ConditionalNode",
    "ReduceNode",
    "PipelineResult",
    # Router
    "ModelRouter",
    "TaskClassifier",
    "TaskType",
    "RoutingDecision",
    # CLI
    "main",
]


def main():
    """Main entry point for the OTK CLI/GUI application"""
    import sys
    import os

    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)

    try:
        import importlib.util
        otk_gui_path = os.path.join(parent_dir, "otk.py")

        if os.path.exists(otk_gui_path):
            spec = importlib.util.spec_from_file_location("otk_gui", otk_gui_path)
            otk_gui = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(otk_gui)
            otk_gui.main()
        else:
            print("OTK GUI not found!")
            print("The OTK library has been installed, but the GUI application is not available.")
            print("\nYou can still use OTK as a Python library:")
            print("  from otk import OllamaClient")
            print("  client = OllamaClient()")
            sys.exit(1)
    except Exception as e:
        print(f"Error launching OTK GUI: {e}")
        print("\nYou can still use OTK as a Python library:")
        print("  from otk import OllamaClient")
        print("  client = OllamaClient()")
        sys.exit(1)
