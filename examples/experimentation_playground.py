"""
Experimentation Playground

Interactive playground for testing, comparing, and experimenting
with different models, settings, and prompts.

This is where you explore model capabilities and find what works best!
"""

from otk import (
    ModelExperiment,
    ModelPlayground,
    ABTest,
    ModelManager,
    ModelBuilder,
    ModelPresets
)
import sys


def interactive_menu():
    """Show interactive menu"""
    print("\n" + "="*70)
    print("🧪 Ollama Experimentation Playground")
    print("="*70)
    print("\nWhat would you like to do?")
    print("\n1. Compare Multiple Models")
    print("2. Test Different Temperatures")
    print("3. Try Prompt Variations")
    print("4. Benchmark a Model")
    print("5. A/B Test Two Models")
    print("6. Experiment with System Messages")
    print("7. Quick Model Test")
    print("8. List Available Models")
    print("0. Exit")
    
    return input("\nChoice: ").strip()


def compare_models_interactive():
    """Interactive model comparison"""
    print("\n" + "="*70)
    print("⚖️  Model Comparison")
    print("="*70)
    
    models_input = input("\nEnter model names (comma-separated, e.g., llama2,mistral): ")
    models = [m.strip() for m in models_input.split(',') if m.strip()]
    
    if len(models) < 2:
        print("❌ Need at least 2 models")
        return
    
    prompt = input("\nEnter test prompt: ")
    parallel = input("\nRun in parallel? (y/n): ").lower() == 'y'
    
    experiment = ModelExperiment()
    print("\n🚀 Running comparison...")
    
    result = experiment.compare_models(models, prompt, parallel=parallel)
    experiment.print_comparison(result)


def test_temperatures_interactive():
    """Interactive temperature testing"""
    print("\n" + "="*70)
    print("🌡️  Temperature Experiment")
    print("="*70)
    
    model = input("\nEnter model name: ").strip()
    prompt = input("Enter test prompt: ").strip()
    
    temps_input = input("Temperatures to try (comma-separated, or press Enter for default): ").strip()
    
    if temps_input:
        temps = [float(t.strip()) for t in temps_input.split(',')]
    else:
        temps = None  # Use defaults
    
    playground = ModelPlayground()
    playground.try_temperatures(model, prompt, temps)


def try_prompts_interactive():
    """Interactive prompt variation testing"""
    print("\n" + "="*70)
    print("📝 Prompt Variations")
    print("="*70)
    
    model = input("\nEnter model name: ").strip()
    base = input("Enter base prompt: ").strip()
    
    print("\nEnter variations (one per line, empty line to finish):")
    variations = []
    while True:
        var = input("> ").strip()
        if not var:
            break
        variations.append(var)
    
    if variations:
        playground = ModelPlayground()
        playground.try_prompt_variations(model, base, variations)


def benchmark_interactive():
    """Interactive benchmarking"""
    print("\n" + "="*70)
    print("⏱️  Model Benchmark")
    print("="*70)
    
    model = input("\nEnter model name: ").strip()
    prompt = input("Enter test prompt: ").strip()
    
    iterations_input = input("Number of iterations (default: 5): ").strip()
    iterations = int(iterations_input) if iterations_input else 5
    
    experiment = ModelExperiment()
    print(f"\n🚀 Running {iterations} iterations...")
    
    stats = experiment.benchmark(model, prompt, iterations=iterations)
    experiment.print_benchmark(stats)


def ab_test_interactive():
    """Interactive A/B testing"""
    print("\n" + "="*70)
    print("⚖️  A/B Test")
    print("="*70)
    
    model_a = input("\nModel A: ").strip()
    model_b = input("Model B: ").strip()
    
    print("\nEnter test prompts (one per line, empty line to finish):")
    prompts = []
    while True:
        prompt = input("> ").strip()
        if not prompt:
            break
        prompts.append(prompt)
    
    if not prompts:
        print("❌ Need at least one prompt")
        return
    
    ab_tester = ABTest()
    ab_tester.test(model_a, model_b, prompts)


def system_messages_interactive():
    """Interactive system message testing"""
    print("\n" + "="*70)
    print("🎭 System Message Experiment")
    print("="*70)
    
    model = input("\nEnter model name: ").strip()
    prompt = input("Enter test prompt: ").strip()
    
    print("\nEnter system messages (one per line, empty line to finish):")
    systems = []
    while True:
        sys_msg = input("> ").strip()
        if not sys_msg:
            break
        systems.append(sys_msg)
    
    if systems:
        playground = ModelPlayground()
        playground.try_system_messages(model, prompt, systems)


def quick_test():
    """Quick model test"""
    print("\n" + "="*70)
    print("⚡ Quick Test")
    print("="*70)
    
    model = input("\nModel name: ").strip()
    prompt = input("Prompt: ").strip()
    
    experiment = ModelExperiment()
    print("\n🚀 Running...")
    
    result = experiment.run_single(model, prompt)
    
    print(f"\n{'='*70}")
    if result.error:
        print(f"❌ Error: {result.error}")
    else:
        print(f"✅ Response:\n{result.response}")
        print(f"\n⏱️  Time: {result.time_taken:.2f}s")
        print(f"📝 Tokens: ~{result.tokens_estimated}")
        print(f"🚀 Speed: ~{result.tokens_estimated / result.time_taken:.1f} tok/s")


def list_models():
    """List available models"""
    print("\n" + "="*70)
    print("📚 Available Models")
    print("="*70)
    
    try:
        manager = ModelManager()
        models = manager.list_models()
        
        if not models:
            print("\n❌ No models installed")
            print("Install models with: ollama pull <model-name>")
            return
        
        print(f"\n✅ Found {len(models)} model(s):\n")
        for model in models:
            print(f"  • {model['name']:<30} {model['size']:>10}")
        
        print(f"\n💡 Use these names in the playground experiments!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")


def preset_experiments():
    """Run preset experiments"""
    print("\n" + "="*70)
    print("🎯 Preset Experiments")
    print("="*70)
    print("\nPre-configured experiments for common testing scenarios")
    print("\n1. The Creative Test - See which model is most creative")
    print("2. The Speed Test - Compare response times")
    print("3. The Accuracy Test - Test factual knowledge")
    print("4. The Code Test - Compare code generation")
    print("0. Back")
    
    choice = input("\nChoice: ").strip()
    
    if choice == "1":
        run_creative_test()
    elif choice == "2":
        run_speed_test()
    elif choice == "3":
        run_accuracy_test()
    elif choice == "4":
        run_code_test()


def run_creative_test():
    """Test creativity"""
    print("\n🎨 Creative Test")
    
    models_input = input("\nModels to test (comma-separated): ")
    models = [m.strip() for m in models_input.split(',') if m.strip()]
    
    if not models:
        return
    
    creative_prompts = [
        "Write a creative story opening about a time-traveling cat",
        "Invent a new ice cream flavor and describe it",
        "Create a haiku about robots"
    ]
    
    experiment = ModelExperiment()
    
    print("\n🚀 Running creative prompts...")
    for prompt in creative_prompts:
        print(f"\n{'='*70}")
        print(f"📝 {prompt}")
        print('='*70)
        
        result = experiment.compare_models(models, prompt)
        for exp in result.results:
            if not exp.error:
                print(f"\n{exp.model}:")
                print(exp.response[:150] + "..." if len(exp.response) > 150 else exp.response)


def run_speed_test():
    """Test speed"""
    print("\n⚡ Speed Test")
    
    models_input = input("\nModels to test (comma-separated): ")
    models = [m.strip() for m in models_input.split(',') if m.strip()]
    
    if not models:
        return
    
    prompt = "Explain what Python is in one sentence."
    
    experiment = ModelExperiment()
    result = experiment.compare_models(models, prompt, parallel=False)
    experiment.print_comparison(result)


def run_accuracy_test():
    """Test factual accuracy"""
    print("\n🎯 Accuracy Test")
    
    model = input("\nModel to test: ").strip()
    
    factual_questions = [
        "What is the capital of France?",
        "What is 15 * 24?",
        "Who wrote Romeo and Juliet?",
        "What year did World War 2 end?"
    ]
    
    experiment = ModelExperiment()
    
    print(f"\n{'='*70}")
    print(f"Testing {model} with factual questions")
    print('='*70)
    
    for question in factual_questions:
        result = experiment.run_single(model, question, temperature=0.2)
        print(f"\nQ: {question}")
        print(f"A: {result.response}")


def run_code_test():
    """Test code generation"""
    print("\n💻 Code Test")
    
    models_input = input("\nModels to test (comma-separated): ")
    models = [m.strip() for m in models_input.split(',') if m.strip()]
    
    if not models:
        return
    
    code_prompt = "Write a Python function to calculate fibonacci numbers"
    
    experiment = ModelExperiment()
    result = experiment.compare_models(models, code_prompt, parallel=False)
    
    print(f"\n{'='*70}")
    print("Code Generation Results")
    print('='*70)
    
    for exp in result.results:
        print(f"\n🤖 {exp.model}:")
        print('─'*70)
        if exp.error:
            print(f"❌ Error: {exp.error}")
        else:
            print(exp.response)


def main():
    """Main playground loop"""
    print("\n" + "="*70)
    print("🧪 Welcome to the Ollama Experimentation Playground!")
    print("="*70)
    print("\n✨ This is your sandbox for:")
    print("   • Testing different models")
    print("   • Comparing outputs")
    print("   • Finding optimal settings")
    print("   • Exploring capabilities")
    
    while True:
        try:
            choice = interactive_menu()
            
            if choice == "0":
                print("\n👋 Happy experimenting!")
                break
            elif choice == "1":
                compare_models_interactive()
            elif choice == "2":
                test_temperatures_interactive()
            elif choice == "3":
                try_prompts_interactive()
            elif choice == "4":
                benchmark_interactive()
            elif choice == "5":
                ab_test_interactive()
            elif choice == "6":
                system_messages_interactive()
            elif choice == "7":
                quick_test()
            elif choice == "8":
                list_models()
            elif choice == "9":
                preset_experiments()
            else:
                print("❌ Invalid choice")
            
            input("\nPress Enter to continue...")
            
        except KeyboardInterrupt:
            print("\n\n👋 Interrupted by user")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            print("Make sure Ollama is running and models are installed!")
            input("\nPress Enter to continue...")


if __name__ == "__main__":
    main()
