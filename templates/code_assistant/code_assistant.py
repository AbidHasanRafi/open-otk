"""
Code Assistant Template

An AI-powered code assistant using Ollama for code generation,
explanation, debugging, and review.
"""

from otk import ChatSession

class CodeAssistant:
    def __init__(self, model=None):
        """
        Initialize the code assistant
        
        Args:
            model: Model to use (auto-detects coding models if None)
        """
        from otk import ModelManager
        
        # Auto-detect best model for coding
        if model is None:
            manager = ModelManager()
            available = manager.list_models()
            
            if not available:
                raise ValueError("No models installed. Please run: ollama pull qwen2:0.5b")
            
            # Prefer coding models
            coding_keywords = ['code', 'coder', 'deepseek', 'qwen']
            coding_models = [m['name'] for m in available 
                           if any(kw in m['name'].lower() for kw in coding_keywords)]
            
            if coding_models:
                self.model = coding_models[0]
                print(f"✓ Auto-selected coding model: {self.model}")
            else:
                self.model = available[0]['name']
                print(f"✓ Using model: {self.model}")
                print(f"   Tip: For better coding results, try: ollama pull deepseek-r1:1.5b")
        else:
            self.model = model
        
        self.session = None
    
    def start(self):
        """Start the code assistant session"""
        system_message = """You are an expert programming assistant.
        Help users with:
        - Writing code
        - Explaining code
        - Debugging issues
        - Code reviews
        - Best practices
        
        Provide clear, well-commented code and explanations."""
        
        self.session = ChatSession(
            model=self.model,
            system_message=system_message,
            temperature=0.3
        )
        
        print(f"✓ Code Assistant ready! Using model: {self.model}")
    
    def generate_code(self, description: str, language: str = "python") -> str:
        """Generate code from description"""
        prompt = f"""Generate {language} code for the following task:

{description}

Provide clean, well-commented code."""
        
        return self.session.send(prompt)
    
    def explain_code(self, code: str) -> str:
        """Explain what code does"""
        prompt = f"""Explain what this code does in simple terms:

```
{code}
```

Provide a clear explanation."""
        
        return self.session.send(prompt)
    
    def debug_code(self, code: str, error: str = None) -> str:
        """Help debug code"""
        if error:
            prompt = f"""This code has an error:

```
{code}
```

Error message:
{error}

Identify the issue and provide a fix."""
        else:
            prompt = f"""Review this code for potential bugs:

```
{code}
```

Identify any issues and suggest fixes."""
        
        return self.session.send(prompt)
    
    def review_code(self, code: str) -> str:
        """Review code for best practices"""
        prompt = f"""Review this code for:
- Code quality
- Best practices
- Performance
- Security
- Readability

Code:
```
{code}
```

Provide constructive feedback."""
        
        return self.session.send(prompt)
    
    def optimize_code(self, code: str) -> str:
        """Suggest optimizations"""
        prompt = f"""Optimize this code for better performance:

```
{code}
```

Provide optimized version with explanations."""
        
        return self.session.send(prompt)
    
    def add_tests(self, code: str, framework: str = "pytest") -> str:
        """Generate unit tests"""
        prompt = f"""Generate unit tests for this code using {framework}:

```
{code}
```

Provide comprehensive test cases."""
        
        return self.session.send(prompt)
    
    def document_code(self, code: str) -> str:
        """Add documentation to code"""
        prompt = f"""Add comprehensive documentation to this code:

```
{code}
```

Include docstrings, comments, and type hints where appropriate."""
        
        return self.session.send(prompt)


def main():
    """Interactive code assistant"""
    print("💻 Code Assistant")
    print("=" * 50)
    
    try:
        assistant = CodeAssistant()  # Auto-detect best coding model
        assistant.start()
    except ValueError as e:
        print(f"\n❌ {e}")
        return
    
    print("\n" + "=" * 50)
    print("Commands:")
    print("  generate - Generate code from description")
    print("  explain - Explain code")
    print("  debug - Debug code")
    print("  review - Review code")
    print("  optimize - Optimize code")
    print("  test - Generate unit tests")
    print("  document - Add documentation")
    print("  chat - Free-form chat")
    print("  clear - Clear conversation")
    print("  quit - Exit")
    print("=" * 50)
    
    while True:
        try:
            command = input("\n💻 Command: ").strip().lower()
            
            if command == 'quit':
                print("\n👋 Goodbye!")
                break
            
            if command == 'clear':
                assistant.session.clear_history()
                print("✓ Conversation cleared!")
                continue
            
            if command == 'generate':
                description = input("Describe what you want to build: ").strip()
                language = input("Language (default: python): ").strip() or "python"
                
                print("\n🤖 Generating code...\n")
                response = assistant.generate_code(description, language)
                print(response)
            
            elif command == 'explain':
                print("Enter code (type 'END' on a new line when done):")
                code_lines = []
                while True:
                    line = input()
                    if line == 'END':
                        break
                    code_lines.append(line)
                code = '\n'.join(code_lines)
                
                print("\n🤖 Explanation:\n")
                response = assistant.explain_code(code)
                print(response)
            
            elif command == 'debug':
                print("Enter code (type 'END' on a new line when done):")
                code_lines = []
                while True:
                    line = input()
                    if line == 'END':
                        break
                    code_lines.append(line)
                code = '\n'.join(code_lines)
                
                error = input("Error message (optional): ").strip()
                
                print("\n🤖 Debugging...\n")
                response = assistant.debug_code(code, error if error else None)
                print(response)
            
            elif command == 'review':
                print("Enter code (type 'END' on a new line when done):")
                code_lines = []
                while True:
                    line = input()
                    if line == 'END':
                        break
                    code_lines.append(line)
                code = '\n'.join(code_lines)
                
                print("\n🤖 Code Review:\n")
                response = assistant.review_code(code)
                print(response)
            
            elif command == 'optimize':
                print("Enter code (type 'END' on a new line when done):")
                code_lines = []
                while True:
                    line = input()
                    if line == 'END':
                        break
                    code_lines.append(line)
                code = '\n'.join(code_lines)
                
                print("\n🤖 Optimizing...\n")
                response = assistant.optimize_code(code)
                print(response)
            
            elif command == 'test':
                print("Enter code (type 'END' on a new line when done):")
                code_lines = []
                while True:
                    line = input()
                    if line == 'END':
                        break
                    code_lines.append(line)
                code = '\n'.join(code_lines)
                
                framework = input("Test framework (default: pytest): ").strip() or "pytest"
                
                print("\n🤖 Generating tests...\n")
                response = assistant.add_tests(code, framework)
                print(response)
            
            elif command == 'document':
                print("Enter code (type 'END' on a new line when done):")
                code_lines = []
                while True:
                    line = input()
                    if line == 'END':
                        break
                    code_lines.append(line)
                code = '\n'.join(code_lines)
                
                print("\n🤖 Adding documentation...\n")
                response = assistant.document_code(code)
                print(response)
            
            elif command == 'chat':
                message = input("Your message: ").strip()
                
                print("\n🤖 Response:\n")
                response = assistant.session.send(message)
                print(response)
            
            else:
                print("❌ Invalid command")
        
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()
