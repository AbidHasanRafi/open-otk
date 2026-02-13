"""
Streaming Chat Example - Real-time streaming responses

This example demonstrates how to stream responses in real-time.
"""

from otk import OllamaClient

def main():
    client = OllamaClient()
    
    if not client.is_running():
        print("❌ Ollama is not running. Please start Ollama first.")
        return
    
    print("✓ Connected to Ollama")
    
    model = "llama2"
    
    print(f"\n🤖 Streaming with model: {model}")
    print("=" * 50)
    
    prompt = "Write a short story about a robot learning to paint."
    print(f"\n👤 Prompt: {prompt}\n")
    print("🤖 Response (streaming):\n")
    
    # Stream the response
    for chunk in client.stream_generate(
        model=model,
        prompt=prompt,
        temperature=0.8
    ):
        print(chunk, end='', flush=True)
    
    print("\n\n" + "=" * 50)
    
    # Chat streaming example
    print("\n\n💬 Chat streaming example:")
    print("=" * 50)
    
    messages = [
        {"role": "system", "content": "You are a creative writing assistant."},
        {"role": "user", "content": "Give me 3 creative writing prompts."}
    ]
    
    print("\n🤖 Response (streaming):\n")
    
    for chunk in client.stream_chat(
        model=model,
        messages=messages,
        temperature=0.9
    ):
        print(chunk, end='', flush=True)
    
    print("\n\n" + "=" * 50)


if __name__ == "__main__":
    main()
