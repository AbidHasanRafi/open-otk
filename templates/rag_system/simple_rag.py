"""
RAG (Retrieval Augmented Generation) System Template

A simple RAG system that uses embeddings for semantic search
and generates answers based on relevant context.
"""

from otk import OllamaClient
import numpy as np
import json
from typing import List, Dict

class SimpleRAG:
    def __init__(
        self,
        llm_model=None,
        embedding_model=None,
        top_k=3
    ):
        """
        Initialize the RAG system
        
        Args:
            llm_model: Model for generating answers (auto-detects if None)
            embedding_model: Model for generating embeddings (auto-detects if None)
            top_k: Number of top results to retrieve
        """
        from otk import ModelManager
        
        self.client = OllamaClient()
        self.manager = ModelManager()
        self.top_k = top_k
        
        # Auto-detect LLM model
        if llm_model is None:
            available = self.manager.list_models()
            if available:
                self.llm_model = available[0]['name']
                print(f"✓ Auto-selected LLM model: {self.llm_model}")
            else:
                raise ValueError("No models installed. Please run: ollama pull qwen2:0.5b")
        else:
            self.llm_model = llm_model
        
        # Auto-detect or use embedding model
        if embedding_model is None:
            # Try to find an embedding model
            available = self.manager.list_models()
            embedding_models = [m['name'] for m in available if 'embed' in m['name'].lower()]
            
            if embedding_models:
                self.embedding_model = embedding_models[0]
                print(f"✓ Auto-selected embedding model: {self.embedding_model}")
            else:
                # Use the LLM model for embeddings (some models support this)
                print(f"⚠️  No dedicated embedding model found.")
                print(f"   Using LLM model '{self.llm_model}' for embeddings.")
                print(f"   For better results, install: ollama pull nomic-embed-text")
                self.embedding_model = self.llm_model
        else:
            self.embedding_model = embedding_model
        
        self.documents = []
        self.embeddings = []
    
    def add_document(self, text: str, metadata: Dict = None):
        """
        Add a document to the knowledge base
        
        Args:
            text: Document text
            metadata: Optional metadata (title, source, etc.)
        """
        # Generate embedding
        embedding = self.client.embeddings(
            model=self.embedding_model,
            text=text
        )
        
        # Store document and embedding
        self.documents.append({
            'text': text,
            'metadata': metadata or {},
            'id': len(self.documents)
        })
        self.embeddings.append(embedding)
        
        print(f"✓ Added document {len(self.documents)}")
    
    def add_documents_from_file(self, filepath: str):
        """
        Load documents from a JSON file
        
        Expected format:
        [
            {"text": "...", "metadata": {...}},
            {"text": "...", "metadata": {...}}
        ]
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            docs = json.load(f)
        
        print(f"Loading {len(docs)} documents...")
        for doc in docs:
            self.add_document(doc['text'], doc.get('metadata'))
    
    def search(self, query: str) -> List[Dict]:
        """
        Search for relevant documents
        
        Args:
            query: Search query
            
        Returns:
            List of relevant documents with scores
        """
        # Generate query embedding
        query_embedding = self.client.embeddings(
            model=self.embedding_model,
            text=query
        )
        
        # Calculate similarities
        similarities = []
        for i, doc_embedding in enumerate(self.embeddings):
            similarity = self._cosine_similarity(query_embedding, doc_embedding)
            similarities.append((i, similarity))
        
        # Sort by similarity
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        # Get top-k results
        results = []
        for idx, score in similarities[:self.top_k]:
            results.append({
                **self.documents[idx],
                'score': score
            })
        
        return results
    
    def query(self, question: str, stream=True) -> str:
        """
        Answer a question using RAG
        
        Args:
            question: Question to answer
            stream: Whether to stream the response
            
        Returns:
            Generated answer
        """
        # Search for relevant documents
        relevant_docs = self.search(question)
        
        # Build context
        context = "\n\n".join([
            f"Document {i+1}:\n{doc['text']}"
            for i, doc in enumerate(relevant_docs)
        ])
        
        # Create prompt
        prompt = f"""Based on the following context, answer the question.
        
Context:
{context}

Question: {question}

Answer:"""
        
        # Generate answer
        if stream:
            print("\n🤖 Answer: ", end='', flush=True)
            answer = ""
            for chunk in self.client.stream_generate(
                model=self.llm_model,
                prompt=prompt,
                temperature=0.3
            ):
                print(chunk, end='', flush=True)
                answer += chunk
            print("\n")
            return answer
        else:
            answer = self.client.generate(
                model=self.llm_model,
                prompt=prompt,
                temperature=0.3
            )
            return answer
    
    def save_knowledge_base(self, filepath: str):
        """Save the knowledge base to a file"""
        data = {
            'documents': self.documents,
            'embeddings': [emb for emb in self.embeddings]
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        
        print(f"✓ Knowledge base saved to {filepath}")
    
    def load_knowledge_base(self, filepath: str):
        """Load the knowledge base from a file"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.documents = data['documents']
        self.embeddings = data['embeddings']
        
        print(f"✓ Loaded {len(self.documents)} documents")
    
    @staticmethod
    def _cosine_similarity(vec1, vec2):
        """Calculate cosine similarity"""
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)
        
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        return dot_product / (norm1 * norm2)


def main():
    """Demo of the RAG system"""
    print("🔍 Simple RAG System")
    print("=" * 50)
    
    # Initialize RAG (auto-detects available models)
    try:
        rag = SimpleRAG(top_k=3)  # Auto-detect models
    except ValueError as e:
        print(f"\n❌ {e}")
        return
    
    # Add sample documents
    print("\n📚 Adding documents to knowledge base...")
    
    documents = [
        {
            "text": "Python is a high-level programming language known for its simplicity and readability. It was created by Guido van Rossum and first released in 1991.",
            "metadata": {"topic": "Python", "type": "intro"}
        },
        {
            "text": "Machine learning is a subset of artificial intelligence that enables systems to learn and improve from experience without being explicitly programmed.",
            "metadata": {"topic": "ML", "type": "definition"}
        },
        {
            "text": "Ollama is a tool that allows you to run large language models locally on your machine. It supports various models like Llama 2, Mistral, and more.",
            "metadata": {"topic": "Ollama", "type": "intro"}
        },
        {
            "text": "Neural networks are computing systems inspired by biological neural networks. They consist of layers of interconnected nodes that process information.",
            "metadata": {"topic": "Neural Networks", "type": "definition"}
        },
        {
            "text": "RAG (Retrieval Augmented Generation) combines information retrieval with text generation to provide more accurate and contextual responses.",
            "metadata": {"topic": "RAG", "type": "definition"}
        }
    ]
    
    for doc in documents:
        rag.add_document(doc['text'], doc['metadata'])
    
    # Interactive query loop
    print("\n" + "=" * 50)
    print("Commands:")
    print("  'quit' - Exit")
    print("  'search <query>' - Search without generating answer")
    print("  'save' - Save knowledge base")
    print("=" * 50)
    
    while True:
        try:
            query = input("\n❓ Your question: ").strip()
            
            if not query:
                continue
            
            if query.lower() == 'quit':
                print("\n👋 Goodbye!")
                break
            
            if query.lower().startswith('search '):
                search_query = query[7:]
                results = rag.search(search_query)
                
                print("\n🔍 Search Results:")
                for i, doc in enumerate(results, 1):
                    print(f"\n{i}. [Score: {doc['score']:.4f}]")
                    print(f"   {doc['text'][:100]}...")
                    print(f"   Metadata: {doc['metadata']}")
                continue
            
            if query.lower() == 'save':
                rag.save_knowledge_base("knowledge_base.json")
                continue
            
            # Answer question
            rag.query(query, stream=True)
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    main()
