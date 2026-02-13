"""
Model Comparison Example - Compare responses from different models

This example compares how different models respond to the same prompt.
"""

from otk import OllamaClient, ModelManager
import time

def main():
    client = OllamaClient()
    manager = ModelManager()
    
    if not client.is_running():
        print("❌ Ollama is not running. Please start Ollama first.")
        return
    
    print("✓ Connected to Ollama")
    
    # Get available models
    installed_models = [m['name'] for m in manager.list_models()]
    
    if len(installed_models) < 2:
        print("\n⚠️  You need at least 2 models installed for comparison.")
        print("Install more models with: ollama pull <model_name>")
        return
    
    print(f"\n📦 Available models: {', '.join(installed_models)}")
    
    # Select models to compare
    print("\nSelect models to compare (or press Enter to use all):")
    selection = input("Enter model names separated by commas: ").strip()
    
    if selection:
        models = [m.strip() for m in selection.split(',')]
    else:
        models = installed_models[:3]  # Use first 3 models
    
    # Get prompt
    print("\n" + "=" * 50)
    prompt = input("Enter your prompt: ").strip()
    
    if not prompt:
        prompt = "Explain quantum computing in simple terms."
    
    print(f"\n🎯 Prompt: {prompt}")
    print("=" * 50)
    
    # Compare models
    results = []
    
    for model in models:
        print(f"\n🤖 Testing model: {model}")
        print("-" * 50)
        
        start_time = time.time()
        
        try:
            response = client.generate(
                model=model,
                prompt=prompt,
                temperature=0.7
            )
            
            elapsed_time = time.time() - start_time
            
            results.append({
                'model': model,
                'response': response,
                'time': elapsed_time,
                'length': len(response),
                'words': len(response.split())
            })
            
            print(f"✓ Response generated in {elapsed_time:.2f}s")
            print(f"Response preview: {response[:150]}...")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            results.append({
                'model': model,
                'response': None,
                'time': 0,
                'error': str(e)
            })
    
    # Display comparison
    print("\n\n📊 COMPARISON RESULTS")
    print("=" * 50)
    
    for i, result in enumerate(results, 1):
        print(f"\n{i}. Model: {result['model']}")
        print("-" * 50)
        
        if result['response']:
            print(f"Response Time: {result['time']:.2f}s")
            print(f"Response Length: {result['length']} characters, {result['words']} words")
            print(f"\nFull Response:\n{result['response']}")
        else:
            print(f"❌ Error: {result.get('error', 'Unknown error')}")
        
        print()
    
    # Summary statistics
    print("\n📈 SUMMARY STATISTICS")
    print("=" * 50)
    
    successful_results = [r for r in results if r['response']]
    
    if successful_results:
        fastest = min(successful_results, key=lambda x: x['time'])
        longest = max(successful_results, key=lambda x: x['length'])
        
        print(f"⚡ Fastest: {fastest['model']} ({fastest['time']:.2f}s)")
        print(f"📝 Longest response: {longest['model']} ({longest['length']} chars)")
        
        avg_time = sum(r['time'] for r in successful_results) / len(successful_results)
        avg_length = sum(r['length'] for r in successful_results) / len(successful_results)
        
        print(f"⏱️  Average time: {avg_time:.2f}s")
        print(f"📏 Average length: {avg_length:.0f} characters")


if __name__ == "__main__":
    main()
