"""Tests for the enhanced OllamaClient."""

import pytest
from tests.mock_ollama import MockOllamaClient


class TestOllamaClient:
    def test_generate_returns_text(self, mock_client):
        result = mock_client.generate("mistral", "Hello")
        assert isinstance(result, str)
        assert "Mock response" in result

    def test_generate_with_metadata_has_keys(self, mock_client):
        meta = mock_client.generate_with_metadata("mistral", "Hello")
        assert "response" in meta
        assert "eval_count" in meta
        assert "eval_duration" in meta
        assert "total_duration" in meta
        assert "prompt_eval_duration" in meta

    def test_chat_returns_text(self, mock_client):
        messages = [{"role": "user", "content": "Hi"}]
        result = mock_client.chat("mistral", messages)
        assert "Mock chat reply" in result

    def test_chat_with_metadata(self, mock_client):
        messages = [{"role": "user", "content": "Hi"}]
        meta = mock_client.chat_with_metadata("mistral", messages)
        assert "message" in meta
        assert meta["message"]["role"] == "assistant"

    def test_stream_generate(self, mock_client):
        chunks = list(mock_client.stream_generate("mistral", "Hello"))
        assert len(chunks) > 0
        assert all(isinstance(c, str) for c in chunks)

    def test_stream_chat(self, mock_client):
        messages = [{"role": "user", "content": "Hi"}]
        chunks = list(mock_client.stream_chat("mistral", messages))
        assert len(chunks) > 0

    def test_embeddings(self, mock_client):
        emb = mock_client.embeddings("nomic-embed-text", "test")
        assert isinstance(emb, list)
        assert len(emb) == 8
        assert all(isinstance(v, float) for v in emb)

    def test_is_running(self, mock_client):
        assert mock_client.is_running() is True

    def test_list_models(self, mock_client):
        models = mock_client.list_models()
        assert len(models) == 4
        names = [m["name"] for m in models]
        assert "mistral:latest" in names

    def test_batch_embeddings(self, mock_client):
        results = mock_client.batch_embeddings("nomic-embed-text", ["a", "b"])
        assert len(results) == 2
        assert results[0] != results[1]

    def test_call_log(self, mock_client):
        mock_client.generate("m", "p")
        mock_client.chat("m", [{"role": "user", "content": "x"}])
        assert len(mock_client._call_log) == 2
        assert mock_client._call_log[0]["method"] == "generate"
        assert mock_client._call_log[1]["method"] == "chat"
