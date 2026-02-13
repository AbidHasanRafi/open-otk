"""
Creative Integration Examples

This shows how to integrate Ollama models into your own Python projects
in creative and useful ways beyond basic chat.
"""

from otk import (
    OllamaClient,
    ChatSession,
    CustomizableModel,
    ModelBuilder,
    HookType,
    ModelPresets
)
import json
import re
from typing import List, Dict


# ============================================================================
# Example 1: Content Generator with Custom Formatting
# ============================================================================

class BlogPostGenerator:
    """Generate structured blog posts with custom formatting"""
    
    def __init__(self, model: str = "llama2"):
        self.model = CustomizableModel(model)
        
        # Add custom post-processing
        self.model.set_post_processor(self._format_blog_post)
    
    def _format_blog_post(self, text: str) -> str:
        """Format the output as proper blog post"""
        # Add metadata
        lines = text.split('\n')
        formatted = []
        formatted.append("=" * 60)
        formatted.append("BLOG POST")
        formatted.append("=" * 60)
        formatted.extend(lines)
        formatted.append("\n" + "=" * 60)
        return '\n'.join(formatted)
    
    def generate_post(self, topic: str, tone: str = "professional") -> str:
        """Generate a blog post on a topic"""
        prompt = f"""Write a short blog post about: {topic}

Tone: {tone}
Include: Introduction, main points, conclusion
Keep it under 300 words."""
        
        return self.model.generate(prompt, temperature=0.8)


# ============================================================================
# Example 2: Smart Data Processor
# ============================================================================

class SmartDataProcessor:
    """Use LLM to process and categorize data"""
    
    def __init__(self, model: str = "llama2"):
        self.client = OllamaClient()
        self.model = model
    
    def categorize_text(self, text: str, categories: List[str]) -> str:
        """Categorize text into one of the given categories"""
        prompt = f"""Categorize this text into ONE of these categories: {', '.join(categories)}

Text: {text}

Respond with ONLY the category name, nothing else."""
        
        response = self.client.generate(
            self.model,
            prompt,
            temperature=0.3  # Low temperature for consistent categorization
        )
        
        return response.strip()
    
    def extract_structured_data(self, text: str, fields: List[str]) -> Dict:
        """Extract structured information from text"""
        prompt = f"""Extract the following information from this text: {', '.join(fields)}

Text: {text}

Respond in JSON format with these fields: {', '.join(fields)}"""
        
        response = self.client.generate(self.model, prompt, temperature=0.2)
        
        # Try to parse JSON
        try:
            # Find JSON in response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        
        return {"raw": response}
    
    def summarize_batch(self, texts: List[str]) -> List[str]:
        """Summarize multiple texts"""
        summaries = []
        for text in texts:
            prompt = f"Summarize this in one sentence: {text}"
            summary = self.client.generate(self.model, prompt, temperature=0.5)
            summaries.append(summary)
        return summaries


# ============================================================================
# Example 3: Code Helper Integration
# ============================================================================

class CodeHelper:
    """Integrate LLM as a code assistant in your workflow"""
    
    def __init__(self, model: str = "codellama"):
        # Use code-optimized settings
        self.model = (ModelBuilder(model)
                     .with_preset("code")
                     .build())
    
    def explain_code(self, code: str, language: str = "python") -> str:
        """Explain what code does"""
        prompt = f"""Explain what this {language} code does in simple terms:

```{language}
{code}
```

Explain line by line if it's complex."""
        
        return self.model.generate(prompt)
    
    def suggest_improvements(self, code: str) -> str:
        """Suggest code improvements"""
        prompt = f"""Review this code and suggest improvements for:
- Performance
- Readability
- Best practices

Code:
```python
{code}
```

Provide specific suggestions."""
        
        return self.model.generate(prompt)
    
    def generate_tests(self, function_code: str) -> str:
        """Generate unit tests for a function"""
        prompt = f"""Generate pytest unit tests for this function:

{function_code}

Include:
- Happy path tests
- Edge cases
- Error cases"""
        
        return self.model.generate(prompt)
    
    def debug_error(self, code: str, error: str) -> str:
        """Help debug an error"""
        prompt = f"""Help debug this error:

Code:
```python
{code}
```

Error:
{error}

What's wrong and how to fix it?"""
        
        return self.model.generate(prompt)


# ============================================================================
# Example 4: Custom Chatbot with Personality
# ============================================================================

class PersonalityBot:
    """Chatbot with customizable personality"""
    
    def __init__(self, model: str, personality: str, name: str = "Bot"):
        self.name = name
        self.personality = personality
        
        system_message = f"""You are {name}, a chatbot with this personality: {personality}

Always stay in character. Be helpful but maintain your unique personality."""
        
        self.session = ChatSession(
            model,
            system_message=system_message,
            temperature=0.9  # High creativity for personality
        )
        
        # Track conversation metadata
        self.message_count = 0
        self.topics_discussed = []
    
    def chat(self, message: str) -> str:
        """Chat with the bot"""
        self.message_count += 1
        response = self.session.send(message)
        return f"{self.name}: {response}"
    
    def add_memory(self, fact: str):
        """Add a fact to remember"""
        self.session.messages.append({
            "role": "system",
            "content": f"Remember this: {fact}"
        })
    
    def get_stats(self) -> Dict:
        """Get conversation statistics"""
        return {
            'messages': self.message_count,
            'history_length': len(self.session.get_history()),
            'name': self.name,
            'personality': self.personality
        }


# ============================================================================
# Example 5: Multi-Model Pipeline
# ============================================================================

class MultiModelPipeline:
    """Chain multiple models for complex tasks"""
    
    def __init__(self):
        self.client = OllamaClient()
    
    def generate_and_improve(
        self,
        topic: str,
        creator_model: str = "llama2",
        critic_model: str = "mistral"
    ) -> Dict[str, str]:
        """
        Use one model to generate, another to critique and improve
        """
        # Step 1: Generate initial content
        initial_prompt = f"Write a short creative story about: {topic}"
        initial = self.client.generate(creator_model, initial_prompt, temperature=0.9)
        
        # Step 2: Critique
        critique_prompt = f"""Review this story and provide constructive criticism:

{initial}

What could be improved?"""
        critique = self.client.generate(critic_model, critique_prompt, temperature=0.5)
        
        # Step 3: Improve based on critique
        improve_prompt = f"""Improve this story based on the feedback:

Original story:
{initial}

Feedback:
{critique}

Write an improved version:"""
        improved = self.client.generate(creator_model, improve_prompt, temperature=0.8)
        
        return {
            'original': initial,
            'critique': critique,
            'improved': improved
        }
    
    def translate_and_check(
        self,
        text: str,
        target_language: str,
        model: str = "llama2"
    ) -> Dict[str, str]:
        """Translate and verify translation"""
        # Translate
        translation = self.client.generate(
            model,
            f"Translate to {target_language}: {text}",
            temperature=0.3
        )
        
        # Back-translate to verify
        back_translation = self.client.generate(
            model,
            f"Translate to English: {translation}",
            temperature=0.3
        )
        
        return {
            'original': text,
            'translated': translation,
            'back_translated': back_translation,
            'accurate': text.lower().strip() in back_translation.lower()
        }


# ============================================================================
# Example 6: Adaptive Response System
# ============================================================================

class AdaptiveResponder:
    """Adapt responses based on user feedback"""
    
    def __init__(self, model: str = "llama2"):
        self.model = model
        self.client = OllamaClient()
        self.temperature = 0.7
        self.feedback_history = []
    
    def respond(self, prompt: str) -> str:
        """Generate response with current settings"""
        response = self.client.generate(
            self.model,
            prompt,
            temperature=self.temperature
        )
        return response
    
    def provide_feedback(self, feedback: str):
        """Adjust based on feedback"""
        self.feedback_history.append(feedback)
        
        # Simple adaptive logic
        if "creative" in feedback.lower() or "boring" in feedback.lower():
            self.temperature = min(1.5, self.temperature + 0.1)
            print(f"🎨 Increased creativity (temp: {self.temperature:.1f})")
        elif "focused" in feedback.lower() or "random" in feedback.lower():
            self.temperature = max(0.1, self.temperature - 0.1)
            print(f"🎯 Increased focus (temp: {self.temperature:.1f})")
    
    def reset(self):
        """Reset to defaults"""
        self.temperature = 0.7
        self.feedback_history = []


# ============================================================================
# DEMO FUNCTIONS
# ============================================================================

def demo_blog_generator():
    """Demo the blog post generator"""
    print("\n" + "="*70)
    print("📝 Blog Post Generator Demo")
    print("="*70)
    
    generator = BlogPostGenerator("llama2")
    post = generator.generate_post(
        topic="The future of AI",
        tone="inspiring"
    )
    print(post)


def demo_data_processor():
    """Demo smart data processor"""
    print("\n" + "="*70)
    print("📊 Smart Data Processor Demo")
    print("="*70)
    
    processor = SmartDataProcessor("llama2")
    
    text = "I love this product! It works great and exceeded my expectations."
    categories = ["positive", "negative", "neutral"]
    
    category = processor.categorize_text(text, categories)
    print(f"\nText: {text}")
    print(f"Category: {category}")


def demo_code_helper():
    """Demo code helper"""
    print("\n" + "="*70)
    print("💻 Code Helper Demo")
    print("="*70)
    
    helper = CodeHelper("codellama")
    
    code = """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
"""
    
    explanation = helper.explain_code(code, "python")
    print(f"\nCode:\n{code}")
    print(f"\nExplanation:\n{explanation}")


def demo_personality_bot():
    """Demo personality chatbot"""
    print("\n" + "="*70)
    print("🤖 Personality Bot Demo")
    print("="*70)
    
    bot = PersonalityBot(
        model="llama2",
        personality="friendly pirate captain who loves coding",
        name="Captain Code"
    )
    
    print("\n" + bot.chat("Hello! What can you help me with?"))
    print("\n" + bot.chat("Tell me about Python"))
    
    print(f"\n📊 Stats: {bot.get_stats()}")


def demo_multi_model():
    """Demo multi-model pipeline"""
    print("\n" + "="*70)
    print("🔄 Multi-Model Pipeline Demo")
    print("="*70)
    
    pipeline = MultiModelPipeline()
    
    result = pipeline.generate_and_improve("a robot learning to paint")
    
    print("\n📝 Original:")
    print(result['original'][:200] + "...")
    print("\n💭 Critique:")
    print(result['critique'][:200] + "...")
    print("\n✨ Improved:")
    print(result['improved'][:200] + "...")


def main():
    """Run all demos"""
    print("\n" + "="*70)
    print("🎨 Creative Integration Examples")
    print("="*70)
    print("\nThese examples show how to integrate Ollama into YOUR projects!")
    print("Go beyond chat - build real applications with AI!")
    
    try:
        # Show what's possible (commented out to avoid long runs)
        print("\n💡 Available Demos:")
        print("1. Blog Post Generator - Auto-format content")
        print("2. Smart Data Processor - Categorize and extract")
        print("3. Code Helper - Explain, debug, test generation")
        print("4. Personality Bot - Custom chatbot personalities")
        print("5. Multi-Model Pipeline - Chain models together")
        print("6. Adaptive Responder - Learn from feedback")
        
        print("\n✨ Key Takeaways:")
        print("• Use CustomizableModel for full control")
        print("• Chain models for complex tasks")
        print("• Add custom processing with hooks")
        print("• Integrate into ANY Python application")
        print("• Build tools, not just chat interfaces")
        
        print("\n📖 To run a demo, uncomment in main() or import the classes!")
        
        # Uncomment to run demos:
        # demo_blog_generator()
        # demo_data_processor()
        # demo_code_helper()
        # demo_personality_bot()
        # demo_multi_model()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure Ollama is running and models are installed!")


if __name__ == "__main__":
    main()
