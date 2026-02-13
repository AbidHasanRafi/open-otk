"""
Simple Chatbot Template

A basic chatbot using Ollama Toolkit with a clean interface.
"""

from otk import ChatSession, ModelManager

class SimpleChatbot:
    def __init__(self, model=None):
        """Initialize the chatbot"""
        self.model = model
        self.session = None
        self.manager = ModelManager()
        
    def setup(self):
        """Setup the chatbot"""
        print("🤖 Simple Chatbot")
        print("=" * 50)
        
        # Auto-detect available models if none specified
        if self.model is None:
            available_models = self.manager.list_models()
            if not available_models:
                print("❌ No models installed!")
                print("\nPlease install a model first:")
                print("  ollama pull qwen2:0.5b    # Small and fast")
                print("  ollama pull llama2        # General purpose")
                print("  ollama pull mistral       # Powerful")
                return False
            
            # Use the first available model
            self.model = available_models[0]['name']
            print(f"✓ Auto-selected model: {self.model}")
            
            # Show other available models
            if len(available_models) > 1:
                print(f"  Other available models: {', '.join([m['name'] for m in available_models[1:4]])}")
        else:
            # Check if specified model exists
            if not self.manager.model_exists(self.model):
                print(f"⚠️  Model '{self.model}' not found.")
                
                # Show available models
                available_models = self.manager.list_models()
                if available_models:
                    print(f"\nAvailable models:")
                    for m in available_models:
                        print(f"  • {m['name']}")
                    
                    # Offer to use first available
                    use_available = input(f"\nUse '{available_models[0]['name']}' instead? (y/n): ").strip().lower()
                    if use_available == 'y':
                        self.model = available_models[0]['name']
                        print(f"✓ Using {self.model}")
                    else:
                        return False
                else:
                    print("\nNo models installed. Please install one:")
                    print("  ollama pull qwen2:0.5b")
                    return False
        
        # Create chat session
        system_message = """You are a helpful, friendly chatbot. 
        Provide clear, concise answers and be conversational."""
        
        self.session = ChatSession(
            model=self.model,
            system_message=system_message,
            temperature=0.7
        )
        
        print(f"✓ Chatbot ready! Using model: {self.model}")
        print("=" * 50)
        print("Commands:")
        print("  'quit' or 'exit' - Exit the chatbot")
        print("  'clear' - Clear conversation history")
        print("  'save' - Save conversation")
        print("=" * 50)
    
    def run(self):
        """Run the chatbot"""
        if self.setup() == False:
            return
        
        while True:
            try:
                # Get user input
                user_input = input("\n👤 You: ").strip()
                
                if not user_input:
                    continue
                
                # Handle commands
                if user_input.lower() in ['quit', 'exit']:
                    print("\n👋 Goodbye!")
                    break
                
                if user_input.lower() == 'clear':
                    self.session.clear_history()
                    print("✓ Conversation cleared!")
                    continue
                
                if user_input.lower() == 'save':
                    filename = input("Enter filename (default: chat_history.json): ").strip()
                    if not filename:
                        filename = "chat_history.json"
                    self.session.export_history(filename)
                    print(f"✓ Conversation saved to {filename}")
                    continue
                
                # Get response
                print("\n🤖 Bot: ", end='', flush=True)
                
                for chunk in self.session.send_stream(user_input):
                    print(chunk, end='', flush=True)
                
                print()  # New line
                
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")


def main():
    # Auto-detects installed models, or specify one:
    # chatbot = SimpleChatbot(model="qwen2:0.5b")
    chatbot = SimpleChatbot()  # Auto-detect
    chatbot.run()


if __name__ == "__main__":
    main()
