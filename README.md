# Open OTK (Open Ollama Toolkit)

![Open OTK Cover](https://raw.githubusercontent.com/abidhasanrafi/open-otk/main/otk-cover.jpg)

**An intelligent Python framework for local LLM orchestration, hybrid retrieval-augmented generation, automated evaluation, and pipeline composition with Ollama.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Version](https://img.shields.io/badge/version-2.0.0-green.svg)](setup.py)


## Overview

Open OTK is a research-grade framework that transforms [Ollama](https://ollama.ai) from a simple local LLM runner into a full orchestration platform. It provides:

- **Pipeline Composition Engine** — DAG-based multi-step LLM workflows with parallel execution
- **Hybrid RAG Engine** — BM25 sparse + HNSW dense retrieval with Reciprocal Rank Fusion and LLM reranking
- **LLM-as-Judge Evaluation** — Automated quality assessment with statistical significance testing (t-test, bootstrap CI, Cohen's d)
- **Intelligent Model Router** — Task-aware model selection with epsilon-greedy learning from performance history
- **Structured Output Engine** — Guaranteed JSON/Pydantic output with schema validation and self-correction
- **REST API Server** — FastAPI server with WebSocket streaming, session management, and rate limiting
- **Resource Profiler** — Tokens/sec, TTFT, CPU/RAM/GPU telemetry with SQLite persistence
- **Desktop GUI** — Modern Tkinter application with sidebar navigation, evaluation lab, template generation, and chat interface

Everything runs **fully offline** with no cloud dependencies.


## Architecture

```
flowchart TD
    %% REST API Layer
    REST[/"REST API Layer (FastAPI)"/]
    REST -->|"/v1/generate, /v1/chat, /v1/stream(WS), /v1/rag/query, /v1/pipeline/run, /v1/evaluate, /v1/structured"| CORE

    %% Core Engine
    CORE["Core Engine (otk package)"]
    CORE --> PIPE["Pipeline Composition Engine (DAG)"]
    CORE --> MODEL["Model Router (ε-greedy)"]
    CORE --> STRUCT["Structured Output Engine (JSON/Pyda)"]

    PIPE --> EVAL["Evaluation Framework (LLM Judge)"]
    MODEL --> RESOURCE["Resource Profiler (telemetry)"]
    STRUCT --> CLIENT["OllamaClient (retry, metadata)"]

    %% Hybrid RAG Engine
    CORE --> RAG["Hybrid RAG Engine"]
    RAG --> SEM["Semantic Chunker"]
    RAG --> BM25["BM25 Sparse Index"]
    RAG --> HNSW["HNSW Dense Index (or NumPy fallback)"]

    BM25 --> RRF["Reciprocal Rank Fusion (RRF)"]
    HNSW --> RRF
    SEM --> RRF

    RRF --> RERANK["LLM Reranker"]
```


## Installation

### Prerequisites

1. Install [Ollama](https://ollama.com/download)
2. Pull at least one model: `ollama pull gemma4`
3. Ensure Ollama is running

### Install from PyPI

```bash
pip install open-otk
```

### Install from Source

```bash
git clone https://github.com/abidhasanrafi/open-otk.git
cd open-otk
pip install -e .
```

### Optional Dependencies

Install extras for specific features:

```bash
pip install open-otk[rag]          # HNSW vector index (hnswlib)
pip install open-otk[server]       # FastAPI REST API server
pip install open-otk[eval]         # scipy for statistical tests
pip install open-otk[structured]   # Pydantic model validation
pip install open-otk[tokenizer]    # tiktoken for accurate token counts
pip install open-otk[all]          # Everything above
pip install open-otk[dev]          # pytest, black, flake8 for development
```


## Quick Start

### Generate Text

```python
from otk import OllamaClient

client = OllamaClient()
response = client.generate("gemma4", "Explain quantum computing in one paragraph")
print(response)
```

### Chat Session with History

```python
from otk import ChatSession

session = ChatSession("gemma4", system_message="You are a helpful assistant")
print(session.send("What is machine learning?"))
print(session.send("How does it differ from deep learning?"))  # remembers context
```

### Streaming Responses

```python
from otk import OllamaClient

client = OllamaClient()
for chunk in client.stream_generate("gemma4", "Write a short story about AI"):
    print(chunk, end="", flush=True)
```


## Core Modules

### Pipeline Composition Engine

Build multi-step LLM workflows as directed acyclic graphs. Nodes execute in topological order with automatic parallelization of independent branches.

```python
from otk import PipelineBuilder, LLMNode, TransformNode

pipeline = (PipelineBuilder("research")
    .add_node(LLMNode("extract", model="mistral",
                       prompt_template="Extract key facts from: {input}"))
    .add_node(LLMNode("analyze", model="gemma4",
                       prompt_template="Analyze these facts: {extract.output}"))
    .add_node(TransformNode("combine",
                             func=lambda ctx: f"{ctx['extract.output']}\n\n{ctx['analyze.output']}"))
    .add_edge("extract", "analyze")
    .add_edge("analyze", "combine")
    .build())

result = pipeline.execute(input="<document text>")
print(result.outputs["combine"])
```

**Key features:**
- Topological sort via Kahn's algorithm for execution ordering
- `ThreadPoolExecutor` for parallel branch execution
- `ConditionalNode` for lambda-predicate branching
- `ReduceNode` for merging multiple node outputs
- Per-node timing, token count, and retry tracking

### Hybrid RAG Engine

Production-grade retrieval-augmented generation combining sparse and dense retrieval with LLM reranking.

```python
from otk import HybridRAG

rag = HybridRAG(embedding_model="nomic-embed-text", reranker_model="mistral")

rag.add_documents([
    "Python was created by Guido van Rossum in 1991.",
    "JavaScript was created by Brendan Eich in 1995.",
    "Rust was first released in 2010 by Mozilla.",
])

answer, sources = rag.query("Who created Python?", model="gemma4")
print(answer)
```

**Components:**
- `RecursiveChunker` — semantic text splitting respecting sentence/paragraph boundaries
- `BM25Index` — Okapi BM25 sparse retrieval with inverted index
- `DenseIndex` — HNSW approximate nearest neighbor search (falls back to brute-force NumPy if `hnswlib` is not installed)
- `reciprocal_rank_fusion()` — merges sparse and dense rankings with tunable k parameter
- LLM cross-encoder reranker for final relevance scoring

### LLM-as-Judge Evaluation Framework

Automated quality assessment of LLM outputs across multiple dimensions with statistical rigor.

```python
from otk import LLMJudge, JudgeConfig, EvaluationDimension

judge = LLMJudge(JudgeConfig(
    model="gemma4",
    dimensions=[EvaluationDimension.COHERENCE,
                EvaluationDimension.RELEVANCE,
                EvaluationDimension.FACTUALITY],
    trials=3
))

scores = judge.evaluate(
    prompt="Explain gravity",
    response="Gravity is the force that attracts objects toward each other..."
)
for dim, score in scores.items():
    print(f"{dim}: {score.mean:.1f}/5 (±{score.std:.2f})")
```

**Statistical analysis:**
- Paired t-test for mean score differences between models
- Bootstrap confidence intervals (1000 resamples)
- Cohen's d effect size
- Full `EvaluationReport` with export capabilities

### Intelligent Model Router

Automatically selects the best local model for a given task using prompt classification and historical performance data.

```python
from otk import ModelRouter

router = ModelRouter()
decision = router.route("Write a Python function to sort a list")
print(f"Selected: {decision.model} (task: {decision.task_type})")
response = decision.execute()
```

**How it works:**
1. `TaskClassifier` identifies task type (CODE, CREATIVE, FACTUAL_QA, SUMMARIZATION, etc.) using keyword boundary matching
2. `CapabilityMatrix` scores each model's suitability per task type
3. `PerformanceHistory` (SQLite-backed) tracks latency and quality over time
4. Epsilon-greedy selection balances exploration vs exploitation
5. Automatic fallback chain if the selected model fails

### Structured Output Engine

Extract guaranteed JSON or typed objects from LLM responses with schema validation and self-correction.

```python
from otk import StructuredGenerator

gen = StructuredGenerator(model="mistral")

result = gen.generate(
    prompt="Extract info: John Smith, 30 years old, engineer at Google",
    schema={"name": "str", "age": "int", "company": "str"}
)
# result = {"name": "John Smith", "age": 30, "company": "Google"}
```

**Features:**
- JSON schema validation with automatic type coercion
- Auto-retry loop: re-prompts the LLM with error context on parse failure (up to 3 retries)
- Optional Pydantic model validation when `pydantic` is installed

### FastAPI REST API Server

Expose all OTK capabilities as a REST API with OpenAPI documentation.

```bash
# Start the server
otk-server
# or
python -m otk.server
```

**Endpoints:**

| Method | Path | Description |
|--------|------|-------------|
| POST | `/v1/generate` | Text generation with model routing |
| POST | `/v1/chat` | Chat with session management |
| WS | `/v1/stream` | WebSocket streaming responses |
| POST | `/v1/rag/query` | Hybrid RAG query |
| POST | `/v1/rag/ingest` | Add documents to RAG index |
| POST | `/v1/structured` | Structured output generation |
| POST | `/v1/evaluate` | Run evaluation suite |
| GET | `/v1/models` | List models with capability scores |
| GET | `/v1/health` | Health check |
| GET | `/v1/metrics` | Performance telemetry |

Includes CORS support, token-bucket rate limiting, and session-based chat with configurable TTL.

### Resource Profiler & Telemetry

Monitor inference performance and system resources.

```python
from otk import InferenceProfiler, OllamaClient

client = OllamaClient()
profiler = InferenceProfiler()

with profiler.profile(client, "gemma4", "Hello world") as metrics:
    pass

print(f"Tokens/sec: {metrics.tokens_per_second:.1f}")
print(f"TTFT: {metrics.time_to_first_token:.3f}s")
print(f"RAM: {metrics.ram_usage_mb:.0f} MB")
```

All metrics are persisted to SQLite via `TelemetryStore` for longitudinal analysis.


## Desktop GUI Application

Launch the modern Tkinter GUI with sidebar navigation:

```bash
otk                # if installed via pip
python -m otk      # always works
python otk.py      # from source
```

**Features:**
- **Dashboard** — Installed models count, Ollama status, quick actions
- **Chat** — Conversational interface with bubble messages and animated thinking indicator
- **Browse Models** — View and inspect all installed models
- **Manage Models** — Pull, delete, and manage Ollama models
- **Evaluation Lab** — Multi-mode benchmarking: speed benchmark, model comparison, quality evaluation (LLM-as-Judge), and A/B testing with configurable dimensions and model selection
- **Templates** — Interactive wizard to generate starter project files


## Template Generator

Generate ready-to-run project files from the GUI or programmatically:

| Template | Description |
|----------|-------------|
| Simple Chat | Basic conversational interface |
| Streaming Chat | Real-time token-by-token responses |
| Custom Model | Hooks, callbacks, and preprocessing |
| Experimentation | Model comparison and benchmarking |
| Integration | Ready for embedding in larger applications |
| Tkinter GUI | Desktop chat app with bubble messages and thinking animation |
| Advanced Tkinter GUI | Sidebar-navigation app with system prompt editor, temperature control, and content generation |


## Examples

The `examples/` directory contains ready-to-run scripts:

| Example | Description |
|---------|-------------|
| `simple_chat.py` | Basic chat interaction |
| `streaming_chat.py` | Real-time streaming responses |
| `chat_session.py` | Interactive chat with history |
| `model_manager.py` | Model management operations |
| `embeddings.py` | Generate and compare embeddings |
| `model_comparison.py` | Compare different models |
| `advanced_model_handling.py` | Response format handling |
| `efficient_response_processing.py` | Optimized response processing |
| `creative_integrations.py` | Real-world integration patterns |
| `experimentation_playground.py` | Interactive experimentation |

```bash
python examples/simple_chat.py
```


## Starter Templates

Pre-built application templates in `templates/`:

```bash
python templates/chatbot/simple_chatbot.py       # Complete chatbot
python templates/rag_system/simple_rag.py         # RAG question-answering
python templates/text_analyzer/text_analyzer.py   # Text analysis
python templates/code_assistant/code_assistant.py # Coding assistant
```


## Testing

Run the full test suite (90 tests):

```bash
pip install pytest pytest-cov
python -m pytest tests/ -v
```

With coverage:

```bash
python -m pytest tests/ --cov=otk --cov-report=term-missing
```

**Test structure:**

| File | Coverage |
|------|----------|
| `test_client.py` | OllamaClient retry, metadata, batch embeddings |
| `test_pipeline.py` | DAG construction, execution order, parallel branches |
| `test_rag.py` | BM25 scoring, dense indexing, RRF, chunking |
| `test_evaluation.py` | LLM judge scoring, statistical analysis, reports |
| `test_router.py` | Task classification, model selection, fallback |
| `test_structured.py` | Schema validation, JSON extraction, type coercion |
| `test_profiler.py` | Metric collection, SQLite persistence |

All tests use `mock_ollama.py` to run without a live Ollama instance.


## Project Structure

```
open-otk/
├── otk/                        # Core Python package
│   ├── __init__.py             # Public API exports (v2.0.0)
│   ├── client.py               # OllamaClient with retry and metadata
│   ├── chat.py                 # ChatSession with token-budget trimming
│   ├── models.py               # ModelManager
│   ├── response_handlers.py    # Auto response processing for thinking models
│   ├── customization.py        # ModelBuilder, hooks, presets
│   ├── experimentation.py      # Model comparison and benchmarking
│   ├── utils.py                # Token estimation, chunking, formatting
│   ├── pipeline.py             # DAG pipeline composition engine
│   ├── rag.py                  # Hybrid RAG (BM25 + HNSW + RRF)
│   ├── evaluation.py           # LLM-as-Judge evaluation framework
│   ├── router.py               # Task-aware model router
│   ├── structured.py           # Structured output with JSON schema
│   ├── server.py               # FastAPI REST API server
│   ├── profiler.py             # Resource profiler and telemetry
│   └── __main__.py             # python -m otk entry point
├── tests/                      # Test suite (90 tests)
│   ├── conftest.py             # Shared fixtures
│   ├── mock_ollama.py          # Mock OllamaClient for offline testing
│   ├── test_client.py
│   ├── test_pipeline.py
│   ├── test_rag.py
│   ├── test_evaluation.py
│   ├── test_router.py
│   ├── test_structured.py
│   └── test_profiler.py
├── examples/                   # Ready-to-run example scripts
├── templates/                  # Starter application templates
│   ├── chatbot/
│   ├── rag_system/
│   ├── text_analyzer/
│   └── code_assistant/
├── otk.py                      # Desktop GUI application
├── setup.py                    # Package configuration
├── requirements.txt            # Core dependencies
└── LICENSE                     # MIT License
```


## API Reference

### OllamaClient

```python
client = OllamaClient(host="http://localhost:11434")

client.generate(model, prompt, system=None, temperature=0.7)
client.generate_with_metadata(model, prompt, ...)   # returns full Ollama response dict
client.chat(model, messages, temperature=0.7)
client.chat_with_metadata(model, messages, ...)
client.stream_generate(model, prompt)                # yields chunks
client.stream_chat(model, messages)                  # yields chunks
client.embeddings(model, text)                       # returns embedding vector
client.batch_embeddings(model, texts)                # batch embedding
client.is_running()                                  # health check
```

### ChatSession

```python
session = ChatSession(
    model="gemma4",
    system_message="You are helpful",
    temperature=0.7,
    max_history=50,
    max_history_tokens=4096,    # token-budget trimming
    auto_process=True           # auto-clean thinking model responses
)

session.send("Hello")                   # returns response string
session.send_stream("Tell me more")     # yields chunks
session.get_last_thinking()             # reasoning from thinking models
session.fork()                          # branch conversation
session.clear_history()
session.export_history("chat.json")
session.load_history("chat.json")
```

### ModelManager

```python
manager = ModelManager()

manager.list_models()
manager.pull_model("gemma4", stream=True)
manager.delete_model("old-model")
manager.model_exists("gemma4")
manager.show_model_info("gemma4")
manager.recommend_models()
```

### Response Processing

```python
from otk import AutoModelHandler, clean_thinking_tags, ModelBuilder, HookType

handler = AutoModelHandler()
processed = handler.process_response(raw_text, "deepseek-r1")

clean_text, thinking = clean_thinking_tags(response)

model = (ModelBuilder("gemma4")
         .with_preset("creative")
         .with_temperature(0.85)
         .with_hook(HookType.POST_PROCESS, my_logger)
         .build())
```


## Troubleshooting

**`otk` command not recognized:**
```bash
python -m otk       # always works without PATH setup
```

**Ollama not running:**
```bash
# Windows: Start the Ollama application
# Linux/Mac: ollama serve
```

**Model not found:**
```bash
ollama pull gemma4
ollama list          # see installed models
```

**Import errors:**
```bash
pip install open-otk
# or from source:
pip install -r requirements.txt
```


## License

MIT License — see [LICENSE](LICENSE) for details.

## Author

**Md. Abid Hasan Rafi**

- GitHub: [@abidhasanrafi](https://github.com/abidhasanrafi)
- Email: [ahr16.abidhasanrafi@gmail.com](mailto:ahr16.abidhasanrafi@gmail.com)
- Documentations: [OTK Docs](https://abidhasanrafi.github.io/otk)

## Links

- [Project Repository](https://github.com/abidhasanrafi/open-otk)
- [Report Issues](https://github.com/abidhasanrafi/open-otk/issues)
- [Ollama](https://ollama.com/)
