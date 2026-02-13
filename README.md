# Open OTK (Open Ollama Toolkit)

![Open OTK Cover](https://raw.githubusercontent.com/abidhasanrafi/open-otk/main/otk.jpg)

A professional Python toolkit for building AI applications with Ollama.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Documentation](https://img.shields.io/badge/docs-aiextension.github.io-blue)](https://aiextension.github.io/otk)

## Features

- Visual GUI for model browsing and template generation
- Comprehensive API for chat, streaming, and embeddings
- Automatic response processing for thinking models (DeepSeek-R1, Qwen)
- Model management and comparison tools
- Production-ready with proper error handling
- Works with all Ollama models

---

## Installation

### Prerequisites

1. Install [Ollama](https://ollama.ai)
2. Install a model: `ollama pull llama2`
3. Ensure Ollama is running

### Install Open OTK

**From PyPI (Recommended):**

```bash
# Install the package
pip install open-otk

# Launch from anywhere
otk
```

**From Source (For Development):**

```bash
# 1. Clone the repository
git clone https://github.com/aiextension/open-otk.git
cd open-otk

# 2. Install in editable mode
pip install -e ".[scraper]"

# 3. Launch from anywhere
otk
```

### Launch GUI

```bash
otk
```

Or run directly:
```bash
python otk.py
```

## Quick Start

### Basic Usage

```python
from otk import OllamaClient

client = OllamaClient()
response = client.generate("llama2", "Tell me a joke")
print(response)
```

### Chat Session

```python
from otk import ChatSession

session = ChatSession("llama2", system_message="You are a helpful assistant")
response = session.send("Hello!")
print(response)
```

### Streaming Responses

```python
from otk import OllamaClient

client = OllamaClient()
for chunk in client.stream_generate("llama2", "Write a story"):
    print(chunk, end='', flush=True)
```

### Model Management

```python
from otk import ModelManager

manager = ModelManager()

# List models
models = manager.list_models()
for model in models:
    print(f"{model['name']} - {model['size']}")

# Pull a model
manager.pull_model("mistral")

# Check if model exists
if manager.model_exists("llama2"):
    print("Model is ready!")
```

### Automatic Response Processing
```python
from otk import ChatSession

session = ChatSession("deepseek-r1:8b", auto_process=True)
response = session.send("Solve 234 + 567")
print(response)  # Clean answer

# Access reasoning
thinking = session.get_last_thinking()
```
```python
from otk import clean_thinking_tags, ModelResponseHandler, ModelType

clean_text, thinking = clean_thinking_tags(raw_response)

handler = ModelResponseHandler(ModelType.THINKING)
processed = handler.process(raw_response)
```

### Customization

```python
from otk import ModelBuilder, HookType

model = (ModelBuilder("llama2")
         .with_preset("creative")
         .with_temperature(0.85)
         .with_hook(HookType.POST_PROCESS, my_logger)
         .build())
```

### Experimentation

```python
from otk import ModelExperiment

experiment = ModelExperiment()
result = experiment.compare_models(
    models=["llama2", "mistral"],
    prompt="Explain quantum computing"
)
experiment.print_comparison(result)
```

## Examples

The `examples/` directory contains ready-to-run examples:

| Example | Description |
|---------|-------------|
| [`simple_chat.py`](examples/simple_chat.py) | Basic chat with models |
| [`streaming_chat.py`](examples/streaming_chat.py) | Real-time streaming responses |
| [`chat_session.py`](examples/chat_session.py) | Interactive chat with history |
| [`model_manager.py`](examples/model_manager.py) | Manage models interactively |
| [`embeddings.py`](examples/embeddings.py) | Generate and compare embeddings |
| [`model_comparison.py`](examples/model_comparison.py) | Compare different models |
| [`advanced_model_handling.py`](examples/advanced_model_handling.py) | Different model format handling |
| [`efficient_response_processing.py`](examples/efficient_response_processing.py) | Efficient response processing |
| [`creative_integrations.py`](examples/creative_integrations.py) | **Real-world integration patterns** |
| [`experimentation_playground.py`](examples/experimentation_playground.py) | **Interactive experimentation tool** |

Run any example:
```bash
python examples/simple_chat.py
```

## Generate Your Starter Template (Interactive)

**NEW! Create custom templates with a beautiful interactive wizard:**

```bash
python create_starter.py
```

### What You Get:

1. **Pick Your Model** - Select from installed models or install one interactively
2. **Choose Template Type:**
   - **Simple Chat** - Basic conversational interface
   - **Custom Model** - Hooks, callbacks, preprocessing
   - **Streaming Chat** - Real-time responses
   - **Experimentation** - Compare and test settings
   - **Integration** - Template for integrating into your app
   - **Tkinter GUI** - Desktop app with custom UI (no dependencies!)
   - **Tkinter Advanced** - Multi-tab desktop app with styling

3. **Name Your File** - Get ready-to-run code!

### GUI Templates Preview:

**Tkinter Desktop GUI:**
```python
# Auto-generated code with:
# - Beautiful custom styling
# - Real-time chat interface
# - Threaded operations
# - Native desktop app
# - NO extra dependencies!
```

**Run with:**
```bash
python your_app.py
# Window opens immediately!
```

**Tkinter Advanced:**
```python
# Auto-generated code with:
# - Multiple tabs (Chat, Generate, Settings)
# - Professional dark theme
# - Parameter controls
# - Content generation tools
# - Production-ready
```

**Want web/API?** Use the Integration template and add Flask/FastAPI/whatever you prefer!

### No Models Installed?

No problem! The wizard will:
1. Detect you have no models
2. Show you recommended models with sizes
3. Install the model for you interactively
4. Generate your template ready to use!

## Starter Templates

Ready-to-use templates for common applications:

### 1. Chatbot
```bash
cd templates/chatbot
python simple_chatbot.py
```
A complete chatbot with conversation history and commands.

### 2. RAG System
```bash
cd templates/rag_system
python simple_rag.py
```
Retrieval Augmented Generation for question-answering with custom knowledge.

### 3. Text Analyzer
```bash
cd templates/text_analyzer
python text_analyzer.py
```
Analyze text for sentiment, keywords, entities, and more.

### 4. Code Assistant
```bash
cd templates/code_assistant
python code_assistant.py
```
AI-powered coding assistant for generation, debugging, and review.

## API Reference

### OllamaClient

Main client for interacting with Ollama:

```python
client = OllamaClient(host="http://localhost:11434")

# Generate text
response = client.generate(model, prompt, system=None, temperature=0.7)

# Stream generation
for chunk in client.stream_generate(model, prompt):
    print(chunk)

# Chat completion
response = client.chat(model, messages, temperature=0.7)

# Stream chat
for chunk in client.stream_chat(model, messages):
    print(chunk)

# Generate embeddings
embedding = client.embeddings(model, text)

# Check if running
is_running = client.is_running()
```

### ChatSession

Maintain conversation context with automatic response processing:

```python
session = ChatSession(
    model="llama2",
    system_message="You are helpful",
    temperature=0.7,
    max_history=50,
    auto_process=True  # Automatically handle different model formats
)

# Send message (automatically cleaned!)
response = session.send("Hello")

# Stream message
for chunk in session.send_stream("Tell me more"):
    print(chunk)

# Access thinking/reasoning (if available)
thinking = session.get_last_thinking()
metadata = session.get_last_metadata()

# Clear history
session.clear_history()

# Get history
history = session.get_history()

# Export/import
session.export_history("chat.json")
session.load_history("chat.json")
```

### Response Handlers

Handle different model formats automatically:

```python
from otk import (
    AutoModelHandler,
    ModelResponseHandler,
    ModelType,
    clean_thinking_tags
)

# Automatic handler (detects model type)
auto_handler = AutoModelHandler()
processed = auto_handler.process_response(raw_text, "deepseek-r1")

# Manual handler for specific type
handler = ModelResponseHandler(ModelType.THINKING)
processed = handler.process(raw_text)

# Quick utility functions
clean_text, thinking = clean_thinking_tags(response)

# Custom patterns
custom_handler = ModelResponseHandler(
    ModelType.CUSTOM,
    custom_patterns={'tag': r'<tag>(.*?)</tag>'}
)
```
session.load_history("chat.json")
```

### ModelManager

Manage Ollama models:

```python
manager = ModelManager()

# List models
models = manager.list_models()

# Pull model
manager.pull_model("llama2", stream=True)

# Delete model
manager.delete_model("old-model")

# Check existence
exists = manager.model_exists("llama2")

# Get model info
info = manager.show_model_info("llama2")

# Get recommendations
recommendations = manager.recommend_models()
```

## Utility Functions

```python
from otk import (
    format_response,
    estimate_tokens,
    chunk_text,
    create_prompt_template,
    extract_code_blocks,
    clean_response
)

# Format for readability
formatted = format_response(long_text, max_width=80)

# Estimate tokens
tokens = estimate_tokens(text)

# Chunk text
chunks = chunk_text(text, chunk_size=1000, overlap=100)

# Use templates
prompt = create_prompt_template(
    "Translate {text} to {language}",
    {"text": "Hello", "language": "Spanish"}
)

# Extract code
code_blocks = extract_code_blocks(markdown_text)
```

## Recommended Models

### General Chat
- `llama2` - Meta's general-purpose model
- `mistral` - Fast and capable
- `phi` - Small but powerful

### Coding
- `codellama` - Code generation and explanation
- `deepseek-coder` - Excellent for code
- `starcoder2` - Strong coding capabilities

### Embeddings
- `nomic-embed-text` - Text embeddings
- `all-minilm` - Lightweight embeddings

Pull models with:
```bash
ollama pull llama2
ollama pull codellama
ollama pull nomic-embed-text
```

## Examples

See [`examples/`](examples/) directory for working code samples.

## Templates

Ready-to-use application templates in [`templates/`](templates/).

## Testing

```bash
python test_quick.py
```

### Test Features

```python
from otk import clean_thinking_tags, ModelBuilder

clean, thinking = clean_thinking_tags("<think>x</think>answer")

model = ModelBuilder("llama2").with_temperature(0.8).build()
```

## Troubleshooting
```bash
# Solution: Make sure Ollama is running
# Windows: Start Ollama app
# Linux/Mac: ollama serve
```

**Issue: Model not found**
```bash
# Solution: Pull the model
ollama pull llama2

# Or list available models
ollama list
```

**Issue: Import errors**
```bash
# Solution: Install dependencies
pip install ollama

# Or install from requirements
pip install -r requirements.txt
```

**Full Testing Guide:** [TESTING_GUIDE.md](TESTING_GUIDE.md)

## Contributing

Contributions are welcome! Feel free to:
- Report bugs
- Suggest features
- Submit pull requests
- Improve documentation

## License

MIT License - feel free to use in your projects!

## Acknowledgments

- Built on top of [Ollama](https://ollama.ai)
- Uses the official [ollama-python](https://github.com/ollama/ollama-python) library

## Documentation

- [Getting Started Guide](docs/guides/GETTING_STARTED.md)
- [GUI Documentation](docs/gui/GUI_APP_README.md)
- [API Reference](docs/reference/QUICK_REFERENCE.md)

## Contributing

Contributions welcome! Open an issue or submit a pull request.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Author

**Md. Abid Hasan Rafi**

- Email: [ahr16.abidhasanrafi@gmail.com](mailto:ahr16.abidhasanrafi@gmail.com)
- GitHub: [@abidhasanrafi](https://github.com/abidhasanrafi)
- Portfolio: [abidhasanrafi.github.io](https://abidhasanrafi.github.io)
- Organization: [AI Extension](https://aiextension.org)

## Links

- [OTK Website](https://aiextension.github.io/otk)
- [Project Repository](https://github.com/aiextension/open-otk)
- [Report Issues](https://github.com/aiextension/open-otk/issues)
- [Ollama Documentation](https://github.com/ollama/ollama)
