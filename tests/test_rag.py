"""Tests for the Hybrid RAG engine components."""

import pytest
import numpy as np
from otk.rag import (
    RecursiveChunker,
    BM25Index,
    DenseIndex,
    reciprocal_rank_fusion,
    HybridRAG,
)
from tests.mock_ollama import MockOllamaClient


class TestRecursiveChunker:
    def test_short_text_single_chunk(self):
        chunker = RecursiveChunker(max_tokens=100)
        chunks = chunker.chunk("Hello world.")
        assert len(chunks) == 1
        assert chunks[0] == "Hello world."

    def test_paragraph_splitting(self):
        para = "This is a moderately long paragraph with enough words to exceed a small token budget easily."
        text = f"{para}\n\n{para}\n\n{para}"
        chunker = RecursiveChunker(max_tokens=15, overlap_tokens=0)
        chunks = chunker.chunk(text)
        assert len(chunks) >= 2

    def test_sentence_splitting_long_paragraph(self):
        sentences = " ".join([f"Sentence number {i} is here." for i in range(50)])
        chunker = RecursiveChunker(max_tokens=30, overlap_tokens=4)
        chunks = chunker.chunk(sentences)
        assert len(chunks) > 1
        for chunk in chunks:
            assert len(chunk) > 0

    def test_overlap_produces_repeated_content(self):
        text = "A. B. C. D. E. F. G. H. I. J."
        chunker = RecursiveChunker(max_tokens=8, overlap_tokens=4)
        chunks = chunker.chunk(text)
        if len(chunks) >= 2:
            # overlap means some words from chunk N appear in chunk N+1
            words_0 = set(chunks[0].split())
            words_1 = set(chunks[1].split())
            assert len(words_0 & words_1) > 0


class TestBM25Index:
    def test_add_and_search(self):
        idx = BM25Index()
        idx.add("the quick brown fox")
        idx.add("the lazy dog")
        idx.add("quick brown rabbit")
        results = idx.search("quick fox", top_k=2)
        assert len(results) <= 2
        top_id = results[0][0]
        assert top_id == 0  # "the quick brown fox" should rank first

    def test_empty_index(self):
        idx = BM25Index()
        results = idx.search("anything")
        assert results == []

    def test_no_match(self):
        idx = BM25Index()
        idx.add("hello world")
        results = idx.search("zzzzz")
        assert results == []


class TestDenseIndex:
    def test_add_and_search(self):
        idx = DenseIndex()
        idx.add([1.0, 0.0, 0.0])
        idx.add([0.0, 1.0, 0.0])
        idx.add([0.9, 0.1, 0.0])
        results = idx.search([1.0, 0.0, 0.0], top_k=2)
        assert len(results) == 2
        # closest should be index 0 or 2
        top_ids = [r[0] for r in results]
        assert 0 in top_ids

    def test_empty_index(self):
        idx = DenseIndex()
        results = idx.search([1.0, 0.0])
        assert results == []


class TestReciprocalRankFusion:
    def test_basic_fusion(self):
        rank_a = [(0, 0.9), (1, 0.7), (2, 0.5)]
        rank_b = [(2, 0.95), (0, 0.6), (1, 0.3)]
        fused = reciprocal_rank_fusion(rank_a, rank_b, k=60)
        ids = [doc_id for doc_id, _ in fused]
        assert 0 in ids
        assert 2 in ids
        # doc 0 ranked 1st in A and 2nd in B -> should score well
        # doc 2 ranked 1st in B and 3rd in A -> should also score well

    def test_single_ranking(self):
        rank = [(5, 1.0), (3, 0.5)]
        fused = reciprocal_rank_fusion(rank, k=60)
        assert fused[0][0] == 5


class TestHybridRAG:
    def test_add_document_and_search(self):
        client = MockOllamaClient()
        rag = HybridRAG(
            llm_model="mistral", embedding_model="nomic-embed-text",
            client=client, rerank=False, top_k=2,
        )
        rag.add_document("Python is a programming language.", {"topic": "python"})
        rag.add_document("Java is a programming language.", {"topic": "java"})
        rag.add_document("Cats are cute animals.", {"topic": "animals"})

        results = rag.search("programming language")
        assert len(results) <= 2
        assert all("chunk" in r for r in results)

    def test_metadata_filter(self):
        client = MockOllamaClient()
        rag = HybridRAG(
            llm_model="mistral", embedding_model="nomic-embed-text",
            client=client, rerank=False, top_k=10,
        )
        rag.add_document("Doc A", {"category": "tech"})
        rag.add_document("Doc B", {"category": "sports"})

        results = rag.search("doc", metadata_filter={"category": "tech"})
        for r in results:
            assert r["metadata"]["category"] == "tech"

    def test_document_count(self):
        client = MockOllamaClient()
        rag = HybridRAG(
            llm_model="m", embedding_model="e", client=client, rerank=False,
        )
        rag.add_document("One")
        rag.add_document("Two")
        assert rag.document_count == 2
        assert rag.chunk_count >= 2

    def test_save_and_load(self, tmp_path):
        client = MockOllamaClient()
        rag = HybridRAG(
            llm_model="m", embedding_model="e", client=client, rerank=False,
        )
        rag.add_document("Document one", {"id": 1})
        rag.add_document("Document two", {"id": 2})

        path = str(tmp_path / "rag.json")
        rag.save(path)

        rag2 = HybridRAG(
            llm_model="m", embedding_model="e", client=client, rerank=False,
        )
        rag2.load(path)
        assert rag2.document_count == 2
        assert rag2.chunk_count == rag.chunk_count
