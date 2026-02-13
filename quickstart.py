"""
Quick Start Script - Test your Ollama Toolkit installation

This script checks if everything is set up correctly.
"""

from otk import OllamaClient, ModelManager

def main():
    print("🦙 Ollama Toolkit - Quick Start Test")
    print("=" * 50)
    
    # Check connection
    print("\n1. Checking Ollama connection...")
    client = OllamaClient()
    
    if not client.is_running():
        print("❌ Ollama is not running!")
        print("\nPlease start Ollama:")
        print("  - On macOS/Linux: ollama serve")
        print("  - On Windows: Ollama should start automatically")
        return
    
    print("✓ Connected to Ollama successfully!")
    
    # Check models
    print("\n2. Checking installed models...")
    manager = ModelManager()
    models = manager.list_models()
    
    if not models:
        print("❌ No models installed!")
        print("\nPlease install at least one model:")
        print("  ollama pull llama2")
        return
    
    print(f"✓ Found {len(models)} model(s):")
    for model in models[:5]:  # Show first 5
        print(f"  • {model['name']} ({model['size']})")
    
    # Test generation
    print("\n3. Testing text generation...")
    test_model = models[0]['name']
    print(f"Using model: {test_model}")
    
    try:
        response = client.generate(
            model=test_model,
            prompt="Say 'Hello, Ollama Toolkit!' and nothing else.",
            temperature=0.1
        )
        print(f"✓ Response: {response[:100]}")
    except Exception as e:
        print(f"❌ Error: {e}")
        return
    
    # Success!
    print("\n" + "=" * 50)
    print("✅ Everything is working correctly!")
    print("\nNext steps:")
    print("  1. Try examples: cd examples && python simple_chat.py")
    print("  2. Try templates: cd templates/chatbot && python simple_chatbot.py")
    print("  3. Read the docs: README.md")
    print("=" * 50)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nPlease make sure:")
        print("  1. Ollama is installed and running")
        print("  2. You have at least one model: ollama pull llama2")
        print("  3. Dependencies are installed: pip install -r requirements.txt")
