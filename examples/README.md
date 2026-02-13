# Examples

This directory contains ready-to-run examples demonstrating various features of the Ollama Toolkit.

## Running Examples

Make sure Ollama is running and you have at least one model installed:

```bash
ollama pull llama2
```

Then run any example:

```bash
python simple_chat.py
```

## Available Examples

### 1. simple_chat.py
Basic text generation with and without system messages.

**What you'll learn:**
- Simple text generation
- Using system messages
- Basic model interaction

**Run:**
```bash
python simple_chat.py
```

### 2. streaming_chat.py
Real-time streaming responses for better UX.

**What you'll learn:**
- Streaming text generation
- Streaming chat completions
- Real-time output

**Run:**
```bash
python streaming_chat.py
```

### 3. chat_session.py
Interactive chat with conversation history.

**What you'll learn:**
- Maintaining conversation context
- Chat history management
- Exporting/importing conversations
- Interactive chat interface

**Run:**
```bash
python chat_session.py
```

**Demo mode:**
```bash
python chat_session.py --demo
```

### 4. model_manager.py
Interactive model management tool.

**What you'll learn:**
- Listing installed models
- Pulling new models
- Deleting models
- Viewing model information
- Model recommendations

**Run:**
```bash
python model_manager.py
```

### 5. embeddings.py
Generate and compare text embeddings.

**What you'll learn:**
- Generating embeddings
- Calculating similarity
- Semantic search
- Similarity matrices

**Requirements:**
```bash
ollama pull nomic-embed-text
pip install numpy
```

**Run:**
```bash
python embeddings.py
```

### 6. model_comparison.py
Compare responses from different models.

**What you'll learn:**
- Benchmarking models
- Comparing response quality
- Performance metrics
- Model selection

**Requirements:** At least 2 models installed

**Run:**
```bash
python model_comparison.py
```

### 7. advanced_model_handling.py
Work with different model response formats.

**What you'll learn:**
- Automatic response cleaning
- Handling thinking models (DeepSeek-R1)
- Working with code models
- Custom response handlers
- Multi-model format handling

**Run:**
```bash
python advanced_model_handling.py
```

### 8. efficient_response_processing.py
Efficient processing for different model structures.

**What you'll learn:**
- Using EfficientModelChat class
- Automatic vs manual cleaning comparison
- Response timing and optimization
- Multi-turn conversations with auto-processing
- Temperature experimentation

**Run:**
```bash
python efficient_response_processing.py
```

### 9. creative_integrations.py
**Real-world integration patterns for developers.**

**What you'll learn:**
- Building custom tools with Ollama (not just chat!)
- Blog post generators with custom formatting
- Smart data processors and categorizers
- Code helper integrations
- Chatbots with personalities
- Multi-model pipelines
- Adaptive response systems

**Run:**
```bash
python creative_integrations.py
```

**This is the KEY example** - Shows how to integrate Ollama into YOUR projects!

### 10. experimentation_playground.py
**Interactive playground for testing and experimenting.**

**What you'll learn:**
- Interactive model comparison
- Temperature experimentation
- Prompt variations testing
- Benchmarking tools
- A/B testing models
- Finding optimal settings

**Run:**
```bash
python experimentation_playground.py
```

**Use this to explore** - Find what works best for YOUR use case!

## Tips

1. **Start Simple**: Begin with `simple_chat.py` to understand basics
2. **Try Streaming**: Run `streaming_chat.py` to see real-time responses
3. **Interactive Mode**: Use `chat_session.py` for a full chat experience
4. **Manage Models**: Use `model_manager.py` to explore available models
5. **Advanced Features**: Try `embeddings.py` and `model_comparison.py` for advanced features
6. **Different Models**: Run `advanced_model_handling.py` to see how the library handles different model formats
7. **Efficient Processing**: Check `efficient_response_processing.py` for best practices
8. **Build Tools**: Study `creative_integrations.py` to learn integration patterns
9. **Experiment**: Use `experimentation_playground.py` to test and compare

## Recommended Learning Path

**For Beginners:**
1. Start with `simple_chat.py`
2. Try `chat_session.py`
3. Explore `model_manager.py`

**For Integration:**
1. Study `creative_integrations.py` - Real patterns
2. Explore `advanced_model_handling.py` - Different formats
3. Check `efficient_response_processing.py` - Best practices

**For Experimentation:**
1. Use `experimentation_playground.py` - Interactive testing
2. Try `model_comparison.py` - Compare outputs
3. Test `advanced_model_handling.py` - Format handling

## Common Issues

### Connection Error
Make sure Ollama is running:
```bash
ollama serve
```

### Model Not Found
Pull the required model:
```bash
ollama pull llama2
```

### Import Error
Install dependencies:
```bash
pip install -r ../requirements.txt
```

## Next Steps

After trying these examples, check out the [templates/](../templates/) directory for complete application templates!
