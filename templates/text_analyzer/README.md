# Text Analyzer Template

Analyze text using Ollama models for various NLP tasks.

## Features

- **Sentiment Analysis** - Detect positive, negative, or neutral sentiment
- **Summarization** - Generate concise summaries
- **Keyword Extraction** - Extract important keywords
- **Entity Extraction** - Identify people, places, organizations
- **Topic Classification** - Classify text into topics
- **Language Detection** - Detect the language of text
- **Readability Analysis** - Assess text complexity

## Usage

### Basic Usage

```python
from text_analyzer import TextAnalyzer

analyzer = TextAnalyzer(model="llama2")

# Sentiment analysis
result = analyzer.analyze_sentiment("I love this product!")
print(result['sentiment'])  # Positive

# Summarization
summary = analyzer.summarize(long_text, max_sentences=3)

# Extract keywords
keywords = analyzer.extract_keywords(text, num_keywords=5)

# Extract entities
entities = analyzer.extract_entities(text)
print(entities['PERSON'])  # List of people mentioned
```

### Run the Demo

```bash
python text_analyzer.py
```

## Available Methods

### `analyze_sentiment(text)`
Returns sentiment: Positive, Negative, or Neutral

### `summarize(text, max_sentences=3)`
Generates a concise summary

### `extract_keywords(text, num_keywords=5)`
Extracts the most important keywords

### `extract_entities(text)`
Extracts named entities (PERSON, PLACE, ORGANIZATION)

### `classify_topic(text, topics)`
Classifies text into one of the provided topics

### `detect_language(text)`
Detects the language of the text

### `analyze_readability(text)`
Analyzes text complexity and reading level

## Interactive Mode

The script includes an interactive mode:

```bash
python text_analyzer.py
```

Commands:
- `sentiment` - Analyze sentiment
- `summarize` - Generate summary
- `keywords` - Extract keywords
- `entities` - Extract named entities
- `topic` - Classify topic
- `language` - Detect language
- `quit` - Exit

## Customization

### Use Different Models

```python
# Use a more powerful model
analyzer = TextAnalyzer(model="mistral")

# Use a coding-focused model for code analysis
analyzer = TextAnalyzer(model="codellama")
```

### Adjust Temperature

For more consistent results, lower the temperature:
```python
# In each method, adjust:
temperature=0.05  # More deterministic
```

## Use Cases

- Email classification
- News article analysis
- Social media monitoring
- Document processing
- Content categorization
- Information extraction

## Requirements

- Ollama with at least one model installed
- otk library
