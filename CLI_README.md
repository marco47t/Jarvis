# Jarvis CLI - Interactive Command Line Interface

## Overview

Jarvis CLI is a colorful, animated command-line interface for testing all Jarvis features without launching the web interface. It provides an interactive menu-driven experience with beautiful formatting, progress indicators, and real-time feedback.

## Features

### 💬 **Chat Mode**
- Direct conversation with the AI
- Real-time responses with loading animations
- Markdown-formatted output for better readability

### 🎯 **Agent Mode**
- Execute complex tasks autonomously
- Watch the agent work with progress indicators
- Get detailed task completion reports

### 🌤️ **Weather Information**
- View current weather conditions
- Beautifully formatted weather tables
- Real-time updates from WeatherBot

### 📊 **System Monitoring**
- Check system health status
- View suggested actions and alerts
- Monitor resource usage

### 🌅 **Morning Briefing**
- Generate personalized daily briefings
- Get AI-powered action plans
- Voice synthesis support

### 💾 **Chat History**
- Browse previous chat sessions
- Load and continue past conversations
- Organized by date and title

### 🔧 **Settings & Configuration**
- View current AI model settings
- Check configured parameters
- Monitor system configuration

### 📋 **User Profile**
- Display user preferences
- View personalization settings
- Check profile completeness

### 🛠️ **Tool Testing**
- Test individual tools directly
- Verify tool availability
- Debug tool functionality

## Installation

1. **Install CLI dependencies:**
   ```bash
   pip install -r requirements-cli.txt
   ```

2. **Ensure main Jarvis dependencies are installed:**
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Starting the CLI

```bash
python cli.py
```

### Navigation

- Use number keys (0-9) to select menu options
- Type 'back' or 'exit' to return to the main menu from any feature
- Press Ctrl+C to interrupt long-running operations
- Confirm exit when prompted

### Visual Features

#### ✨ **Colorful Interface**
- Cyan for headers and system messages
- Green for success states
- Yellow for warnings and Jarvis responses
- Red for errors
- Color-coded tables and panels

#### 🎨 **Animations**
- Spinning progress indicators during processing
- Smooth transitions between screens
- Loading animations for API calls
- Real-time status updates

#### 📊 **Rich Formatting**
- Tables with borders for structured data
- Panels for important information
- Markdown rendering for AI responses
- Syntax highlighting where applicable

## Key Components

### Main Menu
The central hub displaying all available features in a formatted table with descriptions.

### Chat Interface
- Direct input prompt with color coding
- Formatted response panels
- Markdown support for rich text
- Conversation history maintained

### Progress Indicators
- Spinner animations for background tasks
- Status messages for long operations
- Success/failure visual feedback

### Data Tables
- Weather information display
- System status overview
- Chat history listing
- Settings configuration

## Requirements

### Python Packages
- `colorama` - Cross-platform colored terminal text
- `rich` - Rich text and beautiful formatting
- `keyboard` - Keyboard event handling (optional)
- `prompt-toolkit` - Advanced input handling

### System Requirements
- Python 3.8+
- Windows/Linux/macOS
- Terminal with Unicode support
- Terminal with color support (most modern terminals)

## Keyboard Shortcuts

- **Enter**: Submit input or continue
- **Ctrl+C**: Interrupt current operation
- **Ctrl+D**: Exit (on Unix-like systems)
- Type `back`, `exit`, or `quit` to return to main menu

## Features Showcase

### Chat Example
```
┌──────────────────────────────┐
│ Chat Mode Activated      │
│                          │
│ Type your messages...    │
└──────────────────────────────┘

You: What's the weather like?

⏳ Jarvis is thinking...

┌─── Jarvis ───────────────┐
│ The current temperature  │
│ is 22°C with clear      │
│ skies.                   │
└─────────────────────────┘
```

### Weather Display
```
╭───── Current Weather ─────╮
│ Parameter    │ Value        │
├──────────────┼──────────────┤
│ Temperature  │ 22°C        │
│ Condition    │ Clear        │
│ Humidity     │ 65%          │
╰──────────────┴──────────────╯
```

## Troubleshooting

### Colors Not Showing
- Ensure your terminal supports ANSI colors
- On Windows, use Windows Terminal or update cmd.exe
- Try setting `FORCE_COLOR=1` environment variable

### Import Errors
- Verify all dependencies are installed: `pip install -r requirements-cli.txt`
- Check Python version: `python --version` (3.8+ required)

### Keyboard Module Issues
- On Linux, may require root privileges or special permissions
- Can be disabled if causing issues (remove keyboard import)

### Display Issues
- Use a terminal with Unicode support
- Increase terminal width for better table display
- Some terminals may not support all box-drawing characters

## Tips for Best Experience

1. **Terminal Size**: Use a terminal window at least 80 characters wide
2. **Font**: Use a monospace font for proper alignment
3. **Color Scheme**: Dark terminal backgrounds work best
4. **Modern Terminal**: Use Windows Terminal, iTerm2, or similar modern terminals
5. **Full Screen**: Run in full-screen mode for immersive experience

## Differences from Web UI

| Feature | CLI | Web UI |
|---------|-----|--------|
| Voice Input | ❌ No | ✔️ Yes |
| Visual Queries | ❌ No | ✔️ Yes |
| Hotkeys | ❌ Limited | ✔️ Yes |
| Portability | ✔️ High | ❌ Browser Required |
| Speed | ✔️ Fast | ✔️ Fast |
| Testing | ✔️ Excellent | ✔️ Good |
| Animations | ✔️ Text-based | ✔️ Rich |

## Development

### Adding New Features

To add a new menu option:

1. Add entry to `display_menu()` table
2. Create handler method (e.g., `def my_feature(self)`)
3. Add choice handler in `run()` method
4. Implement feature logic with rich formatting

### Styling Guidelines

- Use `[cyan]` for prompts and headers
- Use `[green]` for success messages
- Use `[yellow]` for warnings and Jarvis responses
- Use `[red]` for errors
- Always provide progress feedback for long operations
- Use Rich panels for important information
- Use tables for structured data

## License

Same as main Jarvis project.

## Contributing

Contributions welcome! Please ensure:
- Colors work across platforms
- Progress indicators for operations > 1 second
- Error handling with user-friendly messages
- Consistent styling with existing code

## Support

For issues specific to the CLI:
1. Check terminal compatibility
2. Verify all dependencies installed
3. Review terminal size and settings
4. Check Python version compatibility

---

**Enjoy using Jarvis CLI!** 🚀
