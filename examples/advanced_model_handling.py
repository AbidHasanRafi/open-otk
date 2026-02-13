"""
Multi-Model Response Handling Demo

This example demonstrates how to work with different Ollama models
that may have different response formats (like thinking tags, code blocks, etc.).

The library automatically handles these differences!
"""

from otk import (
    ChatSession,
    AutoModelHandler,
    ModelResponseHandler,
    ModelType,
    clean_thinking_tags,
    auto_clean_response
)
import time


def demo_thinking_model():
    """
    Demo working with models that show reasoning/thinking
    (e.g., DeepSeek-R1, Qwen with reasoning)
    """
    print("\n" + "=" * 70)
    print("🧠 DEMO 1: Working with Thinking Models (e.g., DeepSeek-R1)")
    print("=" * 70)
    
    # AUTO-PROCESSING: The library automatically detects and cleans responses
    session = ChatSession(
        "deepseek-r1:8b",  # or "qwen2.5" or any thinking model you have
        system_message="You are a helpful assistant",
        auto_process=True  # This is on by default!
    )
    
    print("\n📝 Asking a reasoning question...")
    response = session.send("Why is the sky blue? Explain in simple terms.")
    
    print(f"\n✅ Clean Response:\n{response}")
    
    # Get the thinking process if available
    thinking = session.get_last_thinking()
    if thinking:
        print(f"\n💭 Model's Thinking Process:")
        for i, thought in enumerate(thinking, 1):
            print(f"   Step {i}: {thought[:100]}..." if len(thought) > 100 else f"   Step {i}: {thought}")
    
    # Get metadata
    metadata = session.get_last_metadata()
    if metadata:
        print(f"\n📊 Metadata: {metadata}")


def demo_manual_cleaning():
    """
    Demo manual response cleaning for custom scenarios
    """
    print("\n" + "=" * 70)
    print("🛠️  DEMO 2: Manual Response Cleaning")
    print("=" * 70)
    
    # Simulate a raw response with thinking tags
    raw_response = """<think>
Let me analyze this problem step by step.
First, I need to understand what the user is asking...
The answer involves physics and atmospheric science.
</think>

The sky appears blue because of a phenomenon called Rayleigh scattering. 
When sunlight enters Earth's atmosphere, it collides with air molecules. 
Blue light has a shorter wavelength and scatters more easily than other colors, 
making the sky appear blue to our eyes.
"""
    
    print(f"\n📄 Raw Response:\n{raw_response[:200]}...")
    
    # Method 1: Quick utility function
    clean_text, thinking_blocks = clean_thinking_tags(raw_response)
    print(f"\n✨ Cleaned (Quick Method):\n{clean_text}")
    print(f"\n💭 Extracted Thinking: {len(thinking_blocks)} block(s)")
    
    # Method 2: Using handler directly
    handler = ModelResponseHandler(ModelType.THINKING)
    processed = handler.process(raw_response)
    print(f"\n✨ Cleaned (Handler):\n{processed.content}")
    print(f"💭 Thinking blocks: {len(processed.thinking) if processed.thinking else 0}")


def demo_auto_handler():
    """
    Demo automatic model detection and response handling
    """
    print("\n" + "=" * 70)
    print("🤖 DEMO 3: Automatic Model Detection")
    print("=" * 70)
    
    auto_handler = AutoModelHandler()
    
    # Different models, different formats
    test_cases = [
        {
            "model": "deepseek-r1:8b",
            "response": "<think>reasoning here</think>This is the answer",
            "description": "Thinking model"
        },
        {
            "model": "llama2",
            "response": "This is a standard response",
            "description": "Standard model"
        },
        {
            "model": "codellama",
            "response": "Here's the code:\n```python\nprint('hello')\n```",
            "description": "Code model"
        }
    ]
    
    for test in test_cases:
        print(f"\n🔍 Testing: {test['model']} ({test['description']})")
        print(f"   Raw: {test['response'][:50]}...")
        
        processed = auto_handler.process_response(test['response'], test['model'])
        print(f"   ✅ Processed: {processed.content[:50]}...")
        print(f"   📊 Type: {processed.metadata.get('model_type', 'unknown')}")


def demo_model_comparison():
    """
    Demo comparing responses from different models
    """
    print("\n" + "=" * 70)
    print("⚖️  DEMO 4: Multi-Model Comparison")
    print("=" * 70)
    
    # You can compare different models easily
    models_to_test = ["llama2", "deepseek-r1:8b"]  # Add models you have installed
    question = "What is 15 * 24?"
    
    print(f"\n❓ Question: {question}\n")
    
    for model in models_to_test:
        try:
            print(f"🤖 {model}:")
            start_time = time.time()
            
            session = ChatSession(model, auto_process=True)
            response = session.send(question)
            
            elapsed = time.time() - start_time
            
            print(f"   Answer: {response}")
            print(f"   Time: {elapsed:.2f}s")
            
            # Show thinking if available
            thinking = session.get_last_thinking()
            if thinking:
                print(f"   💭 Used reasoning: {len(thinking)} step(s)")
            
            print()
            
        except Exception as e:
            print(f"   ⚠️  Error: {e}")
            print(f"   (Make sure {model} is installed: ollama pull {model})\n")


def demo_custom_response_handler():
    """
    Demo creating a custom response handler for special formats
    """
    print("\n" + "=" * 70)
    print("🎨 DEMO 5: Custom Response Handler")
    print("=" * 70)
    
    # Create a custom handler for extracting specific patterns
    custom_patterns = {
        'confidence': r'Confidence: (\d+)%',
        'sources': r'Source: (.*?)(?:\n|$)'
    }
    
    handler = ModelResponseHandler(ModelType.CUSTOM, custom_patterns=custom_patterns)
    
    # Simulate a response with custom format
    raw = """Confidence: 95%
Source: Wikipedia
Source: Research Paper

The answer is: Python is a high-level programming language."""
    
    print(f"\n📄 Raw Response:\n{raw}\n")
    
    processed = handler.process(raw)
    print(f"✨ Cleaned:\n{processed.content}\n")
    print(f"📊 Extracted Data:")
    if processed.metadata and 'extracted' in processed.metadata:
        for key, values in processed.metadata['extracted'].items():
            print(f"   {key}: {values}")


def main():
    """Run all demos"""
    print("\n" + "=" * 70)
    print("🦙 Ollama Toolkit - Multi-Model Response Handling Demo")
    print("=" * 70)
    print("\nThis demo shows how the library handles different model formats automatically!")
    print("\n⚠️  Note: Some demos require specific models to be installed.")
    print("   Run 'ollama pull <model-name>' to install models.")
    
    try:
        # Run demos that don't require actual models
        demo_manual_cleaning()
        demo_auto_handler()
        demo_custom_response_handler()
        
        # These require actual models - will show errors if not available
        print("\n\n" + "=" * 70)
        print("🔴 The following demos require actual Ollama models installed:")
        print("=" * 70)
        
        input("\nPress Enter to continue with live model demos (or Ctrl+C to exit)...")
        
        demo_thinking_model()
        demo_model_comparison()
        
    except KeyboardInterrupt:
        print("\n\n👋 Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure:")
        print("1. Ollama is installed and running")
        print("2. You have models installed (ollama pull llama2)")
    
    print("\n" + "=" * 70)
    print("✅ Demo Complete!")
    print("=" * 70)
    print("\nKey Takeaways:")
    print("• The library automatically handles different model formats")
    print("• Use auto_process=True (default) for automatic cleaning")
    print("• Access thinking/reasoning with get_last_thinking()")
    print("• Create custom handlers for special formats")
    print("\nHappy coding! 🚀")


if __name__ == "__main__":
    main()
