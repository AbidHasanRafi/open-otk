# Getting Started with Ollama Toolkit

This guide will help you get started with the Ollama Toolkit.

## Step 1: Install Ollama

1. Download Ollama from [ollama.ai](https://ollama.ai)
2. Install it on your system
3. Verify installation by running:
   ```bash
   ollama --version
   ```

## Step 2: Pull a Model

Pull at least one model to get started:

```bash
# General purpose model
ollama pull llama2

# For coding tasks
ollama pull codellama

# For embeddings
ollama pull nomic-embed-text
```

## Step 3: Install the Toolkit

Navigate to the project directory and install:

```bash
cd f:\ollama_project
pip install -e .
```

Or just install dependencies:

```bash
pip install -r requirements.txt
```

## Step 4: Try an Example

Run a simple example:

```bash
python examples/simple_chat.py
```

## Step 5: Explore Templates

Try one of the starter templates:

```bash
# Chatbot
cd templates/chatbot
python simple_chatbot.py

# RAG System
cd templates/rag_system
python simple_rag.py

# Text Analyzer
cd templates/text_analyzer
python text_analyzer.py

# Code Assistant
cd templates/code_assistant
python code_assistant.py
```

## Step 6: Build Your Own

Use the library in your own code:

```python
from otk import OllamaClient, ChatSession

# Simple generation
client = OllamaClient()
response = client.generate("llama2", "Hello!")
print(response)

# Chat session with automatic response handling
session = ChatSession("llama2", auto_process=True)
response = session.send("Tell me about Python")
print(response)

# Works automatically with thinking models too!
session = ChatSession("deepseek-r1:8b", auto_process=True)
response = session.send("What is 15 * 24?")
print(response)  # Clean answer, no thinking tags!

# Access reasoning if available
thinking = session.get_last_thinking()
if thinking:
    print(f"Model used {len(thinking)} reasoning steps")
```

## Step 7: Try Advanced Features

### Automatic Response Handling

The library automatically handles different model formats:

```bash
# See how different models are handled
python examples/advanced_model_handling.py

# See efficient processing
python examples/efficient_response_processing.py
```

### Quick Tips for Different Models

```python
from otk import ChatSession

# ✅ Thinking models (DeepSeek-R1, Qwen) - auto-cleans reasoning tags
session = ChatSession("deepseek-r1:8b", auto_process=True)

# ✅ Standard models (Llama, Mistral) - works normally
session = ChatSession("llama2", auto_process=True)

# ✅ Code models (CodeLlama) - handles code blocks
session = ChatSession("codellama", auto_process=True)

# All use the same API - the library handles the differences!
```

## Common Issues

### Ollama Not Running

If you get connection errors:
1. Make sure Ollama is running
2. Check it's accessible at `http://localhost:11434`
3. Try: `ollama serve`

### Model Not Found

If a model isn't found:
1. Pull it first: `ollama pull <model-name>`
2. List available models: `ollama list`

### Import Errors

If you get import errors:
1. Make sure you're in the right directory
2. Install dependencies: `pip install -r requirements.txt`
3. Install the package: `pip install -e .`

## Next Steps

- Read the [README.md](../README.md) for full API documentation
- Read [RESPONSE_HANDLING.md](../docs/RESPONSE_HANDLING.md) for working with different model formats
- Explore the [examples/](../examples/) directory
- Try the [templates/](../templates/) for common use cases
- Check out [Ollama's documentation](https://github.com/ollama/ollama/blob/main/docs/README.md)

## Tips

1. **Start Small**: Begin with smaller models like `phi` or `tinyllama`
2. **Use Streaming**: For better UX, use streaming responses
3. **Manage Context**: Use ChatSession for conversations
4. **Temperature**: Lower (0.1-0.3) for factual, higher (0.7-0.9) for creative
5. **System Messages**: Use them to set the AI's behavior
6. **Auto-Processing**: Keep `auto_process=True` (default) for automatic response cleaning
7. **Model Types**: The library automatically handles different model formats - just use the same API!
8. **Reasoning Models**: Use `get_last_thinking()` to access model's reasoning steps

Happy coding! 🚀
