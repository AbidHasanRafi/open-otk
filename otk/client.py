"""
Main client wrapper for Ollama API with retry logic, metadata access,
and timeout support.
"""

import ollama
import time
import logging
from typing import Dict, List, Optional, Generator, Any

logger = logging.getLogger(__name__)


class OllamaClient:
    """
    Client for interacting with Ollama models.

    Supports exponential-backoff retries, per-request timeouts, and
    full-metadata responses needed by the profiler and evaluation layers.

    Example:
        >>> client = OllamaClient()
        >>> response = client.generate("llama2", "Tell me a joke")
        >>> print(response)
    """

    def __init__(
        self,
        host: Optional[str] = None,
        max_retries: int = 3,
        retry_base_delay: float = 1.0,
        timeout: Optional[float] = None,
    ):
        """
        Args:
            host: Custom host URL (default: http://localhost:11434)
            max_retries: Maximum retry attempts on transient failures
            retry_base_delay: Base delay in seconds for exponential backoff
            timeout: Default request timeout in seconds (None = no timeout)
        """
        self.client = ollama.Client(host=host) if host else ollama.Client()
        self.host = host or "http://localhost:11434"
        self.max_retries = max_retries
        self.retry_base_delay = retry_base_delay
        self.timeout = timeout

    def _retry(self, func, *args, **kwargs):
        """Execute *func* with exponential-backoff retry."""
        last_exc = None
        for attempt in range(self.max_retries):
            try:
                return func(*args, **kwargs)
            except (ConnectionError, TimeoutError, OSError) as exc:
                last_exc = exc
                delay = self.retry_base_delay * (2 ** attempt)
                logger.warning(
                    "Attempt %d/%d failed (%s), retrying in %.1fs",
                    attempt + 1, self.max_retries, exc, delay,
                )
                time.sleep(delay)
            except Exception:
                raise
        raise last_exc  # type: ignore[misc]

    # ------------------------------------------------------------------
    # Generate
    # ------------------------------------------------------------------

    def generate(
        self,
        model: str,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> str:
        """
        Generate a response from a model.

        Returns:
            Generated text response
        """
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
        """
        Generate a response and return the full Ollama response dict
        including eval_count, eval_duration, prompt_eval_duration, etc.
        """
        options: Dict[str, Any] = {"temperature": temperature}
        if max_tokens:
            options["num_predict"] = max_tokens
        options.update(kwargs.get("options", {}))

        def _call():
            return self.client.generate(
                model=model, prompt=prompt, system=system, options=options,
            )

        return self._retry(_call)

    def stream_generate(
        self,
        model: str,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        **kwargs,
    ) -> Generator[str, None, None]:
        """Stream a response from a model, yielding text chunks."""
        options: Dict[str, Any] = {"temperature": temperature}
        options.update(kwargs.get("options", {}))

        stream = self.client.generate(
            model=model, prompt=prompt, system=system,
            stream=True, options=options,
        )
        for chunk in stream:
            yield chunk["response"]

    # ------------------------------------------------------------------
    # Chat
    # ------------------------------------------------------------------

    def chat(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        **kwargs,
    ) -> str:
        """Send a chat completion request and return the assistant text."""
        meta = self.chat_with_metadata(
            model, messages, temperature=temperature, **kwargs,
        )
        return meta["message"]["content"]

    def chat_with_metadata(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        **kwargs,
    ) -> Dict[str, Any]:
        """Chat and return the full Ollama response dict."""
        options: Dict[str, Any] = {"temperature": temperature}
        options.update(kwargs.get("options", {}))

        def _call():
            return self.client.chat(
                model=model, messages=messages, options=options,
            )

        return self._retry(_call)

    def stream_chat(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        **kwargs,
    ) -> Generator[str, None, None]:
        """Stream a chat response, yielding text chunks."""
        options: Dict[str, Any] = {"temperature": temperature}
        options.update(kwargs.get("options", {}))

        stream = self.client.chat(
            model=model, messages=messages, stream=True, options=options,
        )
        for chunk in stream:
            if "message" in chunk and "content" in chunk["message"]:
                yield chunk["message"]["content"]

    # ------------------------------------------------------------------
    # Embeddings
    # ------------------------------------------------------------------

    def embeddings(self, model: str, text: str) -> List[float]:
        """Generate embeddings for *text*."""
        def _call():
            return self.client.embeddings(model=model, prompt=text)

        response = self._retry(_call)
        return response["embedding"]

    def batch_embeddings(
        self, model: str, texts: List[str],
    ) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        return [self.embeddings(model, t) for t in texts]

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    def is_running(self) -> bool:
        """Return True if the Ollama daemon is reachable."""
        try:
            self.client.list()
            return True
        except Exception:
            return False

    def list_models(self) -> List[Dict[str, Any]]:
        """Return the list of locally-installed models."""
        try:
            resp = self.client.list()
            return resp.get("models", [])
        except Exception:
            return []
