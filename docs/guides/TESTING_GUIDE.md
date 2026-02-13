# Testing Guide 🧪

Quick guide to test and verify the Ollama Toolkit library.

## Quick Start Testing

### 1. Verify Setup (Recommended First Step)

```bash
python verify_setup.py
```

This checks:
- ✅ All imports working
- ✅ Ollama connection
- ✅ Models installed
- ✅ Response handlers working
- ✅ Live model test

### 2. Install the Library

```bash
# Install in development mode
pip install -e .

# Or just install dependencies
pip install -r requirements.txt
```

### 3. Simple Quick Test

```python
# Create test_quick.py
from otk import OllamaClient, ChatSession

# Test 1: Basic client
client = OllamaClient()
print("Testing basic generate...")
response = client.generate("llama2", "Say 'Hello'")
print(f"✓ Response: {response[:50]}")

# Test 2: Chat session with auto-processing
print("\nTesting chat session...")
session = ChatSession("llama2", auto_process=True)
response = session.send("What is 2+2?")
print(f"✓ Response: {response}")

print("\n✅ All basic tests passed!")
```

Run it:
```bash
python test_quick.py
```

## Feature-by-Feature Testing

### Test Response Handling

```python
from otk import clean_thinking_tags, auto_clean_response, ModelResponseHandler, ModelType

# Test 1: Clean thinking tags
raw = "<think>reasoning here</think>The answer is 42"
clean, thinking = clean_thinking_tags(raw)
assert clean == "The answer is 42"
assert thinking == ["reasoning here"]
print("✓ Thinking tag cleaning works")

# Test 2: Auto-detect handler
clean = auto_clean_response(raw, "deepseek-r1")
assert "<think>" not in clean
print("✓ Auto clean works")
```

### Test Customization

```python
from otk import CustomizableModel, ModelBuilder, HookType, ModelPresets

# Test 1: Custom model with hook
def test_hook(ctx):
    print(f"✓ Hook called: {ctx.model}")

model = CustomizableModel("llama2")
model.add_hook(HookType.POST_PROCESS, test_hook)
response = model.generate("Say hello")
print(f"✓ Custom model works")

# Test 2: Builder pattern
model = (ModelBuilder("llama2")
         .with_preset("creative")
         .with_temperature(0.8)
         .build())
response = model.generate("Test prompt")
print("✓ Builder pattern works")

# Test 3: Presets
config = ModelPresets.creative()
assert config.temperature == 0.9
print("✓ Presets work")
```

### Test Experimentation Tools

```python
from otk import ModelExperiment, ModelPlayground

# Test 1: Single model test
experiment = ModelExperiment()
result = experiment.run_single("llama2", "What is Python?")
assert not result.error
print(f"✓ Single test: {result.time_taken:.2f}s")

# Test 2: Benchmark
stats = experiment.benchmark("llama2", "Say hi", iterations=3)
assert 'avg_time' in stats
print(f"✓ Benchmark: {stats['avg_time']:.2f}s avg")

# Test 3: Playground
playground = ModelPlayground()
# This will output to console
playground.try_temperatures("llama2", "Test", temperatures=[0.5, 0.7])
print("✓ Playground works")
```

### Test Model Management

```python
from otk import ModelManager

manager = ModelManager()

# Test 1: List models
models = manager.list_models()
print(f"✓ Found {len(models)} models")

# Test 2: Check if model exists
exists = manager.model_exists("llama2")
print(f"✓ Model exists check: {exists}")
```

## Run Examples

### Basic Examples

```bash
# Test basic chat
python examples/simple_chat.py

# Test streaming
python examples/streaming_chat.py

# Test chat session
python examples/chat_session.py
```

### Advanced Examples

```bash
# Test model handling
python examples/advanced_model_handling.py

# Test efficiency
python examples/efficient_response_processing.py

# Test integrations (examples only, won't run full demos)
python examples/creative_integrations.py

# Interactive playground
python examples/experimentation_playground.py
```

## Interactive Testing

### 1. Experimentation Playground

Most interactive way to test:

```bash
python examples/experimentation_playground.py
```

Then choose:
- Option 7: Quick Test (fastest)
- Option 8: List Models
- Option 1: Compare Models
- Option 2: Test Temperatures

### 2. Python REPL

```bash
python
```

```python
>>> from otk import *
>>> 
>>> # Quick test
>>> client = OllamaClient()
>>> client.generate("llama2", "Say hello")
'Hello! ...'
>>> 
>>> # Test chat
>>> session = ChatSession("llama2")
>>> session.send("Hi")
'Hello! How can I help you today?'
>>> 
>>> # Test customization
>>> model = (ModelBuilder("llama2")
...          .with_temperature(0.9)
...          .build())
>>> model.generate("Test")
'...'
```

## Automated Testing

### Create a Test Suite

```python
# test_all.py
import sys

def test_imports():
    """Test all imports work"""
    try:
        from otk import (
            OllamaClient, ChatSession, ModelManager,
            CustomizableModel, ModelBuilder, ModelPresets,
            ModelExperiment, ModelPlayground, ABTest,
            clean_thinking_tags, auto_clean_response
        )
        print("✓ All imports successful")
        return True
    except Exception as e:
        print(f"✗ Import error: {e}")
        return False

def test_response_handlers():
    """Test response handling"""
    from otk import clean_thinking_tags
    
    raw = "<think>test</think>answer"
    clean, thinking = clean_thinking_tags(raw)
    
    if clean == "answer" and thinking == ["test"]:
        print("✓ Response handlers work")
        return True
    else:
        print("✗ Response handler test failed")
        return False

def test_ollama_connection():
    """Test Ollama connection"""
    from otk import OllamaClient
    
    try:
        client = OllamaClient()
        if client.is_running():
            print("✓ Ollama connection works")
            return True
        else:
            print("✗ Ollama not responding")
            return False
    except Exception as e:
        print(f"✗ Connection error: {e}")
        return False

def test_basic_generation():
    """Test basic generation"""
    from otk import OllamaClient
    
    try:
        client = OllamaClient()
        response = client.generate("llama2", "Say 'test'", max_tokens=10)
        
        if response:
            print(f"✓ Basic generation works")
            return True
        else:
            print("✗ No response received")
            return False
    except Exception as e:
        print(f"✗ Generation error: {e}")
        return False

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("Running Ollama Toolkit Tests")
    print("="*60 + "\n")
    
    tests = [
        ("Imports", test_imports),
        ("Response Handlers", test_response_handlers),
        ("Ollama Connection", test_ollama_connection),
        ("Basic Generation", test_basic_generation),
    ]
    
    results = []
    for name, test_func in tests:
        print(f"\nTesting: {name}")
        print("-" * 60)
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"✗ Test crashed: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")
    
    print(f"\n{passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
```

Run it:
```bash
python test_all.py
```

## Troubleshooting

### Issue: "Connection refused"

**Solution:**
```bash
# Start Ollama
ollama serve

# Or on Windows, just make sure Ollama app is running
```

### Issue: "Model not found"

**Solution:**
```bash
# List available models
ollama list

# Pull a model
ollama pull llama2

# Or use the library
python -c "from otk import ModelManager; m = ModelManager(); m.pull_model('llama2')"
```

### Issue: "Import errors"

**Solution:**
```bash
# Reinstall dependencies
pip install -r requirements.txt

# Or install in development mode
pip install -e .
```

### Issue: "Thinking tags still showing"

**Solution:**
```python
# Make sure auto_process is enabled (it's default)
session = ChatSession("deepseek-r1", auto_process=True)

# Or manually clean
from otk import clean_thinking_tags
clean_text, thinking = clean_thinking_tags(raw_response)
```

## Performance Testing

### Benchmark a Model

```python
from otk import ModelExperiment

experiment = ModelExperiment()

# Benchmark
stats = experiment.benchmark(
    model="llama2",
    prompt="What is Python?",
    iterations=10
)

experiment.print_benchmark(stats)
```

### Compare Multiple Models

```python
result = experiment.compare_models(
    models=["llama2", "mistral", "phi"],
    prompt="Explain AI in one sentence",
    parallel=True
)

experiment.print_comparison(result)
```

## What to Test Based on Your Use Case

### If building a chatbot:
```bash
python examples/chat_session.py
python examples/creative_integrations.py  # See PersonalityBot
```

### If integrating into an app:
```bash
python examples/creative_integrations.py  # Study all examples
```

### If comparing models:
```bash
python examples/experimentation_playground.py
python examples/model_comparison.py
```

### If working with thinking models:
```bash
python examples/advanced_model_handling.py
python examples/efficient_response_processing.py
```

## Continuous Testing

### Watch for Changes

Create a simple watcher script if you're developing:

```python
# watch_test.py
import time
import subprocess

print("Watching for changes... (Ctrl+C to stop)")
while True:
    print("\n" + "="*60)
    print("Running tests...")
    subprocess.run(["python", "test_all.py"])
    print("\nWaiting 30 seconds...")
    time.sleep(30)
```

## Success Criteria

Your library is working if:

✅ `verify_setup.py` passes all checks
✅ You can generate responses from models
✅ Chat sessions maintain context
✅ Response handlers clean outputs correctly
✅ Customization hooks work
✅ Experimentation tools run
✅ Examples execute without errors

## Quick Test Commands Summary

```bash
# 1. Full verification
python verify_setup.py

# 2. Quick test
python -c "from otk import OllamaClient; print(OllamaClient().generate('llama2', 'Say hi'))"

# 3. Test imports
python -c "from otk import *; print('✓ All imports work')"

# 4. Run an example
python examples/simple_chat.py

# 5. Interactive playground
python examples/experimentation_playground.py

# 6. Model management
python examples/model_manager.py
```

## Need Help?

1. Run `python verify_setup.py` first
2. Check error messages
3. Make sure Ollama is running
4. Make sure models are installed
5. Check the troubleshooting section above

**Happy testing! 🧪**
