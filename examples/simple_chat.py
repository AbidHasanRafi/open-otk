"""
Simple Chat Example - Basic conversation with an Ollama model

This example shows how to have a simple conversation with a model.
"""

from otk import OllamaClient

def main():
    # Initialize the client
    client = OllamaClient()
    
    # Check if Ollama is running
    if not client.is_running():
        print("❌ Ollama is not running. Please start Ollama first.")
        return
    
    print("✓ Connected to Ollama")
    
    # Model to use
    model = "llama2"
    
    # Simple generation
    print(f"\n🤖 Using model: {model}")
    print("=" * 50)
    
    prompt = "Explain what Ollama is in 2-3 sentences."
    print(f"\n👤 Prompt: {prompt}\n")
    
    response = client.generate(
        model=model,
        prompt=prompt,
        temperature=0.7
    )
    
    print(f"🤖 Response:\n{response}")
    print("\n" + "=" * 50)
    
    # With system message
    print("\n\n📝 Example with system message:")
    print("=" * 50)
    
    system_msg = "You are a helpful assistant that speaks like a pirate."
    prompt = "Tell me about machine learning."
    
    print(f"\n🏴‍☠️ System: {system_msg}")
    print(f"👤 Prompt: {prompt}\n")
    
    response = client.generate(
        model=model,
        prompt=prompt,
        system=system_msg,
        temperature=0.8
    )
    
    print(f"🤖 Response:\n{response}")
    print("\n" + "=" * 50)


if __name__ == "__main__":
    main()
