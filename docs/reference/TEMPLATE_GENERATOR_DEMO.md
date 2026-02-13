# Interactive Template Generator Demo

## What is `create_starter.py`?

An interactive command-line wizard that generates ready-to-run Ollama applications!

## Quick Demo

```bash
$ python create_starter.py

==================================================
   OLLAMA TOOLKIT - STARTER TEMPLATE GENERATOR
==================================================

Step 1: Select your model
----------------------------------------------------------------------

Available models:

  [1] qwen2:0.5b                     (335.85 MB)
  [2] deepseek-r1:1.5b               (1.04 GB)

  [0] Cancel

Select model number: 1

----------------------------------------------------------------------
Template types:

  [1] Simple Chat         - Basic conversational chat interface
  [2] Custom Model        - Customizable model with hooks and callbacks
  [3] Streaming Chat      - Real-time streaming responses
  [4] Experimentation     - Compare and test different settings
  [5] Integration         - Template for integrating into your app
  [6] Tkinter GUI         - Custom desktop GUI with Tkinter
  [7] Tkinter Advanced    - Advanced Tkinter with features

  [0] Cancel

Select template type: 6

----------------------------------------------------------------------
Enter filename (default: my_ollama_app.py): my_chat_ui.py

======================================================================
TEMPLATE CREATED SUCCESSFULLY!
======================================================================

File: my_chat_ui.py
Model: qwen2:0.5b
Type: Tkinter GUI

To run your app:
  python my_chat_ui.py

The GUI window will open automatically - no dependencies needed!

Happy coding!
======================================================================
```

## What if NO Models Are Installed?

```bash
$ python create_starter.py

==================================================
   OLLAMA TOOLKIT - STARTER TEMPLATE GENERATOR
==================================================

Step 1: Select your model
----------------------------------------------------------------------

No models found!

Would you like to install a model now?
Install model? (Y/n): y

======================================================================
   MODEL INSTALLATION WIZARD
======================================================================

Recommended models:

  [1] qwen2:0.5b           494MB    Fastest - Perfect for testing
  [2] llama2               3.8GB    Balanced - Great all-around
  [3] mistral              4.1GB    Powerful - Excellent quality
  [4] deepseek-r1:1.5b     1.04GB   Thinking - Shows reasoning
  [5] gemma:2b             1.7GB    Google - Compact but capable

  [6] Enter custom model name
  [0] Skip for now

Select model to install: 1

Installing qwen2:0.5b...
This may take a few minutes depending on your connection.

Continue? (Y/n): y

pulling manifest
pulling 6f48b936... 100% ▕████████████████▏ 352 MB
pulling 8ab4849b... 100% ▕████████████████▏   70 B
pulling a68fc89a... 100% ▕████████████████▏  485 B
verifying sha256 digest
writing manifest
removing any unused layers
success

Successfully installed qwen2:0.5b!

[... continues with template selection ...]
```

## Generated Files

### Example 1: Streamlit UI (`my_chat.py`)

A beautiful web interface with:
- Gradient background design
- Real-time chat
- Temperature slider
- Clear chat button
- Conversation history
- Professional styling

**Run:** `streamlit run my_chat.py`

**Preview:**
- Opens in browser automatically
- Beautiful purple gradient background
- Sidebar with settings
- Chat bubbles with timestamps
- Export conversations

### Example 2: Gradio UI (`my_gradio_app.py`)

A clean, shareable interface with:
- Professional chat layout
- Easy sharing (public URLs)
- Mobile-friendly
- Collapsible settings
- Export functionality

**Run:** `python my_gradio_app.py`

**Access:** http://localhost:7860

**Preview:**
- Clean, minimal design
- Share button for public access
- Responsive layout
- Quick setup

### Example 3: Advanced Streamlit (`my_advanced.py`)

A multi-tool application with **4 tabs**:

1. **Chat** - Full conversational interface
2. **Analyze** - Text analysis (sentiment, summary, keywords)
3. **Generate** - Content generation (blog posts, emails, etc.)
4. **Summarize** - Smart text summarization

**Run:** `streamlit run my_advanced.py`

**Preview:**
- Professional multi-tab interface
- Stats tracking
- Export capabilities
- Multiple tools in one app

### Example 4: Simple Chat CLI (`my_simple.py`)

A clean command-line interface:
```bash
$ python my_simple.py
Starting chat with qwen2:0.5b...
Type 'quit', 'exit', or 'bye' to end the conversation

You: Hello!