# Ollama Toolkit - Quick Reference

## Installation

```bash
pip install -e .
# or
pip install -r requirements.txt
```

## Basic Usage

### Simple Generation
```python
from otk import OllamaClient

client = OllamaClient()
response = client.generate("llama2", "Your prompt here")
```

### Chat Session
```python
from otk import ChatSession

session = ChatSession("llama2", auto_process=True)
response = session.send("Hello!")
```

### Streaming
```python
for chunk in client.stream_generate("llama2", "Write a story"):
    print(chunk, end='', flush=True)
```

## Response Handling

### Automatic (Recommended)
```python
# Works with ANY model - auto-cleans responses
session = ChatSession("deepseek-r1:8b", auto_process=True)
response = session.send("Question")  # Clean answer!
```

### Access Thinking
```python
response = session.send("Complex question")
thinking = session.get_last_thinking()
if thinking:
    for step in thinking:
        print(step)
```

### Manual Cleaning
```python
from otk import clean_thinking_tags, auto_clean_response

# Quick clean
clean, thinking = clean_thinking_tags(raw_response)

# Auto-detect model type
clean = auto_clean_response(raw_response, "deepseek-r1")
```

### Custom Handler
```python
from otk import ModelResponseHandler, ModelType

handler = ModelResponseHandler(
    ModelType.CUSTOM,
    custom_patterns={'tag': r'<tag>(.*?)</tag>'}
)
processed = handler.process(raw_text)
```

## Model Management

### List Models
```python
from otk import ModelManager

manager = ModelManager()
models = manager.list_models()
for model in models:
    print(f"{model['name']} - {model['size']}")
```

### Pull/Delete Models
```python
manager.pull_model("mistral", stream=True)
manager.delete_model("old-model")
exists = manager.model_exists("llama2")
```

## Utilities

### Prompt Templates
```python
from otk import create_prompt_template

prompt = create_prompt_template(
    "Translate {text} to {language}",
    {"text": "Hello", "language": "Spanish"}
)
```

### Token Estimation
```python
from otk import estimate_tokens, chunk_text

tokens = estimate_tokens(text)
chunks = chunk_text(text, chunk_size=1000, overlap=100)
```

### Extract Code
```python
from otk import extract_code_blocks

code_blocks = extract_code_blocks(markdown_text)
for block in code_blocks:
    print(f"Language: {block['language']}")
    print(f"Code: {block['code']}")
```

## Chat Session Advanced

### With History Management
```python
session = ChatSession(
    model="llama2",
    system_message="You are helpful",
    temperature=0.7,
    max_history=50,
    auto_process=True
)

response = session.send("Question")
history = session.get_history()
session.clear_history(keep_system=True)
```

### Export/Import
```python
session.export_history("chat.json")
session.load_history("chat.json")
```

### System Message
```python
session.set_system_message("You are a Python expert")
```

## Model Types

The library auto-detects these model types:

| Model Pattern | Type | Features |
|--------------|------|----------|
| `deepseek-r1*` | THINKING | Auto-cleans `<think>` tags |
| `qwen*` | THINKING | Handles reasoning tags |
| `codellama*` | CODE | Extracts code blocks |
| `starcoder*` | CODE | Code-focused processing |
| Others | STANDARD | Basic cleanup |

## Common Patterns

### Multi-Model Comparison
```python
models = ["llama2", "mistral", "deepseek-r1:8b"]
for model in models:
    session = ChatSession(model, auto_process=True)
    response = session.send("Question")
    thinking = session.get_last_thinking()
    print(f"{model}: {response}")
    if thinking:
        print(f"  Reasoning: {len(thinking)} steps")
```

### Temperature Experimentation
```python
temperatures = [0.3, 0.7, 1.0]
for temp in temperatures:
    session = ChatSession("llama2", temperature=temp)
    response = session.send("Write a creative story opening")
    print(f"Temp {temp}: {response}")
```

### Error Handling
```python
try:
    session = ChatSession("model-name")
    response = session.send("Question")
except Exception as e:
    print(f"Error: {e}")
    print("Make sure model is installed: ollama pull model-name")
```

### Timing Responses
```python
import time

start = time.time()
response = session.send("Question")
elapsed = time.time() - start
print(f"Response in {elapsed:.2f}s")
```

## Configuration

### Custom Host
```python
from otk import OllamaClient

client = OllamaClient(host="http://custom-host:11434")
```

### Model Parameters
```python
response = client.generate(
    model="llama2",
    prompt="Your prompt",
    temperature=0.7,
    max_tokens=500,
    options={
        'top_p': 0.9,
        'top_k': 40,
        'repeat_penalty': 1.1
    }
)
```

## Debugging

### Check Metadata
```python
response = session.send("Question")
metadata = session.get_last_metadata()
print(f"Model type: {metadata.get('model_type')}")
print(f"Details: {metadata}")
```

### Get Raw Response
```python
# Disable auto-processing to see raw output
session = ChatSession(model, auto_process=False)
raw = session.send("Question")
print(raw)  # Will show thinking tags if present
```

### Verify Processing
```python
from otk import ModelResponseHandler, ModelType

handler = ModelResponseHandler(ModelType.THINKING)
processed = handler.process(raw_text)

print(f"Raw: {processed.raw_content}")
print(f"Processed: {processed.content}")
print(f"Thinking: {processed.thinking}")
```

## Resources

- [Full Documentation](README.md)
- [Response Handling Guide](docs/RESPONSE_HANDLING.md)
- [Getting Started](GETTING_STARTED.md)
- [Examples](examples/)
- [Templates](templates/)

## Quick Tips

- Use `auto_process=True` for all models  
- Check `get_last_thinking()` for reasoning  
- Start with smaller models for testing  
- Use streaming for better UX  
- Lower temperature for facts, higher for creativity  
- System messages set AI behavior  
- Export chat history for debugging  
- The same API works for ALL models!  

## Examples Directory

| File | What it shows |
|------|---------------|
| `simple_chat.py` | Basic chat |
| `streaming_chat.py` | Streaming responses |
| `chat_session.py` | Conversation history |
| `model_manager.py` | Model management |
| `embeddings.py` | Text embeddings |
| `model_comparison.py` | Compare models |
| `advanced_model_handling.py` | Different model formats |
| `efficient_response_processing.py` | Efficient processing |

Run any example:
```bash
python examples/simple_chat.py
```

## Common Issues

**Connection Error**: Make sure Ollama is running (`ollama serve`)  
**Model Not Found**: Pull it first (`ollama pull model-name`)  
**Import Error**: Install dependencies (`pip install -r requirements.txt`)  
**Thinking Tags Still Show**: Check `auto_process=True` is set  
**Custom Model Not Detected**: Register it with `AutoModelHandler.register_model_type()`  

---

**Need more help?** Check the full [README.md](README.md) or [Response Handling Guide](docs/RESPONSE_HANDLING.md)!
