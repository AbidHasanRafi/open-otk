"""
Text Analyzer Template

Analyze text using Ollama models for various tasks like
sentiment analysis, summarization, entity extraction, etc.
"""

from otk import OllamaClient
from typing import Dict, List

class TextAnalyzer:
    def __init__(self, model=None):
        """Initialize the text analyzer"""
        from otk import ModelManager
        
        self.client = OllamaClient()
        
        # Auto-detect model if not specified
        if model is None:
            manager = ModelManager()
            available = manager.list_models()
            if not available:
                raise ValueError("No models installed. Please run: ollama pull qwen2:0.5b")
            self.model = available[0]['name']
            print(f"✓ Using model: {self.model}")
        else:
            self.model = model
    
    def analyze_sentiment(self, text: str) -> Dict:
        """
        Analyze sentiment of text
        
        Returns:
            Dictionary with sentiment and confidence
        """
        prompt = f"""Analyze the sentiment of the following text.
        Respond with ONLY one word: Positive, Negative, or Neutral.
        
        Text: {text}
        
        Sentiment:"""
        
        response = self.client.generate(
            model=self.model,
            prompt=prompt,
            temperature=0.1
        ).strip()
        
        return {
            'text': text,
            'sentiment': response,
        }
    
    def summarize(self, text: str, max_sentences: int = 3) -> str:
        """
        Summarize text
        
        Args:
            text: Text to summarize
            max_sentences: Maximum sentences in summary
            
        Returns:
            Summary text
        """
        prompt = f"""Summarize the following text in {max_sentences} sentences or less.
        
        Text: {text}
        
        Summary:"""
        
        summary = self.client.generate(
            model=self.model,
            prompt=prompt,
            temperature=0.3
        )
        
        return summary.strip()
    
    def extract_keywords(self, text: str, num_keywords: int = 5) -> List[str]:
        """
        Extract keywords from text
        
        Args:
            text: Text to analyze
            num_keywords: Number of keywords to extract
            
        Returns:
            List of keywords
        """
        prompt = f"""Extract the {num_keywords} most important keywords from the following text.
        Respond with ONLY the keywords separated by commas.
        
        Text: {text}
        
        Keywords:"""
        
        response = self.client.generate(
            model=self.model,
            prompt=prompt,
            temperature=0.1
        )
        
        keywords = [k.strip() for k in response.split(',')]
        return keywords[:num_keywords]
    
    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """
        Extract named entities (people, places, organizations)
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary of entity types and their values
        """
        prompt = f"""Extract named entities from the following text.
        Categorize them as: PERSON, PLACE, ORGANIZATION.
        Format: CATEGORY: entity1, entity2
        
        Text: {text}
        
        Entities:"""
        
        response = self.client.generate(
            model=self.model,
            prompt=prompt,
            temperature=0.1
        )
        
        entities = {
            'PERSON': [],
            'PLACE': [],
            'ORGANIZATION': []
        }
        
        for line in response.split('\n'):
            line = line.strip()
            if ':' in line:
                category, items = line.split(':', 1)
                category = category.strip().upper()
                if category in entities:
                    entities[category] = [item.strip() for item in items.split(',') if item.strip()]
        
        return entities
    
    def classify_topic(self, text: str, topics: List[str]) -> str:
        """
        Classify text into one of the given topics
        
        Args:
            text: Text to classify
            topics: List of possible topics
            
        Returns:
            Most relevant topic
        """
        topics_str = ', '.join(topics)
        
        prompt = f"""Classify the following text into ONE of these topics: {topics_str}
        Respond with ONLY the topic name.
        
        Text: {text}
        
        Topic:"""
        
        response = self.client.generate(
            model=self.model,
            prompt=prompt,
            temperature=0.1
        )
        
        return response.strip()
    
    def analyze_readability(self, text: str) -> Dict:
        """
        Analyze text readability
        
        Returns:
            Dictionary with readability metrics
        """
        prompt = f"""Analyze the readability of the following text.
        Provide:
        1. Reading level (Elementary, Middle School, High School, College, Graduate)
        2. Complexity (Simple, Moderate, Complex)
        3. Brief explanation
        
        Text: {text}
        
        Analysis:"""
        
        response = self.client.generate(
            model=self.model,
            prompt=prompt,
            temperature=0.2
        )
        
        return {
            'text': text,
            'analysis': response.strip()
        }
    
    def detect_language(self, text: str) -> str:
        """
        Detect the language of text
        
        Returns:
            Language name
        """
        prompt = f"""Detect the language of the following text.
        Respond with ONLY the language name in English.
        
        Text: {text}
        
        Language:"""
        
        response = self.client.generate(
            model=self.model,
            prompt=prompt,
            temperature=0.1
        )
        
        return response.strip()


def main():
    """Demo of the text analyzer"""
    print("📊 Text Analyzer")
    print("=" * 50)
    
    try:
        analyzer = TextAnalyzer()  # Auto-detect model
    except ValueError as e:
        print(f"\n❌ {e}")
        return
    
    # Sample text
    sample_text = """
    Apple Inc. announced today that CEO Tim Cook will visit their new facility 
    in Cupertino, California next month. The tech giant has been investing heavily 
    in artificial intelligence and machine learning technologies. The company's 
    stock price rose 3% following the announcement.
    """
    
    print("\n📝 Sample Text:")
    print(sample_text.strip())
    print("\n" + "=" * 50)
    
    # Sentiment Analysis
    print("\n😊 Sentiment Analysis:")
    sentiment = analyzer.analyze_sentiment(sample_text)
    print(f"Sentiment: {sentiment['sentiment']}")
    
    # Summarization
    print("\n📋 Summary:")
    summary = analyzer.summarize(sample_text, max_sentences=2)
    print(summary)
    
    # Keyword Extraction
    print("\n🔑 Keywords:")
    keywords = analyzer.extract_keywords(sample_text, num_keywords=5)
    print(", ".join(keywords))
    
    # Entity Extraction
    print("\n🏷️  Named Entities:")
    entities = analyzer.extract_entities(sample_text)
    for entity_type, values in entities.items():
        if values:
            print(f"  {entity_type}: {', '.join(values)}")
    
    # Topic Classification
    print("\n📂 Topic Classification:")
    topics = ["Technology", "Politics", "Sports", "Entertainment", "Science"]
    topic = analyzer.classify_topic(sample_text, topics)
    print(f"Topic: {topic}")
    
    # Language Detection
    print("\n🌍 Language Detection:")
    language = analyzer.detect_language(sample_text)
    print(f"Language: {language}")
    
    # Interactive mode
    print("\n\n" + "=" * 50)
    print("Interactive Mode")
    print("Commands: sentiment, summarize, keywords, entities, topic, language, quit")
    print("=" * 50)
    
    while True:
        try:
            command = input("\n📊 Command: ").strip().lower()
            
            if command == 'quit':
                print("\n👋 Goodbye!")
                break
            
            if command not in ['sentiment', 'summarize', 'keywords', 'entities', 'topic', 'language']:
                print("❌ Invalid command")
                continue
            
            text = input("Enter text: ").strip()
            
            if not text:
                print("❌ Text cannot be empty")
                continue
            
            if command == 'sentiment':
                result = analyzer.analyze_sentiment(text)
                print(f"Sentiment: {result['sentiment']}")
            
            elif command == 'summarize':
                result = analyzer.summarize(text)
                print(f"Summary: {result}")
            
            elif command == 'keywords':
                result = analyzer.extract_keywords(text)
                print(f"Keywords: {', '.join(result)}")
            
            elif command == 'entities':
                result = analyzer.extract_entities(text)
                for entity_type, values in result.items():
                    if values:
                        print(f"{entity_type}: {', '.join(values)}")
            
            elif command == 'topic':
                topics_input = input("Enter topics (comma-separated): ").strip()
                topics = [t.strip() for t in topics_input.split(',')]
                result = analyzer.classify_topic(text, topics)
                print(f"Topic: {result}")
            
            elif command == 'language':
                result = analyzer.detect_language(text)
                print(f"Language: {result}")
        
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()
