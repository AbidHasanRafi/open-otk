"""
Mock Ollama client for offline testing.

Provides deterministic responses without requiring a running Ollama daemon.
"""

from typing import Any, Dict, Generator, List, Optional


_MOCK_MODELS = [
    {"name": "mistral:latest", "size": 4_000_000_000},
    {"name": "llama3:latest", "size": 8_000_000_000},
    {"name": "codellama:latest", "size": 4_500_000_000},
    {"name": "nomic-embed-text:latest", "size": 300_000_000},
]

_MOCK_EMBEDDING_DIM = 8


def _mock_embedding(text: str) -> List[float]:
    """Deterministic pseudo-embedding based on text hash."""
    import hashlib
    h = hashlib.sha256(text.encode()).hexdigest()
    return [int(h[i * 2:(i + 1) * 2], 16) / 255.0 for i in range(_MOCK_EMBEDDING_DIM)]


class MockOllamaClient:
    """
    Drop-in replacement for ``otk.OllamaClient`` that never hits the network.
    """

    def __init__(self, host: Optional[str] = None, **kwargs):
        self.host = host or "http://localhost:11434"
        self.max_retries = kwargs.get("max_retries", 1)
        self.retry_base_delay = kwargs.get("retry_base_delay", 0)
        self.timeout = kwargs.get("timeout", None)
        self._call_log: List[Dict[str, Any]] = []

    def generate(
        self,
        model: str,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> str:
        meta = self.generate_with_metadata(
            model, prompt, system=system, temperature=temperature,
            max_tokens=max_tokens, **kwargs,
        )
        return meta["response"]

    def generate_with_metadata(
        self,
        model: str,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        self._call_log.append({
            "method": "generate", "model": model, "prompt": prompt,
        })
        text = f"Mock response to: {prompt[:50]}"
        return {
            "response": text,
            "model": model,
            "eval_count": len(text) // 4,
            "eval_duration": 100_000_000,
            "prompt_eval_count": len(prompt) // 4,
            "prompt_eval_duration": 50_000_000,
            "total_duration": 150_000_000,
        }

    def stream_generate(
        self,
        model: str,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        **kwargs,
    ) -> Generator[str, None, None]:
        self._call_log.append({"method": "stream_generate", "model": model})
        for word in f"Mock streamed response to {prompt[:30]}".split():
            yield word + " "

    def chat(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        **kwargs,
    ) -> str:
        meta = self.chat_with_metadata(model, messages, temperature=temperature, **kwargs)
        return meta["message"]["content"]

    def chat_with_metadata(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        **kwargs,
    ) -> Dict[str, Any]:
        self._call_log.append({"method": "chat", "model": model})
        last_msg = messages[-1]["content"] if messages else ""
        text = f"Mock chat reply to: {last_msg[:50]}"
        return {
            "message": {"role": "assistant", "content": text},
            "model": model,
            "eval_count": len(text) // 4,
            "eval_duration": 80_000_000,
            "prompt_eval_duration": 40_000_000,
            "total_duration": 120_000_000,
        }

    def stream_chat(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        **kwargs,
    ) -> Generator[str, None, None]:
        self._call_log.append({"method": "stream_chat", "model": model})
        for word in "Mock streamed chat reply".split():
            yield word + " "

    def embeddings(self, model: str, text: str) -> List[float]:
        self._call_log.append({"method": "embeddings", "model": model})
        return _mock_embedding(text)

    def batch_embeddings(self, model: str, texts: List[str]) -> List[List[float]]:
        return [self.embeddings(model, t) for t in texts]

    def is_running(self) -> bool:
        return True

    def list_models(self) -> List[Dict[str, Any]]:
        return list(_MOCK_MODELS)
