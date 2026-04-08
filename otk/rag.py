"""
Hybrid Retrieval-Augmented Generation engine.

Combines BM25 sparse retrieval, HNSW dense retrieval, Reciprocal Rank
Fusion, and optional LLM-based reranking for high-quality document
retrieval over a local Ollama stack.
"""

import json
import math
import re
import logging
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)

try:
    import hnswlib
    _HAS_HNSWLIB = True
except ImportError:
    _HAS_HNSWLIB = False


# ======================================================================
# Chunking
# ======================================================================

_SENTENCE_SPLIT = re.compile(r'(?<=[.!?])\s+')
_PARAGRAPH_SPLIT = re.compile(r'\n\s*\n')


def _count_tokens_approx(text: str) -> int:
    """Cheap token estimator (~3.3 chars/token for English)."""
    return max(1, int(len(text) / 3.3))


class RecursiveChunker:
    """
    Split text into semantically coherent chunks respecting a token budget.

    Strategy:
    1. Split on paragraph boundaries.
    2. If a paragraph exceeds the budget, split on sentence boundaries.
    3. Merge small consecutive chunks to fill the budget with *overlap*.
    """

    def __init__(
        self,
        max_tokens: int = 256,
        overlap_tokens: int = 32,
        token_counter: Optional[Callable[[str], int]] = None,
    ):
        self.max_tokens = max_tokens
        self.overlap_tokens = overlap_tokens
        self._count = token_counter or _count_tokens_approx

    def chunk(self, text: str) -> List[str]:
        paragraphs = _PARAGRAPH_SPLIT.split(text.strip())
        raw_chunks: List[str] = []
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            if self._count(para) <= self.max_tokens:
                raw_chunks.append(para)
            else:
                raw_chunks.extend(self._split_paragraph(para))

        return self._merge_with_overlap(raw_chunks)

    def _split_paragraph(self, para: str) -> List[str]:
        sentences = _SENTENCE_SPLIT.split(para)
        chunks: List[str] = []
        buf: List[str] = []
        buf_tok = 0
        for sent in sentences:
            sent = sent.strip()
            if not sent:
                continue
            stok = self._count(sent)
            if buf and buf_tok + stok > self.max_tokens:
                chunks.append(" ".join(buf))
                # keep last sentence as overlap seed
                overlap_buf = [buf[-1]] if buf else []
                buf = overlap_buf + [sent]
                buf_tok = sum(self._count(s) for s in buf)
            else:
                buf.append(sent)
                buf_tok += stok
        if buf:
            chunks.append(" ".join(buf))
        return chunks

    def _merge_with_overlap(self, chunks: List[str]) -> List[str]:
        if len(chunks) <= 1:
            return chunks
        merged: List[str] = []
        i = 0
        while i < len(chunks):
            if merged and self.overlap_tokens > 0:
                prev_words = merged[-1].split()
                overlap_word_count = max(1, self.overlap_tokens // 2)
                overlap = " ".join(prev_words[-overlap_word_count:])
                candidate = overlap + " " + chunks[i]
            else:
                candidate = chunks[i]

            while (
                i + 1 < len(chunks)
                and self._count(candidate + " " + chunks[i + 1]) <= self.max_tokens
            ):
                i += 1
                candidate = candidate + " " + chunks[i]

            merged.append(candidate.strip())
            i += 1
        return merged


# ======================================================================
# BM25 Sparse Index
# ======================================================================

def _tokenize(text: str) -> List[str]:
    """Lowercase whitespace+punctuation tokenizer."""
    return re.findall(r"[a-z0-9]+", text.lower())


class BM25Index:
    """
    Okapi BM25 sparse retrieval index with incremental updates.
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self._docs: List[List[str]] = []  # tokenised docs
        self._doc_lens: List[int] = []
        self._avg_dl: float = 0.0
        self._inverted: Dict[str, List[Tuple[int, int]]] = defaultdict(list)  # term -> [(doc_idx, freq)]
        self._n_docs: int = 0

    def add(self, text: str) -> int:
        tokens = _tokenize(text)
        idx = self._n_docs
        self._docs.append(tokens)
        self._doc_lens.append(len(tokens))
        self._n_docs += 1
        self._avg_dl = sum(self._doc_lens) / self._n_docs

        freq: Dict[str, int] = defaultdict(int)
        for t in tokens:
            freq[t] += 1
        for term, f in freq.items():
            self._inverted[term].append((idx, f))
        return idx

    def search(self, query: str, top_k: int = 10) -> List[Tuple[int, float]]:
        qtokens = _tokenize(query)
        scores: Dict[int, float] = defaultdict(float)
        for term in qtokens:
            postings = self._inverted.get(term, [])
            df = len(postings)
            if df == 0:
                continue
            idf = math.log(
                (self._n_docs - df + 0.5) / (df + 0.5) + 1.0
            )
            for doc_idx, tf in postings:
                dl = self._doc_lens[doc_idx]
                numerator = tf * (self.k1 + 1)
                denominator = tf + self.k1 * (
                    1 - self.b + self.b * dl / self._avg_dl
                )
                scores[doc_idx] += idf * numerator / denominator

        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return ranked[:top_k]


# ======================================================================
# Dense Vector Index (HNSW with numpy fallback)
# ======================================================================

class DenseIndex:
    """
    HNSW approximate nearest-neighbor index.  Falls back to brute-force
    cosine similarity over numpy arrays when ``hnswlib`` is not installed.
    """

    def __init__(self, dim: int = 0, ef_construction: int = 200, M: int = 16):
        self._dim = dim
        self._ef = ef_construction
        self._M = M
        self._vectors: List[np.ndarray] = []
        self._index: Any = None  # hnswlib.Index when available
        self._using_hnsw = False

    def _init_hnsw(self, dim: int) -> None:
        if _HAS_HNSWLIB and dim > 0:
            self._index = hnswlib.Index(space="cosine", dim=dim)
            self._index.init_index(
                max_elements=100_000, ef_construction=self._ef, M=self._M,
            )
            self._index.set_ef(128)
            self._using_hnsw = True

    def add(self, vector: List[float]) -> int:
        arr = np.array(vector, dtype=np.float32)
        idx = len(self._vectors)
        self._vectors.append(arr)

        if self._dim == 0:
            self._dim = len(vector)
            self._init_hnsw(self._dim)

        if self._using_hnsw:
            current_max = self._index.get_max_elements()
            if idx >= current_max:
                self._index.resize_index(current_max * 2)
            self._index.add_items(arr.reshape(1, -1), np.array([idx]))
        return idx

    def search(self, query_vector: List[float], top_k: int = 10) -> List[Tuple[int, float]]:
        if not self._vectors:
            return []
        q = np.array(query_vector, dtype=np.float32)

        if self._using_hnsw and self._index.get_current_count() > 0:
            k = min(top_k, self._index.get_current_count())
            labels, distances = self._index.knn_query(q.reshape(1, -1), k=k)
            return [(int(labels[0][i]), 1.0 - float(distances[0][i]))
                    for i in range(len(labels[0]))]

        # Brute-force fallback
        mat = np.stack(self._vectors)
        q_norm = q / (np.linalg.norm(q) + 1e-10)
        norms = np.linalg.norm(mat, axis=1, keepdims=True) + 1e-10
        cosines = (mat / norms) @ q_norm
        top_idx = np.argsort(-cosines)[:top_k]
        return [(int(i), float(cosines[i])) for i in top_idx]


# ======================================================================
# Reciprocal Rank Fusion
# ======================================================================

def reciprocal_rank_fusion(
    *rankings: List[Tuple[int, float]],
    k: int = 60,
) -> List[Tuple[int, float]]:
    """
    Merge multiple ranked lists using RRF (Cormack et al., 2009).
    ``k`` is the constant that dampens the contribution of low-ranked items.
    """
    scores: Dict[int, float] = defaultdict(float)
    for ranking in rankings:
        for rank, (doc_id, _score) in enumerate(ranking):
            scores[doc_id] += 1.0 / (k + rank + 1)
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)


# ======================================================================
# Document store
# ======================================================================

@dataclass
class Document:
    text: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    doc_id: int = -1


# ======================================================================
# HybridRAG
# ======================================================================

class HybridRAG:
    """
    Production-grade hybrid RAG combining BM25 + dense HNSW retrieval,
    Reciprocal Rank Fusion, and optional LLM-based reranking.

    Example:
        >>> rag = HybridRAG(llm_model="mistral", embedding_model="nomic-embed-text")
        >>> rag.add_document("Python was created by Guido van Rossum in 1991.")
        >>> answer = rag.query("Who created Python?")
    """

    def __init__(
        self,
        llm_model: str,
        embedding_model: Optional[str] = None,
        client: Optional[Any] = None,
        chunker: Optional[RecursiveChunker] = None,
        top_k: int = 5,
        rerank: bool = True,
        rerank_top_n: int = 15,
        rrf_k: int = 60,
    ):
        from .client import OllamaClient
        self.client: OllamaClient = client or OllamaClient()
        self.llm_model = llm_model
        self.embedding_model = embedding_model or llm_model
        self.chunker = chunker or RecursiveChunker()
        self.top_k = top_k
        self.rerank = rerank
        self.rerank_top_n = rerank_top_n
        self.rrf_k = rrf_k

        self._documents: List[Document] = []
        self._chunks: List[str] = []
        self._chunk_to_doc: List[int] = []  # chunk_idx -> doc_idx
        self._bm25 = BM25Index()
        self._dense = DenseIndex()

    @property
    def document_count(self) -> int:
        return len(self._documents)

    @property
    def chunk_count(self) -> int:
        return len(self._chunks)

    def add_document(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> int:
        doc = Document(text=text, metadata=metadata or {}, doc_id=len(self._documents))
        self._documents.append(doc)

        chunks = self.chunker.chunk(text)
        for chunk in chunks:
            cidx = len(self._chunks)
            self._chunks.append(chunk)
            self._chunk_to_doc.append(doc.doc_id)
            self._bm25.add(chunk)
            embedding = self.client.embeddings(self.embedding_model, chunk)
            self._dense.add(embedding)
        return doc.doc_id

    def add_documents(self, docs: List[Dict[str, Any]]) -> List[int]:
        ids = []
        for d in docs:
            ids.append(self.add_document(d["text"], d.get("metadata")))
        return ids

    def search(
        self,
        query: str,
        top_k: Optional[int] = None,
        metadata_filter: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Hybrid search returning ranked chunks with scores.
        """
        k = top_k or self.top_k
        n_candidates = max(k * 3, self.rerank_top_n)

        bm25_results = self._bm25.search(query, top_k=n_candidates)
        query_emb = self.client.embeddings(self.embedding_model, query)
        dense_results = self._dense.search(query_emb, top_k=n_candidates)

        fused = reciprocal_rank_fusion(
            bm25_results, dense_results, k=self.rrf_k,
        )

        if metadata_filter:
            fused = [
                (cid, score) for cid, score in fused
                if self._matches_filter(cid, metadata_filter)
            ]

        if self.rerank and len(fused) > k:
            candidates = fused[: self.rerank_top_n]
            fused = self._llm_rerank(query, candidates)

        results = []
        for chunk_idx, score in fused[:k]:
            doc_idx = self._chunk_to_doc[chunk_idx]
            results.append({
                "chunk": self._chunks[chunk_idx],
                "chunk_idx": chunk_idx,
                "doc_id": doc_idx,
                "metadata": self._documents[doc_idx].metadata,
                "score": score,
            })
        return results

    def query(
        self,
        question: str,
        top_k: Optional[int] = None,
        metadata_filter: Optional[Dict[str, Any]] = None,
        stream: bool = False,
    ) -> str:
        """Retrieve context and generate an answer."""
        results = self.search(question, top_k=top_k, metadata_filter=metadata_filter)
        context = "\n\n".join(
            f"[{i+1}] {r['chunk']}" for i, r in enumerate(results)
        )
        prompt = (
            "Answer the question using ONLY the provided context. "
            "If the context does not contain the answer, say so.\n\n"
            f"Context:\n{context}\n\nQuestion: {question}\n\nAnswer:"
        )
        if stream:
            parts: List[str] = []
            for chunk in self.client.stream_generate(
                self.llm_model, prompt, temperature=0.3,
            ):
                print(chunk, end="", flush=True)
                parts.append(chunk)
            print()
            return "".join(parts)

        return self.client.generate(self.llm_model, prompt, temperature=0.3)

    # ------------------------------------------------------------------
    # Reranking
    # ------------------------------------------------------------------

    def _llm_rerank(
        self, query: str, candidates: List[Tuple[int, float]],
    ) -> List[Tuple[int, float]]:
        """Use the LLM to rerank candidate chunks by relevance."""
        scored: List[Tuple[int, float]] = []
        for chunk_idx, _fusion_score in candidates:
            chunk_text = self._chunks[chunk_idx]
            prompt = (
                "Rate the relevance of the following passage to the query "
                "on a scale of 1 to 5 (1=irrelevant, 5=highly relevant). "
                "Respond with ONLY the number.\n\n"
                f"Query: {query}\n\nPassage: {chunk_text}\n\nRelevance score:"
            )
            try:
                resp = self.client.generate(
                    self.llm_model, prompt, temperature=0.0, max_tokens=5,
                )
                numbers = re.findall(r"[1-5]", resp)
                score = int(numbers[0]) if numbers else 3
            except Exception:
                score = 3
            scored.append((chunk_idx, float(score)))
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored

    def _matches_filter(self, chunk_idx: int, filt: Dict[str, Any]) -> bool:
        doc_idx = self._chunk_to_doc[chunk_idx]
        meta = self._documents[doc_idx].metadata
        return all(meta.get(k) == v for k, v in filt.items())

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save(self, path: str) -> None:
        """Save the document store to a JSON file (excluding HNSW index)."""
        data = {
            "documents": [asdict(d) for d in self._documents],
            "chunks": self._chunks,
            "chunk_to_doc": self._chunk_to_doc,
            "vectors": [v.tolist() for v in self._dense._vectors],
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f)

    def load(self, path: str) -> None:
        """Load document store from a JSON file and rebuild indices."""
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self._documents = [
            Document(**d) for d in data["documents"]
        ]
        self._chunks = data["chunks"]
        self._chunk_to_doc = data["chunk_to_doc"]

        self._bm25 = BM25Index()
        self._dense = DenseIndex()
        for i, chunk in enumerate(self._chunks):
            self._bm25.add(chunk)
        for vec in data["vectors"]:
            self._dense.add(vec)
