# Working with Different Model Formats

## Overview

Different Ollama models have different response structures. Some models (like DeepSeek-R1) include reasoning steps in `<think>` tags, while others may have different formatting. The Ollama Toolkit automatically handles these differences for you!

## Problem Statement

When working with different models, you often encounter:

```python
# DeepSeek-R1 response
"<think>Let me break this down step by step...</think>The answer is 42"

# Standard model response
"The answer is 42"

# Code model response
"Here's the solution:\n```python\nprint('42')\n```"
```

**Without this library**, you'd need to write custom regex patterns for each model type:

```python
import re

def clean_deepseek(text):
    # Remove thinking tags
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    return text.strip()

def clean_qwen(text):
    # Different pattern for Qwen
    text = re.sub(r'<reasoning>.*?</reasoning>', '', text, flags=re.DOTALL)
    return text.strip()

# ... and so on for each model
```

## Solution: Automatic Response Handling

The Ollama Toolkit provides **automatic response handling**:

```python
from otk import ChatSession

# Just use it - the library handles everything!
session = ChatSession("deepseek-r1:8b", auto_process=True)
response = session.send("What is 5 + 3?")

# Response is automatically cleaned!
print(response)  # "8" (no thinking tags!)
```

## How It Works

### 1. Automatic Model Detection

The library automatically detects model types:

```python
from otk import AutoModelHandler

handler = AutoModelHandler()

# Automatically detects DeepSeek as a "thinking" model
result = handler.process_response(raw_text, "deepseek-r1:8b")
```

**Supported Model Types:**

| Model Pattern | Type | Description |
|--------------|------|-------------|
| `deepseek-r1` | THINKING | Models with reasoning steps |
| `qwen` | THINKING | Qwen models with thinking |
| `codellama` | CODE | Code-focused models |
| `starcoder` | CODE | Code generation models |
| `*` (default) | STANDARD | Standard chat models |

### 2. Response Processing

Each model type has specific processing:

#### Thinking Models
- Extracts content between `<think>`, `<reasoning>`, `<thought>` tags
- Provides access to reasoning steps
- Cleans the main response

```python
session = ChatSession("deepseek-r1:8b", auto_process=True)
response = session.send("Solve 15 * 24")

# Get the clean answer
print(response)  # "360"

# Access the thinking process
thinking = session.get_last_thinking()
for step in thinking:
    print(f"Reasoning: {step}")
```

#### Code Models
- Extracts code blocks
- Identifies programming languages
- Maintains both code and explanation

```python
from otk import ModelResponseHandler, ModelType

handler = ModelResponseHandler(ModelType.CODE)
processed = handler.process(response)

print(processed.content)  # Clean explanation
print(processed.metadata['code_blocks'])  # Extracted code
```

#### Standard Models
- Basic cleanup (whitespace, newlines)
- No special processing needed

### 3. Manual Control

You can also process responses manually:

```python
from otk import (
    clean_thinking_tags,
    auto_clean_response,
    ModelResponseHandler,
    ModelType
)

# Quick function for thinking tags
clean_text, thinking = clean_thinking_tags(raw_response)

# Auto-detect and clean
clean_text = auto_clean_response(raw_response, "deepseek-r1")

# Full control with handler
handler = ModelResponseHandler(ModelType.THINKING)
processed = handler.process(raw_response)

print(processed.content)    # Cleaned text
print(processed.thinking)   # Reasoning steps
print(processed.metadata)   # Additional info
print(processed.raw_content) # Original response
```

## Practical Examples

### Example 1: Simple Chat with Auto-Processing

```python
from otk import ChatSession

# Works with ANY model - auto-processing enabled by default
session = ChatSession("deepseek-r1:8b")

response = session.send("What is Python?")
print(response)  # Clean answer, no thinking tags!
```

### Example 2: Accessing Reasoning Steps

```python
from otk import ChatSession

session = ChatSession("deepseek-r1:8b", auto_process=True)
response = session.send("Explain quantum computing in simple terms")

print(f"Answer: {response}\n")

# Show the model's thinking process
thinking = session.get_last_thinking()
if thinking:
    print("Model's reasoning:")
    for i, step in enumerate(thinking, 1):
        print(f"{i}. {step}\n")
```

### Example 3: Comparing Models

```python
from otk import ChatSession
import time

models = ["llama2", "deepseek-r1:8b", "mistral"]
question = "What is 25 * 16?"

for model in models:
    print(f"\nTesting {model}:")
    
    session = ChatSession(model, auto_process=True)
    start = time.time()
    response = session.send(question)
    elapsed = time.time() - start
    
    print(f"  Answer: {response}")
    print(f"  Time: {elapsed:.2f}s")
    
    # Check if reasoning was used
    thinking = session.get_last_thinking()
    if thinking:
        print(f"  Reasoning: {len(thinking)} step(s)")
```

### Example 4: Custom Response Format

```python
from otk import ModelResponseHandler, ModelType

# Define custom patterns to extract
custom_patterns = {
    'confidence': r'Confidence: (\d+)%',
    'sources': r'Source: (.*?)(?:\n|$)'
}

handler = ModelResponseHandler(ModelType.CUSTOM, custom_patterns=custom_patterns)

raw = """Confidence: 95%
Source: Wikipedia
Source: Research Paper

Python is a high-level programming language."""

processed = handler.process(raw)

print(f"Content: {processed.content}")
print(f"Confidence: {processed.metadata['extracted']['confidence']}")
print(f"Sources: {processed.metadata['extracted']['sources']}")
```

### Example 5: Disable Auto-Processing

```python
from otk import ChatSession

# Get raw responses without processing
session = ChatSession("deepseek-r1:8b", auto_process=False)
raw_response = session.send("Hello")

# raw_response will contain thinking tags if model includes them
print(raw_response)
```

## Advanced Usage

### Registering Custom Model Types

```python
from otk import AutoModelHandler, ModelType

handler = AutoModelHandler()

# Register your custom model pattern
handler.register_model_type("my-custom-model", ModelType.THINKING)

# Now it will automatically use thinking model processing
result = handler.process_response(text, "my-custom-model:latest")
```

### Creating Custom Handlers

```python
from otk import ModelResponseHandler, ModelType

# For models with special XML-style tags
custom_patterns = {
    'summary': r'<summary>(.*?)</summary>',
    'details': r'<details>(.*?)</details>'
}

handler = ModelResponseHandler(ModelType.CUSTOM, custom_patterns=custom_patterns)
processed = handler.process(response)

# Access extracted data
summary = processed.metadata['extracted']['summary']
details = processed.metadata['extracted']['details']
```

### Batch Processing

```python
from otk import AutoModelHandler

handler = AutoModelHandler()

responses = [
    ("deepseek-r1:8b", "<think>...</think>Answer"),
    ("llama2", "Standard answer"),
    ("codellama", "```python\ncode\n```")
]

for model, response in responses:
    processed = handler.process_response(response, model)
    print(f"{model}: {processed.content}")
```

## Best Practices

### 1. Use Auto-Processing by Default

```python
# CORRECT - automatic handling
session = ChatSession("deepseek-r1:8b", auto_process=True)

# Only disable if you need raw responses
session = ChatSession("deepseek-r1:8b", auto_process=False)
```

### 2. Check for Thinking Content

```python
response = session.send("Complex question")

# Always check if thinking is available
thinking = session.get_last_thinking()
if thinking:
    # Use the reasoning steps
    for step in thinking:
        print(step)
```

### 3. Handle Multiple Models Gracefully

```python
from otk import ChatSession

def chat_with_model(model_name, question):
    try:
        session = ChatSession(model_name, auto_process=True)
        response = session.send(question)
        return response
    except Exception as e:
        return f"Error with {model_name}: {e}"
```

### 4. Use Metadata for Debugging

```python
response = session.send("Question")
metadata = session.get_last_metadata()

print(f"Model type: {metadata.get('model_type')}")
print(f"Processing info: {metadata}")
```

## Migration Guide

### From Manual Cleaning

**Before:**
```python
import re
import ollama

def clean_response(text):
    thinking = re.findall(r'<think>(.*?)</think>', text, flags=re.DOTALL)
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    text = re.sub(r'^<[^>]+>\s*', '', text)
    return text.strip(), thinking

response = ollama.chat(model="deepseek-r1:8b", messages=[...])
clean_text, thinking = clean_response(response.message.content)
```

**After:**
```python
from otk import ChatSession

session = ChatSession("deepseek-r1:8b", auto_process=True)
response = session.send("Question")  # Automatically cleaned!
thinking = session.get_last_thinking()  # Easy access to reasoning
```

### Adding to Existing Code

```python
# Your existing code
import ollama

# Add the library
from otk import auto_clean_response

response = ollama.chat(model="deepseek-r1:8b", messages=[...])
raw_text = response.message.content

# Clean it automatically
clean_text = auto_clean_response(raw_text, "deepseek-r1:8b")
```

## Troubleshooting

### Response Still Has Tags

**Problem:** Response contains tags even with auto_process=True

**Solution:** Make sure you're using the correct model name pattern:

```python
# CORRECT
session = ChatSession("deepseek-r1:8b", auto_process=True)

# WRONG - might not detect properly
session = ChatSession("deepseek-r1", auto_process=False)
```

### Custom Model Not Recognized

**Problem:** Your custom model isn't being detected

**Solution:** Register it manually:

```python
from otk import AutoModelHandler, ModelType

handler = AutoModelHandler()
handler.register_model_type("mycustommodel", ModelType.THINKING)

# Now use it in your session
session = ChatSession("mycustommodel:latest", auto_process=True)
```

### Want Raw Response Sometimes

**Problem:** Need both raw and processed response

**Solution:** Disable auto_process and process manually:

```python
session = ChatSession(model, auto_process=False)
raw_response = session.send("Question")

# Process manually when needed
from otk import auto_clean_response
clean = auto_clean_response(raw_response, model)
```

## Summary

The Ollama Toolkit makes working with different model formats effortless:

- **Automatic detection** - Works with any model  
- **Clean responses** - No manual regex needed  
- **Access reasoning** - Get thinking steps when available  
- **Extensible** - Add custom patterns easily  
- **Simple API** - Just use ChatSession!  

Start using it today and never worry about model-specific formatting again!
