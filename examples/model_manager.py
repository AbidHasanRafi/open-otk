"""
Model Management Example - List, pull, and manage models

This example demonstrates model management capabilities.
"""

from otk import ModelManager

def main():
    manager = ModelManager()
    
    print("🔧 Ollama Model Manager")
    print("=" * 50)
    
    while True:
        print("\nOptions:")
        print("1. List installed models")
        print("2. Pull a new model")
        print("3. Delete a model")
        print("4. Show model info")
        print("5. View recommended models")
        print("6. Check if model exists")
        print("0. Exit")
        
        choice = input("\nEnter your choice: ").strip()
        
        if choice == "0":
            print("\n👋 Goodbye!")
            break
        
        elif choice == "1":
            list_models(manager)
        
        elif choice == "2":
            pull_model(manager)
        
        elif choice == "3":
            delete_model(manager)
        
        elif choice == "4":
            show_model_info(manager)
        
        elif choice == "5":
            show_recommendations(manager)
        
        elif choice == "6":
            check_model_exists(manager)
        
        else:
            print("❌ Invalid choice. Please try again.")


def list_models(manager: ModelManager):
    """List all installed models"""
    print("\n📦 Installed Models:")
    print("-" * 50)
    
    models = manager.list_models()
    
    if not models:
        print("No models installed.")
        return
    
    for i, model in enumerate(models, 1):
        print(f"{i}. {model['name']}")
        print(f"   Size: {model['size']}")
        print(f"   Modified: {model['modified']}")
        print()


def pull_model(manager: ModelManager):
    """Pull a new model"""
    model_name = input("\nEnter model name to pull (e.g., llama2, mistral): ").strip()
    
    if not model_name:
        print("❌ Model name cannot be empty.")
        return
    
    print(f"\n📥 Pulling model: {model_name}")
    manager.pull_model(model_name, stream=True)


def delete_model(manager: ModelManager):
    """Delete a model"""
    model_name = input("\nEnter model name to delete: ").strip()
    
    if not model_name:
        print("❌ Model name cannot be empty.")
        return
    
    confirm = input(f"⚠️  Are you sure you want to delete '{model_name}'? (yes/no): ").strip().lower()
    
    if confirm == 'yes':
        if manager.delete_model(model_name):
            print(f"✓ Model '{model_name}' deleted successfully!")
        else:
            print(f"❌ Failed to delete model '{model_name}'.")
    else:
        print("❌ Deletion cancelled.")


def show_model_info(manager: ModelManager):
    """Show detailed model information"""
    model_name = input("\nEnter model name: ").strip()
    
    if not model_name:
        print("❌ Model name cannot be empty.")
        return
    
    print(f"\n📋 Information for '{model_name}':")
    print("-" * 50)
    
    info = manager.show_model_info(model_name)
    
    if 'error' in info:
        print(f"❌ Error: {info['error']}")
        return
    
    print(f"Parameters: {info.get('parameters', 'N/A')}")
    print(f"\nTemplate:\n{info.get('template', 'N/A')[:200]}...")
    print(f"\nDetails: {info.get('details', {})}")


def show_recommendations(manager: ModelManager):
    """Show recommended models"""
    print("\n💡 Recommended Models by Use Case:")
    print("-" * 50)
    
    recommendations = manager.recommend_models()
    
    for use_case, models in recommendations.items():
        print(f"\n{use_case.replace('_', ' ').title()}:")
        for model in models:
            print(f"  • {model}")


def check_model_exists(manager: ModelManager):
    """Check if a model exists"""
    model_name = input("\nEnter model name to check: ").strip()
    
    if not model_name:
        print("❌ Model name cannot be empty.")
        return
    
    if manager.model_exists(model_name):
        size = manager.get_model_size(model_name)
        print(f"✓ Model '{model_name}' exists (Size: {size})")
    else:
        print(f"❌ Model '{model_name}' not found.")


if __name__ == "__main__":
    main()
