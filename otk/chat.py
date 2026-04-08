"""
Chat session with conversation history, token-budget trimming,
auto response processing for both streamed and non-streamed output,
and conversation branching.
"""

import json
import copy
from typing import List, Dict, Optional, Generator

from .client import OllamaClient
from .response_handlers import AutoModelHandler, ProcessedResponse
from .utils import estimate_tokens


class ChatSession:
    """
    Maintain a chat session with conversation history.

    History can be trimmed by message count **or** by a token budget,
    whichever limit is hit first.  Response auto-processing (thinking
    tag removal, etc.) now applies to both streamed and non-streamed
    output.

    Example:
        >>> session = ChatSession("llama2")
        >>> response = session.send("Hello!")
        >>> branch = session.fork()  # create a branch for exploration
    """

    def __init__(
        self,
        model: str,
        system_message: Optional[str] = None,
        client: Optional[OllamaClient] = None,
        temperature: float = 0.7,
        max_history: int = 50,
        max_history_tokens: Optional[int] = None,
        auto_process: bool = True,
    ):
        self.model = model
        self.client = client or OllamaClient()
        self.temperature = temperature
        self.max_history = max_history
        self.max_history_tokens = max_history_tokens
        self.auto_process = auto_process
        self.response_handler = AutoModelHandler() if auto_process else None
        self.messages: List[Dict[str, str]] = []
        self.last_processed_response: Optional[ProcessedResponse] = None

        if system_message:
            self.messages.append({"role": "system", "content": system_message})

    def send(self, message: str, stream: bool = False) -> str:
        """Send a message and return the (optionally processed) response."""
        self.messages.append({"role": "user", "content": message})
        self._trim_history()

        if stream:
            response_text = ""
            for chunk in self.client.stream_chat(
                model=self.model,
                messages=self.messages,
                temperature=self.temperature,
            ):
                print(chunk, end="", flush=True)
                response_text += chunk
            print()
        else:
            response_text = self.client.chat(
                model=self.model,
                messages=self.messages,
                temperature=self.temperature,
            )

        final_response = self._process(response_text)
        self.messages.append({"role": "assistant", "content": final_response})
        return final_response

    def send_stream(self, message: str) -> Generator[str, None, None]:
        """Send a message and yield response chunks. Auto-processes the full response at the end."""
        self.messages.append({"role": "user", "content": message})
        self._trim_history()

        response_text = ""
        for chunk in self.client.stream_chat(
            model=self.model,
            messages=self.messages,
            temperature=self.temperature,
        ):
            response_text += chunk
            yield chunk

        final_response = self._process(response_text)
        self.messages.append({"role": "assistant", "content": final_response})

    def _process(self, raw: str) -> str:
        if self.auto_process and self.response_handler:
            processed = self.response_handler.process_response(raw, self.model)
            self.last_processed_response = processed
            if processed.thinking:
                print(f"\n[Model showed {len(processed.thinking)} thinking step(s)]")
            return processed.content
        self.last_processed_response = None
        return raw

    # ------------------------------------------------------------------
    # History management
    # ------------------------------------------------------------------

    def _trim_history(self) -> None:
        """Trim history by message count and/or token budget."""
        has_system = (
            self.messages and self.messages[0]["role"] == "system"
        )

        # Message-count trim
        if len(self.messages) > self.max_history:
            if has_system:
                self.messages = [self.messages[0]] + self.messages[-(self.max_history - 1):]
            else:
                self.messages = self.messages[-self.max_history:]

        # Token-budget trim
        if self.max_history_tokens is not None:
            total = sum(estimate_tokens(m["content"]) for m in self.messages)
            while total > self.max_history_tokens and len(self.messages) > (2 if has_system else 1):
                removed_idx = 1 if has_system else 0
                total -= estimate_tokens(self.messages[removed_idx]["content"])
                self.messages.pop(removed_idx)

    def clear_history(self, keep_system: bool = True) -> None:
        if keep_system and self.messages and self.messages[0]["role"] == "system":
            self.messages = [self.messages[0]]
        else:
            self.messages = []

    def get_history(self) -> List[Dict[str, str]]:
        return self.messages.copy()

    def get_last_thinking(self) -> Optional[List[str]]:
        if self.last_processed_response and self.last_processed_response.thinking:
            return self.last_processed_response.thinking
        return None

    def get_last_metadata(self) -> Optional[Dict]:
        if self.last_processed_response:
            return self.last_processed_response.metadata
        return None

    def set_system_message(self, message: str) -> None:
        if self.messages and self.messages[0]["role"] == "system":
            self.messages.pop(0)
        self.messages.insert(0, {"role": "system", "content": message})

    # ------------------------------------------------------------------
    # Branching
    # ------------------------------------------------------------------

    def fork(self) -> "ChatSession":
        """Create a copy of this session for exploring alternative continuations."""
        branch = ChatSession(
            model=self.model,
            client=self.client,
            temperature=self.temperature,
            max_history=self.max_history,
            max_history_tokens=self.max_history_tokens,
            auto_process=self.auto_process,
        )
        branch.messages = copy.deepcopy(self.messages)
        return branch

    # ------------------------------------------------------------------
    # I/O
    # ------------------------------------------------------------------

    def export_history(self, filepath: str) -> None:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(
                {"model": self.model, "temperature": self.temperature,
                 "messages": self.messages},
                f, indent=2, ensure_ascii=False,
            )

    def load_history(self, filepath: str) -> None:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.model = data.get("model", self.model)
            self.temperature = data.get("temperature", self.temperature)
            self.messages = data.get("messages", [])

    def token_count(self) -> int:
        """Return the estimated total token count of the conversation."""
        return sum(estimate_tokens(m["content"]) for m in self.messages)
