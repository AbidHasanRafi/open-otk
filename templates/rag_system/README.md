# RAG System Template

A Retrieval Augmented Generation (RAG) system using Ollama Toolkit.

## What is RAG?

RAG combines:
1. **Retrieval**: Finding relevant information from a knowledge base
2. **Generation**: Using that information to generate accurate answers

This approach helps LLMs provide more accurate, contextual responses based on your specific data.

## Features

- Build custom knowledge bases
- Semantic search using embeddings
- Context-aware answer generation
- Save/load knowledge bases
- Similarity scoring

## Usage

### Basic Usage

```python
from simple_rag import SimpleRAG

# Initialize
rag = SimpleRAG(
    llm_model="llama2",
    embedding_model="nomic-embed-text"
)

# Add documents
rag.add_document("Your document text here", {"source": "example"})

# Query
answer = rag.query("What is this about?")
```

### Run the Demo

```bash
python simple_rag.py
```

## Adding Documents

### From Code

```python
rag.add_document(
    text="Document content...",
    metadata={"title": "Doc 1", "source": "manual"}
)
```

### From JSON File

Create a `documents.json`:
```json
[
    {
        "text": "Document 1 content...",
        "metadata": {"title": "Doc 1"}
    },
    {
        "text": "Document 2 content...",
        "metadata": {"title": "Doc 2"}
    }
]
```

Load it:
```python
rag.add_documents_from_file("documents.json")
```

## Commands

- `quit` - Exit the system
- `search <query>` - Search without generating answer
- `save` - Save knowledge base to file

## Customization

### Change Models

```python
rag = SimpleRAG(
    llm_model="mistral",           # For generation
    embedding_model="nomic-embed-text",  # For embeddings
    top_k=5                        # Number of results to retrieve
)
```

### Adjust Temperature

Lower temperature (0.1-0.3) for more factual answers:
```python
# In the query method, change:
temperature=0.1  # More factual
```

## Requirements

- Ollama with models:
  - LLM model (e.g., `ollama pull llama2`)
  - Embedding model (e.g., `ollama pull nomic-embed-text`)
- numpy

## Use Cases

- Document Q&A systems
- Educational assistants
- Company knowledge bases
- Research paper analysis
- Technical documentation helper
