# 🎨 Custom GUI Templates Guide

Build beautiful, custom desktop interfaces for your Ollama models - **your way**!

## Quick Start

```bash
python create_starter.py
```

Select one of the custom GUI templates:
- **Tkinter GUI** - Desktop app (built-in, zero dependencies!)
- **Tkinter Advanced** - Multi-tab desktop app

## Why Custom GUIs?

✅ **Full Control** - Every pixel, every style, every interaction  
✅ **No Bloat** - Only what you need, nothing more  
✅ **Easy Customization** - Pure Python, easy to modify  
✅ **Learn & Build** - Understand exactly how it works  
✅ **Production Ready** - Real, deployable applications
✅ **No Framework Dependencies** - Just Python built-ins!  

## Template Types

### 1. Tkinter GUI 🖥️

**Perfect for:** Desktop apps, internal tools, offline applications, no-dependency solutions

**Features:**
- Native desktop window
- Custom styled interface
- Real-time chat
- Threaded operations (non-blocking)
- Dark theme included
- **Zero external dependencies** (Tkinter is built-in!)

**To run:**
```bash
python your_app.py
# Window opens immediately!
```

**What you get:**
```python
# A complete GUI with:
- Chat display area with colored text
- Input field with Enter key support
- Send button
- Status bar
- Custom colors (easily changeable!)
- Threading for smooth UI
```

**Example Screenshot (ASCII):**
```
┌──────────────────────────────────────────────────┐
│  🦙 Chat with qwen2:0.5b                        │
├──────────────────────────────────────────────────┤
│                                                  │
│  🦙 Bot: Hello! How can I help you?             │
│                                                  │
│  You: What's AI?                                 │
│                                                  │
│  🦙 Bot: AI stands for Artificial               │
│  Intelligence...                                 │
│                                                  │
├──────────────────────────────────────────────────┤
│  [Type message here...          ] [Send]        │
├──────────────────────────────────────────────────┤
│  Ready                                           │
└──────────────────────────────────────────────────┘
```

---

### 2. Tkinter Advanced 🖥️✨

**Perfect for:** Professional apps, multiple features, complex workflows

**Features:**
- **Multi-tab interface:**
  - 💬 Chat tab
  - ✨ Content generation tab
  - ⚙️ Settings tab
- Professional dark theme
- Temperature slider
- Style selection
- Real-time generation
- Threaded operations
- Modern UI components

**To run:**
```bash
python your_app.py
```

**What you get:**
```
┌─────────────────────────────────────────────────────┐
│  🦙 Ollama Advanced Interface    Model: qwen2:0.5b │
├─────────────────────────────────────────────────────┤
│  [💬 Chat] [✨ Generate] [⚙️ Settings]              │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Chat content area with colored syntax...          │
│                                                     │
│  [Message input field...              ] [Send]     │
│                                                     │
└─────────────────────────────────────────────────────┘
```

## Customization Guide

### Tkinter GUI Customization

**Change Colors:**
```python
self.bg_color = "#2C3E50"      # Background
self.fg_color = "#ECF0F1"      # Text color
self.button_bg = "#3498DB"     # Button color
self.user_color = "#3498DB"    # User message color
self.bot_color = "#2ECC71"     # Bot message color
```

**Popular Color Schemes:**

**Dark Blue:**
```python
self.bg_color = "#1a1a2e"
self.input_bg = "#16213e"
self.button_bg = "#0f3460"
```

**Dracula Theme:**
```python
self.bg_color = "#282a36"
self.fg_color = "#f8f8f2"
self.button_bg = "#bd93f9"
```

**Light Mode:**
```python
self.bg_color = "#FFFFFF"
self.fg_color = "#333333"
self.button_bg = "#007AFF"
```

**Add New Features:**
```python
# Add a clear button:
clear_btn = tk.Button(
    input_frame,
    text="Clear",
    command=self.clear_chat,
    ...
)

def clear_chat(self):
    self.chat_display.config(state=tk.NORMAL)
    self.chat_display.delete("1.0", tk.END)
    self.chat_display.config(state=tk.DISABLED)
```

---

## Advanced Customization

### Add Voice Input (Tkinter)

```python
import speech_recognition as sr

def voice_input(self):
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        audio = recognizer.listen(source)
        text = recognizer.recognize_google(audio)
        self.input_field.insert(0, text)
```

### Add File Upload (Tkinter)

```python
from tkinter import filedialog

def upload_file(self):
    filename = filedialog.askopenfilename()
    with open(filename, 'r') as f:
        content = f.read()
        self.input_field.insert(0, f"Analyze this: {content[:500]}")
```

## Deployment

### Tkinter Desktop App

**Create Executable:**
```bash
pip install pyinstaller
pyinstaller --onefile --windowed your_app.py
# Creates standalone .exe in dist/
```

**Distribute:**
- Share the .exe file
- No Python installation needed on user's computer!

## Troubleshooting

### Tkinter Issues

**"tkinter not found" (Linux):**
```bash
sudo apt-get install python3-tk
```

**Window too small:**
```python
self.root.geometry("1000x800")  # Width x Height
```

**Blurry text on Windows:**
```python
import ctypes
ctypes.windll.shcore.SetProcessDpiAwareness(1)
```

## Tips & Best Practices

### Performance

**1. Use threading for long operations:**
```python
thread = threading.Thread(target=self.long_operation)
thread.daemon = True
thread.start()
```

**2. Use after() for UI updates:**
```python
def update():
    # Update UI elements
    self.root.after(300, update)  # Repeat every 300ms
```

### User Experience

**1. Show loading states:**
- Disable buttons while processing
- Show "Thinking..." message
- Add progress indicators

**2. Handle errors gracefully:**
- Try/catch blocks
- Show user-friendly messages
- Log errors for debugging

**3. Save conversation history:**
```python
import json

def save_history(self):
    with open('history.json', 'w') as f:
        json.dump(self.messages, f)
```

## Examples Gallery

### Minimal Tkinter (50 lines)
Simple chat window with basic styling.

### Styled Tkinter (100 lines)
Beautiful interface with custom colors and threading.

### Feature-Rich Tkinter (300 lines)
Multi-tab, settings, themes, export functionality.

### Simple Web (150 lines)
Clean, modern web interface.

### Advanced Web (400 lines)
Multiple tools, real-time updates, admin panel.

## Resources

**Tkinter:**
- Official Docs: https://docs.python.org/3/library/tkinter.html
- Real Python Tutorial: https://realpython.com/python-gui-tkinter/
- TkDocs: https://tkdocs.com/tutorial/

**Python GUI Design:**
- Tkinter Colors: https://www.tcl.tk/man/tcl8.4/TkCmd/colors.htm
- Font Configuration: https://tkdocs.com/tutorial/fonts.html

## Next Steps

1. Generate your first GUI template
2. Run it and see how it works
3. Customize colors and styling
4. Add your own features
5. Share your creation!

```bash
python create_starter.py
# Pick a model
# Choose a GUI template
# Start customizing!
```

Happy building! 🎨🚀
