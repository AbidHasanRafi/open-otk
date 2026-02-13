"""
Embeddings Example - Generate and use text embeddings

This example shows how to generate embeddings and calculate similarity.
"""

from otk import OllamaClient
import numpy as np

def cosine_similarity(vec1, vec2):
    """Calculate cosine similarity between two vectors"""
    vec1 = np.array(vec1)
    vec2 = np.array(vec2)
    
    dot_product = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    
    return dot_product / (norm1 * norm2)


def main():
    client = OllamaClient()
    
    if not client.is_running():
        print("❌ Ollama is not running. Please start Ollama first.")
        return
    
    print("✓ Connected to Ollama")
    
    # Embedding model (make sure it's installed)
    model = "nomic-embed-text"
    
    print(f"\n🔢 Using embedding model: {model}")
    print("=" * 50)
    
    # Sample texts
    texts = [
        "The cat sat on the mat.",
        "A feline rested on the rug.",
        "Python is a programming language.",
        "Dogs are loyal animals.",
        "Machine learning is a subset of AI."
    ]
    
    print("\n📝 Sample texts:")
    for i, text in enumerate(texts, 1):
        print(f"{i}. {text}")
    
    # Generate embeddings
    print("\n🔄 Generating embeddings...")
    embeddings = []
    
    for text in texts:
        embedding = client.embeddings(model=model, text=text)
        embeddings.append(embedding)
        print(f"✓ Generated embedding for: '{text[:50]}...'")
    
    # Calculate similarities
    print("\n📊 Similarity Matrix:")
    print("-" * 50)
    
    # Header
    print(f"{'':30}", end='')
    for i in range(len(texts)):
        print(f"Text {i+1:2}  ", end='')
    print()
    
    # Similarity scores
    for i, text1 in enumerate(texts):
        print(f"Text {i+1}: {text1[:25]:25}", end='')
        for j, text2 in enumerate(texts):
            similarity = cosine_similarity(embeddings[i], embeddings[j])
            print(f"{similarity:7.4f} ", end='')
        print()
    
    # Find most similar pairs
    print("\n🔍 Most Similar Text Pairs:")
    print("-" * 50)
    
    similarities = []
    for i in range(len(texts)):
        for j in range(i + 1, len(texts)):
            sim = cosine_similarity(embeddings[i], embeddings[j])
            similarities.append((i, j, sim))
    
    # Sort by similarity
    similarities.sort(key=lambda x: x[2], reverse=True)
    
    # Show top 3
    for i, j, sim in similarities[:3]:
        print(f"\nSimilarity: {sim:.4f}")
        print(f"  Text {i+1}: {texts[i]}")
        print(f"  Text {j+1}: {texts[j]}")
    
    # Semantic search example
    print("\n\n🔎 Semantic Search Example:")
    print("=" * 50)
    
    query = "What is AI?"
    print(f"\nQuery: {query}")
    
    query_embedding = client.embeddings(model=model, text=query)
    
    # Find most similar text
    similarities = []
    for i, text in enumerate(texts):
        sim = cosine_similarity(query_embedding, embeddings[i])
        similarities.append((i, sim))
    
    similarities.sort(key=lambda x: x[1], reverse=True)
    
    print("\nMost relevant results:")
    for i, (idx, sim) in enumerate(similarities[:3], 1):
        print(f"{i}. [{sim:.4f}] {texts[idx]}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure you have the 'nomic-embed-text' model installed:")
        print("  ollama pull nomic-embed-text")
