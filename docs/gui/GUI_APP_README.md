# 🎨 GUI Template Generator

A powerful GUI application for browsing, managing, and generating Ollama templates!

## Features

### 🌐 Browse Available Models
- **Web Scraping**: Automatically scrapes ollama.com to show all available models
- **Search & Filter**: Quickly find models by name
- **One-Click Install**: Install any model directly from the browser
- **Live Updates**: Refresh to see the latest models

### 🔧 Manage Installed Models
- **List All Models**: See all your installed models with sizes and dates
- **Run Models**: Launch models directly in terminal
- **Delete Models**: Remove unused models to free up space
- **Model Info**: View detailed information about any model

### ✨ Generate Templates
- **7 Template Types**:
  - Simple Chat - Basic conversational interface
  - Custom Model - Customizable with hooks
  - Streaming Chat - Real-time responses
  - Experimentation - Test different settings
  - Integration - Integrate into your app
  - Tkinter GUI - Desktop GUI interface
  - Tkinter Advanced - Advanced GUI with features

- **Model Selection**: Choose from installed models
- **File Browser**: Save templates anywhere
- **Instant Generation**: Creates working code in seconds

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Or install manually
pip install ollama requests beautifulsoup4
```

## Usage

### Launch the GUI

```bash
python create_starter_gui.py
```

### Quick Start

1. **First Time Setup**:
   - Go to "🌐 Browse Models" tab
   - Click "🔄 Refresh" to load available models
   - Select a model (e.g., `qwen2:0.5b` for quick testing)
   - Click "📥 Install Selected Model"
   - Wait for installation to complete

2. **Generate Your First Template**:
   - Go to "✨ Generate Template" tab
   - Select your installed model
   - Choose a template type
   - Enter a filename
   - Click "🚀 Generate Template"

3. **Run Your Template**:
   ```bash
   python my_ollama_app.py
   ```

## Screenshots

### Browse Models Tab
```
┌─────────────────────────────────────────────────────────────┐
│              🌐 Browse Available Models                      │
├─────────────────────────────────────────────────────────────┤
│  🔍 Search: [llama________________] [🔄 Refresh]            │
├─────────────────────────────────────────────────────────────┤
│  • llama2                                                    │
│  • llama2:13b                                                │
│  • llama3                                                    │
│  • mistral                                                   │
│  • qwen2:0.5b                                                │
│  • gemma:2b                                                  │
│  • deepseek-r1:1.5b                                          │
│  • codellama                                                 │
│  ...                                                         │
├─────────────────────────────────────────────────────────────┤
│              [📥 Install Selected Model]                     │
│  ✅ Found 127 models from ollama.com                        │
└─────────────────────────────────────────────────────────────┘
```

### Manage Models Tab
```
┌─────────────────────────────────────────────────────────────┐
│               🔧 Manage Installed Models                     │
├─────────────────────────────────────────────────────────────┤
│  Model Name          │ Size      │ Last Modified             │
│  ────────────────────┼───────────┼──────────────────────────│
│  qwen2:0.5b         │ 335.85 MB │ 2026-02-10 14:23:11      │
│  llama2             │ 3.8 GB    │ 2026-02-09 10:15:42      │
│  deepseek-r1:1.5b   │ 1.04 GB   │ 2026-02-08 16:45:23      │
├─────────────────────────────────────────────────────────────┤
│  [🔄 Refresh] [▶️  Run] [🗑️  Delete] [ℹ️  Info]            │
│  ✅ 3 models installed                                      │
└─────────────────────────────────────────────────────────────┘
```

### Generate Template Tab
```
┌─────────────────────────────────────────────────────────────┐
│             ✨ Generate Starter Templates                    │
├─────────────────────────────────────────────────────────────┤
│  1️⃣  Select Model                                           │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ qwen2:0.5b ▼                                          │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                              │
│  2️⃣  Select Template Type                                   │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ ⚪ Simple Chat - Basic conversational interface      │  │
│  │ ⚪ Custom Model - Customizable with hooks            │  │
│  │ ⚪ Streaming Chat - Real-time responses              │  │
│  │ ⚪ Experimentation - Test different settings         │  │
│  │ ⚪ Integration - Integrate into your app             │  │
│  │ ⚪ Tkinter GUI - 🎨 Desktop GUI                      │  │
│  │ ⚫ Tkinter Advanced - 🎨 Advanced GUI                │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                              │
│  3️⃣  Output Filename                                        │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ my_ollama_app.py                        [📁 Browse]  │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                              │
│               [🚀 Generate Template]                         │
│  ✅ Ready to generate!                                      │
└─────────────────────────────────────────────────────────────┘
```

## Features in Detail

### Model Browser
- **Automatic Scraping**: Fetches all available models from ollama.com
- **Smart Search**: Filter models as you type
- **Pagination**: Loads multiple pages of results
- **Direct Install**: Install any model with one click

### Model Manager
- **Complete Control**: View, run, delete, and inspect models
- **Terminal Integration**: Opens models in native terminal
- **Safe Delete**: Confirmation before removing models
- **Detailed Info**: View model metadata and configuration

### Template Generator
- **All Template Types**: Access all 7 template types
- **Smart Defaults**: Sensible defaults for quick start
- **File Browser**: Choose save location easily
- **Instant Feedback**: Shows generation status and results

## Ollama Commands Integrated

The GUI provides easy access to these Ollama commands:

```bash
# Browsing
ollama search <query>      # (via web scraping)

# Management
ollama list                # View installed models
ollama pull <model>        # Install model
ollama rm <model>          # Delete model
ollama show <model>        # Model information
ollama run <model>         # Run model in terminal

# All accessible through the GUI!
```

## Advantages Over CLI

### CLI Version (`create_starter.py`)
```bash
$ python create_starter.py
# Text-based prompts
# Linear workflow
# Type everything manually
```

### GUI Version (`create_starter_gui.py`)
```bash
$ python create_starter_gui.py
# Beautiful visual interface
# Tab-based workflow
# Click and select
# Browse available models from web
# Manage models visually
# Multiple actions at once
```

## Tips & Tricks

### Fast Model Testing
1. Install `qwen2:0.5b` (smallest, fastest)
2. Generate a "Simple Chat" template
3. Test it immediately
4. Then try larger models if needed

### Batch Operations
- Keep the GUI open while models install
- Browse available models in one tab
- Manage installations in another
- Generate templates in the third

### Model Discovery
- Use search to find specific types (e.g., "code", "llama", "mistral")
- Sort by size if storage is limited
- Read model descriptions on ollama.com

## Troubleshooting

### "No models found"
- Install a model from the Browse tab
- Or run: `ollama pull qwen2:0.5b`

### "Ollama not running"
- Start Ollama: Download from https://ollama.ai
- Check if running: `ollama list`

### "Scraping failed"
- Check internet connection
- Try refreshing again
- Or install models manually: `ollama pull <name>`

### "Dependencies missing"
```bash
pip install requests beautifulsoup4
```

## Technical Details

- **Framework**: Pure Python Tkinter (built-in)
- **Threading**: Non-blocking UI during operations
- **Web Scraping**: Beautiful Soup 4
- **Process Management**: subprocess for Ollama commands
- **Cross-Platform**: Works on Windows, macOS, Linux

## Color Scheme

The GUI uses a modern dark theme:
- Background: Dark blue-grey (`#1a1a2e`)
- Accent: Cyan (`#00d4ff`)
- Success: Green (`#00ff88`)
- Warning: Orange (`#ffaa00`)
- Error: Red (`#ff4444`)

## Future Enhancements

Potential additions:
- [ ] Model size filtering
- [ ] Category-based browsing
- [ ] Favorites/bookmarks
- [ ] Model comparison
- [ ] Download progress bars
- [ ] Template previews
- [ ] Custom template editor
- [ ] Settings panel

## Comparison with CLI

| Feature | CLI | GUI |
|---------|-----|-----|
| Browse models | ❌ No | ✅ Yes (web scraping) |
| Search models | ❌ No | ✅ Yes |
| Visual model list | ❌ No | ✅ Yes |
| Run models | ❌ External | ✅ Integrated |
| Delete models | ❌ External | ✅ One-click |
| Model info | ❌ External | ✅ Built-in |
| Template generation | ✅ Yes | ✅ Yes |
| File browser | ❌ No | ✅ Yes |
| Multi-tasking | ❌ No | ✅ Tabs |
| Visual feedback | ❌ Text only | ✅ Colors & icons |

## Why This GUI?

### Philosophy
- **Custom-built**: No Streamlit, Gradio, or Flask
- **Zero dependencies**: Only Tkinter (built-in) + web scraping libs
- **Full control**: Complete customization possible
- **Fast**: No web server overhead
- **Portable**: Runs anywhere Python runs

### Design Decisions
- **Tab-based**: Logical separation of concerns
- **Dark theme**: Easy on the eyes
- **Icons**: Visual clarity
- **Threaded**: Non-blocking operations
- **Status feedback**: Always know what's happening

## Contributing

Want to enhance the GUI? Ideas:
1. Add more Ollama commands
2. Improve the scraper (handle more pages, filters)
3. Add template preview before generation
4. Create a settings panel
5. Add keyboard shortcuts
6. Implement drag-and-drop

## License

Same as the main project.

---

**Made with ❤️  using pure Python Tkinter!**

No frameworks, no dependencies (except scraping), just clean custom code! 🚀
