# Customization & Integration Guide

**Make Ollama work YOUR way! 🎨**

This library is designed to be a flexible toolkit for integrating Ollama models into **your own projects**. This isn't just another chat interface - it's a foundation for building AI-powered tools and applications.

## Philosophy

> "Ollama already has chat. We give you the tools to build **anything** with it."

**Key Principles:**
- ✅ Full control over model behavior
- ✅ Easy to customize and extend  
- ✅ Hook into any stage of processing
- ✅ Build tools, not just chatbots
- ✅ Experiment and find what works for YOU

---

## Table of Contents

1. [Basic Customization](#basic-customization)
2. [Hooks and Callbacks](#hooks-and-callbacks)
3. [Custom Processing](#custom-processing)
4. [Model Presets](#model-presets)
5. [Builder Pattern](#builder-pattern)
6. [Integration Examples](#integration-examples)
7. [Experimentation Tools](#experimentation-tools)
8. [Advanced Patterns](#advanced-patterns)

---

## Basic Customization

### Using Model Configurations

```python
from otk import CustomizableModel, ModelConfig

# Create custom configuration
config = ModelConfig(
    temperature=0.9,
    max_tokens=500,
    top_p=0.95,
    repeat_penalty=1.1
)

model = CustomizableModel("llama2", config=config.to_dict())
response = model.generate("Your prompt")
```

### Using Presets

```python
from otk import ModelPresets, CustomizableModel

# Pre-configured settings
creative_config = ModelPresets.creative()  # High creativity
factual_config = ModelPresets.factual()    # Low temp, focused
code_config = ModelPresets.code()          # Optimized for code

model = CustomizableModel("llama2", config=creative_config.to_dict())
```

---

## Hooks and Callbacks

Hooks let you run custom code at different stages of processing.

### Available Hook Types

```python
from otk import HookType

# HookType.PRE_PROCESS   - Before sending to model
# HookType.POST_PROCESS  - After receiving from model
# HookType.PRE_CLEAN     - Before response cleaning
# HookType.POST_CLEAN    - After response cleaning
# HookType.ERROR         - On errors
# HookType.STREAM_CHUNK  - On each streaming chunk
```

### Adding Hooks

```python
from otk import CustomizableModel, HookType, HookContext

def log_input(ctx: HookContext):
    """Log all inputs"""
    print(f"[INPUT] {ctx.input_text[:50]}...")

def log_output(ctx: HookContext):
    """Log all outputs"""
    print(f"[OUTPUT] {ctx.output_text[:50]}...")

def handle_error(ctx: HookContext):
    """Custom error handling"""
    print(f"[ERROR] {ctx.error}")

# Create model with hooks
model = CustomizableModel("llama2")
model.add_hook(HookType.PRE_PROCESS, log_input)
model.add_hook(HookType.POST_PROCESS, log_output)
model.add_hook(HookType.ERROR, handle_error)

# Now every interaction is logged!
response = model.generate("Hello")
```

### Real-World Hook Example: Content Filtering

```python
def content_filter_hook(ctx: HookContext):
    """Filter inappropriate content"""
    if ctx.output_text:
        # Your filtering logic
        inappropriate_words = ["word1", "word2"]
        for word in inappropriate_words:
            ctx.output_text = ctx.output_text.replace(word, "[FILTERED]")

model = CustomizableModel("llama2")
model.add_hook(HookType.POST_CLEAN, content_filter_hook)
```

---

## Custom Processing

Add your own pre/post processing functions.

### Pre-Processing (Modify Inputs)

```python
def enhance_prompt(text: str) -> str:
    """Add context to every prompt"""
    return f"You are an expert. {text}"

model = CustomizableModel("llama2")
model.set_pre_processor(enhance_prompt)

# Every prompt is now enhanced!
response = model.generate("Explain Python")
# Actually sends: "You are an expert. Explain Python"
```

### Post-Processing (Modify Outputs)

```python
def format_response(text: str) -> str:
    """Add formatting to responses"""
    lines = ["=" * 50, text, "=" * 50]
    return "\n".join(lines)

model = CustomizableModel("llama2")
model.set_post_processor(format_response)

# Every response is formatted!
```

### Utility Processors

```python
from ollama_toolkit.customization import (
    length_limiter,
    keyword_filter,
    add_prefix,
    add_suffix
)

model = CustomizableModel("llama2")

# Limit response length
model.set_post_processor(length_limiter(500))

# Or filter keywords
model.set_post_processor(keyword_filter(["bad", "word"]))

# Or add branding
model.set_post_processor(add_suffix("\n\n— Powered by YourApp"))
```

---

## Model Presets

Quick configurations for common use cases.

```python
from otk import ModelPresets

# Creative writing
ModelPresets.creative()      # temp: 0.9, top_p: 0.95

# Factual responses
ModelPresets.factual()       # temp: 0.2, top_p: 0.5

# Balanced
ModelPresets.balanced()      # temp: 0.7, top_p: 0.9

# Code generation
ModelPresets.code()          # temp: 0.2, optimized for code

# Conversation
ModelPresets.conversational() # temp: 0.8, natural chat

# Custom
ModelPresets.custom(temperature=0.6, max_tokens=1000, top_k=30)
```

---

## Builder Pattern

Fluent interface for easy model configuration.

```python
from otk import ModelBuilder, HookType

# Build a fully customized model
model = (ModelBuilder("llama2")
         .with_preset("creative")
         .with_temperature(0.85)
         .with_max_tokens(500)
         .with_hook(HookType.POST_PROCESS, my_hook)
         .with_post_processor(my_formatter)
         .build())

# Use it!
response = model.generate("Write a story")
```

### Real Example: Logging Model

```python
def log_hook(ctx):
    with open("model_log.txt", "a") as f:
        f.write(f"{ctx.model}: {ctx.output_text}\n")

logging_model = (ModelBuilder("llama2")
                .with_preset("balanced")
                .with_hook(HookType.POST_PROCESS, log_hook)
                .build())
```

---

## Integration Examples

### 1. Content Generator

```python
from otk import CustomizableModel

class BlogGenerator:
    def __init__(self, model="llama2"):
        self.model = CustomizableModel(model)
        self.model.set_post_processor(self._format)
    
    def _format(self, text):
        return f"# Blog Post\n\n{text}\n\n---\nAuto-generated"
    
    def generate(self, topic):
        prompt = f"Write a blog post about: {topic}"
        return self.model.generate(prompt, temperature=0.8)

generator = BlogGenerator()
post = generator.generate("AI in 2025")
```

### 2. Data Processor

```python
from otk import OllamaClient

class SmartCategorizer:
    def __init__(self):
        self.client = OllamaClient()
    
    def categorize(self, text, categories):
        prompt = f"""Categorize: {text}
Categories: {', '.join(categories)}
Respond with ONE category only."""
        
        return self.client.generate(
            "llama2",
            prompt,
            temperature=0.2  # Low temp for consistency
        ).strip()

categorizer = SmartCategorizer()
category = categorizer.categorize(
    "This product is amazing!",
    ["positive", "negative", "neutral"]
)
```

### 3. Code Assistant

```python
from otk import ModelBuilder, ModelPresets

class CodeHelper:
    def __init__(self):
        self.model = (ModelBuilder("codellama")
                     .with_preset("code")
                     .build())
    
    def explain(self, code):
        return self.model.generate(f"Explain this code:\n{code}")
    
    def debug(self, code, error):
        return self.model.generate(
            f"Debug this error:\nCode: {code}\nError: {error}"
        )
    
    def improve(self, code):
        return self.model.generate(f"Improve this code:\n{code}")

helper = CodeHelper()
```

### 4. Multi-Model Pipeline

```python
from otk import OllamaClient

class ContentPipeline:
    def __init__(self):
        self.client = OllamaClient()
    
    def generate_and_improve(self, topic):
        # Step 1: Generate
        draft = self.client.generate(
            "llama2",
            f"Write about: {topic}",
            temperature=0.9
        )
        
        # Step 2: Critique
        critique = self.client.generate(
            "mistral",
            f"Critique this: {draft}",
            temperature=0.5
        )
        
        # Step 3: Improve
        final = self.client.generate(
            "llama2",
            f"Improve based on: {critique}\n\nOriginal: {draft}",
            temperature=0.7
        )
        
        return {'draft': draft, 'critique': critique, 'final': final}
```

---

## Experimentation Tools

### Compare Models

```python
from otk import ModelExperiment

experiment = ModelExperiment()

# Compare multiple models
result = experiment.compare_models(
    models=["llama2", "mistral", "phi"],
    prompt="Explain quantum computing",
    parallel=True  # Run in parallel for speed
)

experiment.print_comparison(result)
```

### Benchmark Performance

```python
stats = experiment.benchmark(
    model="llama2",
    prompt="What is Python?",
    iterations=10
)

experiment.print_benchmark(stats)
# Shows: avg time, min/max, std dev, tokens/sec
```

### Playground Experimentation

```python
from otk import ModelPlayground

playground = ModelPlayground()

# Try different temperatures
playground.try_temperatures(
    model="llama2",
    prompt="Write a story",
    temperatures=[0.1, 0.5, 0.9, 1.2]
)

# Try prompt variations
playground.try_prompt_variations(
    model="llama2",
    base_prompt="Python",
    variations=["What is", "Explain", "Teach me about"]
)

# Try system messages
playground.try_system_messages(
    model="llama2",
    prompt="Hello",
    system_messages=[
        "You are friendly",
        "You are professional",
        "You are a pirate"
    ]
)
```

### A/B Testing

```python
from otk import ABTest

ab = ABTest()

results = ab.test(
    model_a="llama2",
    model_b="mistral",
    prompts=[
        "Explain AI",
        "Write a poem",
        "Debug this code"
    ]
)

# See which model wins!
```

---

## Advanced Patterns

### 1. Adaptive System

```python
class AdaptiveModel:
    def __init__(self, model):
        self.model = CustomizableModel(model)
        self.temperature = 0.7
    
    def respond(self, prompt):
        return self.model.generate(prompt, temperature=self.temperature)
    
    def adjust(self, feedback):
        if "more creative" in feedback:
            self.temperature = min(1.5, self.temperature + 0.1)
        elif "more focused" in feedback:
            self.temperature = max(0.1, self.temperature - 0.1)
```

### 2. Caching System

```python
class CachedModel:
    def __init__(self, model):
        self.model = CustomizableModel(model)
        self.cache = {}
    
    def generate(self, prompt):
        if prompt in self.cache:
            return self.cache[prompt]
        
        response = self.model.generate(prompt)
        self.cache[prompt] = response
        return response
```

### 3. Rate-Limited Model

```python
import time

class RateLimitedModel:
    def __init__(self, model, max_per_minute=10):
        self.model = CustomizableModel(model)
        self.max_per_minute = max_per_minute
        self.requests = []
    
    def generate(self, prompt):
        # Clean old requests
        now = time.time()
        self.requests = [t for t in self.requests if now - t < 60]
        
        # Check limit
        if len(self.requests) >= self.max_per_minute:
            wait = 60 - (now - self.requests[0])
            time.sleep(wait)
        
        # Make request
        self.requests.append(now)
        return self.model.generate(prompt)
```

### 4. Ensemble Model

```python
class EnsembleModel:
    def __init__(self, models):
        self.client = OllamaClient()
        self.models = models
    
    def generate(self, prompt):
        """Get responses from all models"""
        responses = []
        for model in self.models:
            response = self.client.generate(model, prompt)
            responses.append(response)
        return responses
    
    def vote(self, prompt):
        """Simple voting mechanism"""
        responses = self.generate(prompt)
        # Your voting logic here
        return max(set(responses), key=responses.count)
```

---

## Best Practices

### ✅ DO

- Use presets for common scenarios
- Add hooks for logging and monitoring
- Experiment to find optimal settings
- Chain models for complex tasks
- Customize for your specific use case
- Test different models for your task

### ❌ DON'T

- Hardcode everything
- Ignore error handling
- Use same settings for all tasks
- Skip experimentation
- Assume one model fits all
- Forget to handle edge cases

---

## Quick Reference

```python
# Import everything
from otk import (
    OllamaClient,              # Core client
    ChatSession,               # Conversational
    CustomizableModel,         # Full customization
    ModelBuilder,              # Fluent builder
    ModelPresets,              # Quick configs
    ModelExperiment,           # Testing
    ModelPlayground,           # Experimentation
    ABTest,                    # A/B testing
)

# Quick patterns
client = OllamaClient()                    # Basic usage
session = ChatSession("llama2")            # Conversations
model = CustomizableModel("llama2")        # Customization
experiment = ModelExperiment()             # Testing
playground = ModelPlayground()             # Exploring

# Build custom model
model = (ModelBuilder("llama2")
         .with_preset("creative")
         .with_hook(HookType.POST_PROCESS, my_hook)
         .build())
```

---

## Examples to Study

Check these files for complete examples:

- `examples/creative_integrations.py` - Real-world integration patterns
- `examples/experimentation_playground.py` - Interactive experimentation
- `examples/advanced_model_handling.py` - Different model formats
- `examples/efficient_response_processing.py` - Performance patterns

---

## Need Help?

- 📖 Check `README.md` for API reference
- 🚀 See `GETTING_STARTED.md` for basics
- 💡 Run `examples/creative_integrations.py` for ideas
- 🧪 Try `examples/experimentation_playground.py` for testing
- 📝 Read `QUICK_REFERENCE.md` for quick lookup

---

## Remember

**This library is a toolkit, not a finished product.** You have full control to:

- Customize model behavior
- Add your own processing
- Chain multiple models
- Build complex workflows
- Integrate into ANY application
- Experiment and find what works

**Go beyond chat. Build something amazing! 🚀**
