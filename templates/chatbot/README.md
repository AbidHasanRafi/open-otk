# Simple Chatbot Template

A ready-to-use chatbot template built with Ollama Toolkit.

## Features

- Interactive conversation interface
- Streaming responses
- Save/load conversation history
- Clear conversation history
- Easy model customization

## Usage

1. Make sure Ollama is running
2. Run the chatbot:
   ```bash
   python simple_chatbot.py
   ```

3. Start chatting!

## Commands

- `quit` or `exit` - Exit the chatbot
- `clear` - Clear conversation history
- `save` - Save conversation to file

## Customization

Edit the `SimpleChatbot` class to customize:

- **Model**: Change the default model in `main()`
- **System Message**: Modify the personality in `setup()`
- **Temperature**: Adjust creativity in the `ChatSession` initialization
- **Max History**: Control conversation memory length

## Example

```python
# Use a different model
chatbot = SimpleChatbot(model="mistral")
chatbot.run()
```

## Requirements

- Ollama installed and running
- otk library
- At least one model pulled (e.g., `ollama pull llama2`)
