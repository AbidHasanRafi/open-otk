# 🎨 GUI Templates & Tools

Custom GUIs for your Ollama models - **no frameworks required!**

## 🚀 Two Ways to Build GUIs

### 1. GUI Template Generator App (Recommended)

**Visual tool for browsing, managing, and generating templates:**

```bash
python create_starter_gui.py
```

**Features:**
- 🌐 Browse ALL available models from ollama.com
- 🔧 Manage installed models (install, delete, run, info)
- ✨ Generate templates with clicks instead of typing
- 🎨 Beautiful dark-themed interface
- 📊 Real-time status and feedback

[📖 Full GUI App Documentation](GUI_APP_README.md)

---

### 2. CLI Template Generator

**Command-line wizard for quick generation:**

```bash
python create_starter.py
```

**Choose from 7 template types including**:
- Tkinter GUI - Custom desktop interface
- Tkinter Advanced - Enhanced GUI with styling
- Simple Chat - Basic CLI interface
- Custom Model - Fully customizable
- Streaming Chat - Real-time responses
- Experimentation - Test and compare
- Integration - Add to your existing projects

---

## 🎨 Tkinter GUI Templates

### What Are They?

Pre-built desktop GUI applications using Python's built-in Tkinter library.

**Key Benefits:**
- ✅ **Zero Dependencies** - Tkinter is built into Python
- ✅ **Full Customization** - Complete control over UI
- ✅ **Cross-Platform** - Works on Windows, macOS, Linux
- ✅ **No Web Server** - Native desktop application
- ✅ **Fast** - No framework overhead

### Template Types

#### 1. Tkinter GUI 🎨

**Perfect for:** Simple desktop chat applications

**Features:**
- Clean chat interface
- Message history
- Input field with send button
- Model selection
- Scrollable chat area

**Generated Code:** ~200 lines

**Example:**
```python
# Generated automatically
python my_ollama_app.py
# Opens a window with chat interface!
```

#### 2. Tkinter Advanced 🚀

**Perfect for:** Feature-rich desktop applications

**Features:**
- Everything from basic template PLUS:
- Temperature slider
- System prompt customization
- Clear chat history
- Save/load conversations
- Model info display
- Status indicators
- Custom styling and colors
- Keyboard shortcuts

**Generated Code:** ~400 lines

**Example:**
```python
# Generated with all features
python my_advanced_app.py
# Rich desktop application!
```

---

## 🚀 Quick Start Guide

### Method 1: Using GUI App

1. **Launch the GUI:**
   ```bash
   pip install requests beautifulsoup4  # First-time only
   python create_starter_gui.py
   ```

2. **Browse & Install a Model** (if you don't have one):
   - Go to "🌐 Browse Models" tab
   - Search or browse available models
   - Select one (try `qwen2:0.5b` for quick testing)
   - Click "📥 Install Selected Model"

3. **Generate Your GUI:**
   - Go to "✨ Generate Template" tab
   - Select your model
   - Choose "Tkinter GUI" or "Tkinter Advanced"
   - Enter filename (e.g., `my_chat_gui.py`)
   - Click "🚀 Generate Template"

4. **Run It:**
   ```bash
   python my_chat_gui.py
   ```

### Method 2: Using CLI

1. **Run the wizard:**
   ```bash
   python create_starter.py
   ```

2. **Follow prompts:**
   ```
   Select model: [1] qwen2:0.5b
   Select template: [6] Tkinter GUI
   Enter filename: my_chat_gui.py
   ```

3. **Done!**
   ```bash
   python my_chat_gui.py
   ```

---

## 🎨 Customization

### Colors & Styling

Both Tkinter templates use customizable color schemes:

```python
# In generated code, find the COLORS dict:
COLORS = {
    'bg': '#1a1a2e',           # Main background
    'bg_secondary': '#16213e',  # Secondary areas
    'accent': '#00d4ff',        # Buttons, highlights
    'success': '#00ff88',       # Success messages
    'text': '#ffffff',          # Text color
}

# Change these to customize your theme!
```

### Adding Features

The generated code is fully editable. Common additions:

**File Upload:**
```python
from tkinter import filedialog

def upload_file(self):
    filename = filedialog.askopenfilename()
    with open(filename, 'r') as f:
        content = f.read()
        self.send_message(f"Analyze: {content}")
```

**Save Chat History:**
```python
def save_history(self):
    with open('chat_history.txt', 'w') as f:
        f.write(self.chat_display.get('1.0', tk.END))
```

**Temperature Control:**
```python
# Already in Advanced template!
self.temperature = tk.Scale(
    from_=0.0, to=2.0, 
    resolution=0.1,
    orient='horizontal'
)
```

---

## 📊 Feature Comparison

| Feature | Basic GUI | Advanced GUI |
|---------|-----------|--------------|
| Chat interface | ✅ | ✅ |
| Send/receive messages | ✅ | ✅ |
| Message history | ✅ | ✅ |
| Scrollable area | ✅ | ✅ |
| Temperature control | ❌ | ✅ |
| System prompt | ❌ | ✅ |
| Clear history | ❌ | ✅ |
| Save/load chats | ❌ | ✅ |
| Model info | ❌ | ✅ |
| Status indicators | ❌ | ✅ |
| Keyboard shortcuts | ❌ | ✅ |
| Custom colors | ✅ | ✅ |
| Lines of code | ~200 | ~400 |

---

## 💡 Use Cases

### Personal Assistant
```bash
# Generate Tkinter Advanced
# Customize system prompt for assistant behavior
# Add file upload for document analysis
```

### Code Helper
```bash
# Generate Tkinter GUI
# Set system prompt: "You are a coding assistant"
# Great for quick code questions
```

### Writing Tool
```bash
# Generate Tkinter Advanced
# Add save/load for drafts
# Use temperature slider for creativity
```

### Learning Tool
```bash
# Generate Tkinter GUI
# Simple interface for students
# No distractions, just chat
```

---

## 🔧 Technical Details

### Tkinter Basics

Tkinter is Python's standard GUI library:
- **Included**: No installation needed
- **Mature**: Stable and well-documented
- **Cross-platform**: Works everywhere Python does
- **Lightweight**: Small footprint
- **Flexible**: Full customization possible

### Generated Code Structure

```python
# 1. Imports
import tkinter as tk
from otk import OllamaClient

# 2. Color scheme
COLORS = {...}

# 3. Main application class
class OllamaGUI:
    def __init__(self):
        # Setup window, widgets
        
    def send_message(self, message):
        # Handle sending
        
    def display_message(self, sender, text):
        # Display in chat

# 4. Entry point
if __name__ == "__main__":
    app = OllamaGUI()
    app.run()
```

### Threading

Both templates use threading for non-blocking AI responses:

```python
import threading

def send_in_thread():
    response = client.generate(...)
    # Update UI from thread
    
thread = threading.Thread(target=send_in_thread)
thread.daemon = True
thread.start()
```

This keeps the UI responsive while waiting for responses.

---

## 🎯 Best Practices

### Choosing a Template

**Use Basic (Tkinter GUI) when:**
- You want simple, clean interface
- Building a focused tool
- Prefer minimal code
- Quick prototyping

**Use Advanced (Tkinter Advanced) when:**
- Need full control over model parameters
- Want to save/load conversations
- Building a production tool
- Need rich features

### Performance Tips

1. **Start with smaller models** (`qwen2:0.5b`) for testing
2. **Use threading** (already built-in)
3. **Limit message history** for very long chats
4. **Clear chat periodically** to free memory

### UI/UX Tips

1. **Keep it simple** - Don't overcrowd the interface
2. **Use color wisely** - Highlight important elements
3. **Provide feedback** - Show when AI is thinking
4. **Keyboard shortcuts** - Make it efficient (Advanced template has this)

---

## 🆚 Why NOT Streamlit/Gradio/Flask?

### This Toolkit's Philosophy

We provide **custom-built** GUIs because:

✅ **No Vendor Lock-in**: Pure Python code you control  
✅ **No Dependencies**: Just Tkinter (built-in)  
✅ **Full Customization**: Change anything  
✅ **Lightweight**: No web server overhead  
✅ **Fast**: Native performance  
✅ **Learn by Doing**: Understand how it works  

### Want Web/Frameworks Anyway?

No problem! Use the **Integration** template:

```bash
python create_starter.py
# Select: [5] Integration
```

Then add ANY framework you want:
- Flask
- FastAPI
- Streamlit
- Gradio  
- Django
- Whatever you prefer!

**We give you the building blocks** - you add the frameworks you need.

---

## 📚 Resources

### Tkinter Learning
- [Official Docs](https://docs.python.org/3/library/tkinter.html)
- [Real Python Tutorial](https://realpython.com/python-gui-tkinter/)
- [TkDocs](https://tkdocs.com/tutorial/)

### Ollama Toolkit
- [CUSTOM_GUI_GUIDE.md](CUSTOM_GUI_GUIDE.md) - Deep customization guide
- [GUI_APP_README.md](GUI_APP_README.md) - GUI app documentation
- [README.md](README.md) - Main documentation

### Color Tools
- [Coolors.co](https://coolors.co/) - Color palette generator
- [Tkinter Colors](https://www.tcl.tk/man/tcl8.4/TkCmd/colors.htm) - Named colors

---

## ❓ FAQ

**Q: Do I need to install Tkinter?**  
A: No! It's included with Python.

**Q: Can I use these templates in my project?**  
A: Yes! Generated code is yours to use freely.

**Q: Can I modify the generated code?**  
A: Absolutely! That's the whole point.

**Q: Which template should I start with?**  
A: Try Tkinter GUI first, upgrade to Advanced if you need more features.

**Q: Can I deploy these as .exe files?**  
A: Yes! Use PyInstaller:
```bash
pip install pyinstaller
pyinstaller --onefile --windowed your_app.py
```

**Q: Do these work on Mac/Linux?**  
A: Yes! Tkinter is cross-platform.

**Q: Can I add a web interface later?**  
A: Yes! Use the Integration template and add Flask/FastAPI.

---

## 🚀 Next Steps

1. **Try the GUI app**: `python create_starter_gui.py`
2. **Generate a template**: Pick Tkinter GUI or Advanced
3. **Run it**: See it work immediately
4. **Customize it**: Make it yours
5. **Share it**: Show off your creation!

---

**Made with ❤️ using pure Python and Tkinter!**

No frameworks, no lock-in, just clean customizable code! 🎨
pip install streamlit
streamlit run your_app.py
```

**Screenshot Preview:**
```
┌─────────────────────────────────────────────┐
│  ⚙️ Settings         🦙 Chat with Ollama    │
│  ─────────           ────────────────────   │
│  🦙 Model                                    │
│  qwen2:0.5b          💬 Chat messages here  │
│                                              │
│  🎛️ Parameters      ┌──────────────────┐   │
│  Temperature: 0.7    │ Your message...  │   │
│                      └──────────────────┘   │
│  🗑️ Clear Chat                              │
└─────────────────────────────────────────────┘
```

### 2. Gradio UI 🎨

**Perfect for:** Sharing with others, public demos, quick testing

**Features:**
- Clean, professional design
- Easy to share (built-in sharing link)
- Mobile-friendly
- Collapsible settings
- Export conversations

**To run:**
```bash
pip install gradio
python your_app.py
```

**Access:** Opens at `http://localhost:7860`

**Screenshot Preview:**
```
┌─────────────────────────────────────────────┐
│         🦙 Ollama Chat Interface            │
│         Powered by qwen2:0.5b               │
│                                              │
│  ┌────────────────────────────────────┐     │
│  │ 🦙 Bot: Hello! How can I help?    │     │
│  │                                    │     │
│  │ 👤 User: What's AI?               │     │
│  │                                    │     │
│  │ 🦙 Bot: AI stands for...         │     │
│  └────────────────────────────────────┘     │
│                                              │
│  [Type your message here...] [Send 🚀]      │
│                                              │
│  [Clear 🗑️]                                 │
└─────────────────────────────────────────────┘
```

### 3. Streamlit Advanced 🚀

**Perfect for:** Professional projects, multiple use cases, production

**Features:**
- **4 Different Tools:**
  1. 💬 **Chat** - Full conversational interface
  2. 📝 **Analyze** - Sentiment, summary, keywords
  3. ✨ **Generate** - Blog posts, emails, content
  4. 🎯 **Summarize** - Smart text summarization

- **Professional UI:**
  - Multiple tabs for different functions
  - Real-time stats tracking
  - Export functionality
  - Customizable parameters
  - Time tracking

**To run:**
```bash
pip install streamlit
streamlit run your_app.py
```

## Installation

### Option 1: Individual Packages
```bash
# For Streamlit templates
pip install streamlit

# For Gradio templates
pip install gradio
```

### Option 2: Install All
```bash
pip install -r requirements.txt
```

## Customization

All templates are **fully customizable**! Here's what you can easily modify:

### Colors & Styling
```python
# In Streamlit templates - edit the CSS:
st.markdown("""
    <style>
    .main {
        background: linear-gradient(YOUR_COLORS);
    }
    </style>
""")
```

### Add New Features
```python
# Add a new tab in Advanced template:
with st.tabs(["Chat", "Analyze", "YOUR_NEW_FEATURE"]):
    # Your code here
    pass
```

### Change Model Settings
```python
# Adjust temperature, add more parameters:
temperature = st.slider("Temperature", 0.0, 2.0, 0.7)
max_tokens = st.slider("Max Tokens", 100, 2000, 1000)
```

## Examples

### Generate a Simple Streamlit Chat:
```bash
python create_starter.py
# Select: [1] your model
# Select: [6] Streamlit UI
# Enter: my_chat.py
```

### Generate Advanced Multi-Tool App:
```bash
python create_starter.py
# Select: [1] your model  
# Select: [8] Streamlit Advanced
# Enter: my_advanced_app.py
```

### Generate Gradio Interface:
```bash
python create_starter.py
# Select: [1] your model
# Select: [7] Gradio UI
# Enter: my_gradio_app.py
```

## Styling Guide

### Streamlit Themes

**Dark Purple Gradient** (Default):
```python
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%)
```

**Blue Ocean:**
```python
background: linear-gradient(135deg, #0093E9 0%, #80D0C7 100%)
```

**Sunset Orange:**
```python
background: linear-gradient(135deg, #FF6B6B 0%, #FFE66D 100%)
```

**Forest Green:**
```python
background: linear-gradient(135deg, #56ab2f 0%, #a8e6cf 100%)
```

### Gradio Themes

Change the theme in your Gradio app:
```python
demo = gr.Blocks(theme=gr.themes.Soft())      # Soft theme
demo = gr.Blocks(theme=gr.themes.Glass())     # Glass theme
demo = gr.Blocks(theme=gr.themes.Monochrome()) # Monochrome
```

## Tips & Tricks

### 1. Add Custom Avatars
**Streamlit:**
```python
with st.chat_message("assistant", avatar="🤖"):
    st.write("Hello!")
```

**Gradio:**
```python
chatbot = gr.Chatbot(avatar_images=("👤", "🤖"))
```

### 2. Add Loading Animations
```python
with st.spinner("Processing your request..."):
    response = get_response()
```

### 3. Add Metrics & Stats
```python
col1, col2, col3 = st.columns(3)
col1.metric("Responses", "42")
col2.metric("Avg Time", "2.3s")
col3.metric("Success Rate", "98%")
```

### 4. Add File Upload
```python
uploaded_file = st.file_uploader("Upload a document")
if uploaded_file:
    content = uploaded_file.read()
    # Process with Ollama
```

### 5. Add Voice Input (Advanced)
Use speech recognition libraries:
```python
import speech_recognition as sr
# Add voice input to your interface
```

## Deployment

### Deploy Streamlit App
```bash
# Deploy to Streamlit Cloud (free)
# 1. Push to GitHub
# 2. Visit share.streamlit.io
# 3. Connect your repo
```

### Deploy Gradio App
```bash
# Deploy to Hugging Face Spaces (free)
# 1. Create account at huggingface.co
# 2. Create new Space
# 3. Upload your app
```

## Troubleshooting

### Streamlit Issues

**Port already in use:**
```bash
streamlit run app.py --server.port 8502
```

**Can't connect:**
```bash
streamlit run app.py --server.address 0.0.0.0
```

### Gradio Issues

**Share link not working:**
```python
demo.launch(share=True)  # Creates public link
```

**Custom port:**
```python
demo.launch(server_port=7861)
```

## More Resources

- **Streamlit Docs:** https://docs.streamlit.io
- **Gradio Docs:** https://gradio.app/docs
- **Streamlit Gallery:** https://streamlit.io/gallery
- **Gradio Examples:** https://gradio.app/demos

## Next Steps

1. Generate your first GUI template
2. Customize the styling to match your brand
3. Add new features based on your needs
4. Deploy and share with others!

Happy building! 🎨🚀
