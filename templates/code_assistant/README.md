# Code Assistant Template

An AI-powered coding assistant using Ollama.

## Features

- **Code Generation** - Generate code from descriptions
- **Code Explanation** - Understand what code does
- **Debugging** - Find and fix bugs
- **Code Review** - Get feedback on code quality
- **Optimization** - Improve code performance
- **Test Generation** - Create unit tests
- **Documentation** - Add docstrings and comments

## Usage

### Basic Usage

```python
from code_assistant import CodeAssistant

assistant = CodeAssistant(model="codellama")
assistant.start()

# Generate code
code = assistant.generate_code(
    "Create a function to calculate fibonacci numbers",
    language="python"
)

# Explain code
explanation = assistant.explain_code(code)

# Debug code
fix = assistant.debug_code(buggy_code, error_message)

# Review code
feedback = assistant.review_code(code)
```

### Run Interactive Mode

```bash
python code_assistant.py
```

## Commands

- `generate` - Generate code from description
- `explain` - Explain what code does
- `debug` - Debug code and find issues
- `review` - Review code for best practices
- `optimize` - Optimize code for performance
- `test` - Generate unit tests
- `document` - Add documentation
- `chat` - Free-form conversation
- `clear` - Clear conversation history
- `quit` - Exit

## Recommended Models

### Best for Code

1. **codellama** - Meta's code-specialized model
   ```bash
   ollama pull codellama
   ```

2. **deepseek-coder** - Excellent for code generation
   ```bash
   ollama pull deepseek-coder
   ```

3. **starcoder2** - Strong coding capabilities
   ```bash
   ollama pull starcoder2
   ```

### General Purpose

- **llama2** - Good all-around performance
- **mistral** - Fast and capable

## Examples

### Generate a Function

```
Command: generate
Describe: Create a binary search function
Language: python

Output: Fully implemented binary search with comments
```

### Debug Code

```
Command: debug
Enter code: [paste your code]
END
Error message: IndexError: list index out of range

Output: Identified issue and suggested fix
```

### Generate Tests

```
Command: test
Enter code: [paste your function]
END
Framework: pytest

Output: Comprehensive test cases
```

## Customization

### Use Different Models

```python
# For general coding
assistant = CodeAssistant(model="codellama")

# For specialized tasks
assistant = CodeAssistant(model="deepseek-coder")
```

### Adjust Creativity

```python
# In the ChatSession initialization:
temperature=0.1  # More deterministic (better for code)
temperature=0.5  # More creative (better for exploration)
```

## Tips

1. **Be Specific**: Provide clear, detailed descriptions
2. **Include Context**: Mention language, framework, requirements
3. **Iterate**: Use chat mode to refine solutions
4. **Review Output**: Always review generated code
5. **Test**: Test generated code before using in production

## Use Cases

- Rapid prototyping
- Learning new languages/frameworks
- Understanding legacy code
- Debugging complex issues
- Code refactoring
- Documentation generation
- Test case creation

## Requirements

- Ollama with a code model installed
- otk library
