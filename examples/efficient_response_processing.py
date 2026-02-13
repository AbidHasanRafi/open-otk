"""
Efficient Model Response Processing

This example shows how to efficiently work with different model structures
using the Ollama Toolkit, handling thinking tags, different temperatures,
and response timing automatically.

This replaces manual response cleaning with the library's built-in handlers.
"""

from otk import ChatSession, AutoModelHandler, ProcessedResponse
import ollama
import time
from typing import Optional, Dict, List, Tuple


class EfficientModelChat:
    """
    Enhanced chat interface with automatic response processing
    """
    
    def __init__(self, model: str, temperature: float = 0.7):
        """
        Initialize efficient chat
        
        Args:
            model: Model name to use
            temperature: Sampling temperature (0.0 to 1.0)
        """
        self.model = model
        self.temperature = temperature
        self.session = ChatSession(
            model=model,
            temperature=temperature,
            auto_process=True  # Automatically clean responses!
        )
        self.response_times: List[float] = []
    
    def chat(
        self,
        message: str,
        max_tokens: Optional[int] = None,
        top_p: float = 0.9,
        show_thinking: bool = False
    ) -> Dict:
        """
        Send a message and get processed response with timing
        
        Args:
            message: User message
            max_tokens: Maximum tokens to generate
            top_p: Top-p sampling parameter
            show_thinking: Whether to show thinking process
            
        Returns:
            Dictionary with response, thinking, time, and metadata
        """
        start_time = time.time()
        
        try:
            # The library handles response cleaning automatically!
            response = self.session.send(message)
            
            response_time = time.time() - start_time
            self.response_times.append(response_time)
            
            # Get thinking if available
            thinking = self.session.get_last_thinking()
            metadata = self.session.get_last_metadata()
            
            # Optionally display thinking
            if show_thinking and thinking:
                print("\n" + "=" * 50)
                print("💭 Model's Thinking Process:")
                print("=" * 50)
                for i, thought in enumerate(thinking, 1):
                    print(f"\nStep {i}:")
                    print(thought)
                print("=" * 50 + "\n")
            
            return {
                'response': response,
                'thinking': thinking,
                'response_time': response_time,
                'metadata': metadata,
                'error': None
            }
            
        except Exception as e:
            return {
                'response': f"Error: {str(e)}",
                'thinking': None,
                'response_time': time.time() - start_time,
                'metadata': None,
                'error': str(e)
            }
    
    def get_average_response_time(self) -> float:
        """Get average response time across all interactions"""
        if not self.response_times:
            return 0.0
        return sum(self.response_times) / len(self.response_times)
    
    def clear_history(self):
        """Clear conversation history"""
        self.session.clear_history()
        self.response_times = []


def demo_basic_usage():
    """Basic usage example"""
    print("\n" + "=" * 70)
    print("🚀 Demo 1: Basic Efficient Usage")
    print("=" * 70)
    
    # Create chat with any model
    chat = EfficientModelChat("llama2", temperature=0.7)
    
    # Send a message - response is automatically cleaned!
    result = chat.chat("What is Python? Give a brief answer.")
    
    print(f"\n✅ Response:\n{result['response']}")
    print(f"\n⏱️  Time: {result['response_time']:.2f}s")
    
    if result['thinking']:
        print(f"\n💭 Thinking steps: {len(result['thinking'])}")


def demo_thinking_model():
    """Demo with a thinking model like DeepSeek-R1"""
    print("\n" + "=" * 70)
    print("🧠 Demo 2: Thinking Model (DeepSeek-R1)")
    print("=" * 70)
    
    # Works with thinking models automatically!
    chat = EfficientModelChat("deepseek-r1:8b", temperature=0.8)
    
    print("\n📝 Question: Solve 234 + 567")
    result = chat.chat(
        "What is 234 + 567? Show your reasoning.",
        show_thinking=True  # Display the thinking process
    )
    
    print(f"\n✅ Clean Answer:\n{result['response']}")
    print(f"\n⏱️  Response Time: {result['response_time']:.2f}s")


def demo_multi_turn_conversation():
    """Demo multi-turn conversation with automatic cleaning"""
    print("\n" + "=" * 70)
    print("💬 Demo 3: Multi-Turn Conversation")
    print("=" * 70)
    
    chat = EfficientModelChat("llama2", temperature=0.7)
    
    questions = [
        "What is machine learning?",
        "Give me a simple example",
        "What skills do I need to learn it?"
    ]
    
    for i, question in enumerate(questions, 1):
        print(f"\n{'─' * 50}")
        print(f"Question {i}: {question}")
        print('─' * 50)
        
        result = chat.chat(question)
        print(f"Answer: {result['response']}")
        print(f"Time: {result['response_time']:.2f}s")
    
    print(f"\n📊 Average Response Time: {chat.get_average_response_time():.2f}s")


def demo_model_comparison():
    """Compare different models on the same task"""
    print("\n" + "=" * 70)
    print("⚖️  Demo 4: Model Comparison")
    print("=" * 70)
    
    models = ["llama2", "mistral"]  # Add models you have installed
    task = "Explain recursion in programming in one sentence."
    
    print(f"\n📋 Task: {task}\n")
    
    results = []
    
    for model in models:
        try:
            print(f"🤖 Testing {model}...")
            chat = EfficientModelChat(model, temperature=0.7)
            result = chat.chat(task)
            
            results.append({
                'model': model,
                'response': result['response'],
                'time': result['response_time'],
                'has_thinking': bool(result['thinking'])
            })
            
            print(f"   ✅ Response time: {result['time']:.2f}s")
            if result['thinking']:
                print(f"   💭 Used reasoning: {len(result['thinking'])} steps")
            
        except Exception as e:
            print(f"   ⚠️  Error: {e}")
    
    # Display comparison
    print("\n" + "=" * 70)
    print("📊 Comparison Results")
    print("=" * 70)
    
    for result in results:
        print(f"\n{result['model']}:")
        print(f"  Response: {result['response'][:100]}...")
        print(f"  Time: {result['time']:.2f}s")
        print(f"  Reasoning: {'Yes' if result['has_thinking'] else 'No'}")


def demo_custom_parameters():
    """Demo with custom parameters"""
    print("\n" + "=" * 70)
    print("🎛️  Demo 5: Custom Parameters")
    print("=" * 70)
    
    # Try different temperatures
    temperatures = [0.3, 0.7, 1.0]
    question = "Write a creative opening line for a story."
    
    print(f"\n📝 Question: {question}\n")
    
    for temp in temperatures:
        print(f"🌡️  Temperature: {temp}")
        chat = EfficientModelChat("llama2", temperature=temp)
        result = chat.chat(question)
        print(f"   Response: {result['response']}")
        print(f"   Time: {result['response_time']:.2f}s\n")


# The OLD WAY (manual cleaning - what you were doing before)
def old_manual_way():
    """
    This is how you had to do it manually before.
    Compare this complexity to the new way!
    """
    import re
    
    def clean_response(text):
        thinking_content = re.findall(r'<think>(.*?)</think>', text, flags=re.DOTALL)
        text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
        text = re.sub(r'^<[^>]+>\s*', '', text)
        return text.strip(), thinking_content
    
    def get_model_response(model, messages, temperature, max_tokens, top_p):
        start_time = time.time()
        try:
            response = ollama.chat(
                model=model,
                messages=messages,
                options={
                    'temperature': temperature,
                    'num_predict': max_tokens,
                    'top_p': top_p
                }
            )
            response_time = time.time() - start_time
            final_reply, thinking_process = clean_response(response.message.content)
            return final_reply, thinking_process, response_time, None
        except Exception as e:
            return f"Error: {str(e)}", [], time.time() - start_time, str(e)
    
    # Manual message management
    messages = [{"role": "user", "content": "Hello"}]
    final_reply, thinking, resp_time, error = get_model_response(
        "llama2", messages, 0.7, None, 0.9
    )
    
    return final_reply, thinking, resp_time


# The NEW WAY (automatic with library)
def new_library_way():
    """
    The new efficient way using the library.
    Much simpler and cleaner!
    """
    chat = EfficientModelChat("llama2", temperature=0.7)
    result = chat.chat("Hello")
    
    return result['response'], result['thinking'], result['response_time']


def main():
    """Run all demos"""
    print("\n" + "=" * 70)
    print("🦙 Efficient Model Response Processing with Ollama Toolkit")
    print("=" * 70)
    print("\n✨ All response cleaning happens automatically!")
    print("   No manual regex patterns needed!")
    print("   Works with any model structure!")
    
    try:
        # Run demos
        demo_basic_usage()
        
        print("\n\n" + "=" * 70)
        print("⚠️  The following demos require specific models installed:")
        print("=" * 70)
        
        input("\nPress Enter to continue (or Ctrl+C to exit)...")
        
        # These require actual models
        demo_thinking_model()
        demo_multi_turn_conversation()
        demo_model_comparison()
        demo_custom_parameters()
        
        # Show the difference
        print("\n" + "=" * 70)
        print("📊 OLD vs NEW Comparison")
        print("=" * 70)
        print("\n🟥 OLD WAY (Manual):")
        print("   • Write regex patterns for each model type")
        print("   • Manually manage message arrays")
        print("   • Handle errors for each model differently")
        print("   • Complex, error-prone code")
        print("\n🟩 NEW WAY (Library):")
        print("   • Automatic detection and cleaning")
        print("   • Simple API for all models")
        print("   • Consistent error handling")
        print("   • Clean, maintainable code")
        
    except KeyboardInterrupt:
        print("\n\n👋 Demo interrupted")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure:")
        print("1. Ollama is running")
        print("2. Models are installed: ollama pull <model-name>")
    
    print("\n" + "=" * 70)
    print("✅ All Done!")
    print("=" * 70)
    print("\n🚀 Start using EfficientModelChat in your projects!")
    print("   It's that simple! 😊")


if __name__ == "__main__":
    main()
