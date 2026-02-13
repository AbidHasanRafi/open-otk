# Starter Templates

This directory contains ready-to-use templates for common Ollama applications.

## Available Templates

### 1. Chatbot (`chatbot/`)
A complete interactive chatbot with conversation management.

**Features:**
- Interactive chat interface
- Conversation history
- Save/load conversations
- Command system

**Quick Start:**
```bash
cd chatbot
python simple_chatbot.py
```

[Read More](chatbot/README.md)

---

### 2. RAG System (`rag_system/`)
Retrieval Augmented Generation for question-answering with custom knowledge.

**Features:**
- Semantic search with embeddings
- Custom knowledge base
- Context-aware answers
- Save/load knowledge bases

**Quick Start:**
```bash
cd rag_system
python simple_rag.py
```

**Requirements:**
```bash
ollama pull llama2
ollama pull nomic-embed-text
pip install numpy
```

[Read More](rag_system/README.md)

---

### 3. Text Analyzer (`text_analyzer/`)
Analyze text for sentiment, keywords, entities, and more.

**Features:**
- Sentiment analysis
- Text summarization
- Keyword extraction
- Named entity recognition
- Topic classification
- Language detection

**Quick Start:**
```bash
cd text_analyzer
python text_analyzer.py
```

[Read More](text_analyzer/README.md)

---

### 4. Code Assistant (`code_assistant/`)
AI-powered coding assistant for generation, debugging, and review.

**Features:**
- Code generation
- Code explanation
- Debugging help
- Code review
- Optimization suggestions
- Test generation
- Documentation

**Quick Start:**
```bash
cd code_assistant
python code_assistant.py
```

**Recommended Model:**
```bash
ollama pull codellama
```

[Read More](code_assistant/README.md)

---

## Customization

All templates are designed to be easily customizable:

1. **Change Models**: Edit the model name in the initialization
2. **Adjust Temperature**: Modify for more/less creative responses
3. **System Messages**: Customize the AI's personality
4. **Add Features**: Extend the templates with your own functionality

## Use Cases

- **Chatbot**: Customer support, virtual assistants, tutoring
- **RAG System**: Document Q&A, knowledge bases, research tools
- **Text Analyzer**: Content moderation, data analysis, categorization
- **Code Assistant**: Development tools, code review, learning

## Next Steps

1. Try each template to see what they can do
2. Customize them for your specific needs
3. Combine features from multiple templates
4. Build your own applications using these as starting points

## Contributing

Have a great template idea? Feel free to contribute!

## Support

- Check the individual README files in each template directory
- See the main [README](../README.md) for API documentation
- Visit [Ollama Documentation](https://github.com/ollama/ollama/blob/main/docs/README.md)
