"""
Utility functions for working with Ollama models.

Includes improved token estimation, text chunking, prompt templating,
and formatting helpers.
"""

import re
from typing import List, Dict, Any, Optional

# Attempt to load tiktoken for accurate BPE token counting
try:
    import tiktoken
    _TIKTOKEN_ENC = tiktoken.get_encoding("cl100k_base")
    _HAS_TIKTOKEN = True
except Exception:
    _TIKTOKEN_ENC = None
    _HAS_TIKTOKEN = False


def estimate_tokens(text: str) -> int:
    """
    Estimate the token count for *text*.

    Uses tiktoken (cl100k_base) when available; otherwise falls back to
    a heuristic that splits on whitespace + punctuation boundaries
    (~1.3 tokens per whitespace-delimited word for English).
    """
    if _HAS_TIKTOKEN and _TIKTOKEN_ENC is not None:
        return len(_TIKTOKEN_ENC.encode(text))

    words = re.findall(r"\S+", text)
    return max(1, int(len(words) * 1.3))


def format_response(response: str, max_width: int = 80) -> str:
    """Word-wrap *response* to *max_width* columns."""
    lines = response.split("\n")
    formatted_lines: List[str] = []
    for line in lines:
        if len(line) <= max_width:
            formatted_lines.append(line)
        else:
            words = line.split()
            current_line: List[str] = []
            current_length = 0
            for word in words:
                if current_length + len(word) + 1 <= max_width:
                    current_line.append(word)
                    current_length += len(word) + 1
                else:
                    formatted_lines.append(" ".join(current_line))
                    current_line = [word]
                    current_length = len(word)
            if current_line:
                formatted_lines.append(" ".join(current_line))
    return "\n".join(formatted_lines)


def chunk_text(
    text: str,
    chunk_size: int = 1000,
    overlap: int = 100,
) -> List[str]:
    """Split *text* into overlapping character-based chunks."""
    chunks: List[str] = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start = end - overlap
    return chunks


def chunk_text_by_tokens(
    text: str,
    max_tokens: int = 256,
    overlap_tokens: int = 32,
) -> List[str]:
    """
    Split *text* into chunks respecting a token budget.

    Splits on sentence boundaries when possible to maintain coherence.
    """
    from .rag import RecursiveChunker
    chunker = RecursiveChunker(
        max_tokens=max_tokens, overlap_tokens=overlap_tokens,
        token_counter=estimate_tokens,
    )
    return chunker.chunk(text)


def create_prompt_template(
    template: str,
    variables: Dict[str, Any],
) -> str:
    """Fill ``{variable}`` placeholders in *template*."""
    result = template
    for key, value in variables.items():
        result = result.replace(f"{{{key}}}", str(value))
    return result


def extract_code_blocks(text: str) -> List[Dict[str, str]]:
    """Extract fenced code blocks from markdown-formatted *text*."""
    pattern = r"```(\w+)?\n(.*?)```"
    matches = re.findall(pattern, text, re.DOTALL)
    return [{"language": lang or "text", "code": code.strip()} for lang, code in matches]


def clean_response(response: str) -> str:
    """Clean up excessive whitespace in *response*."""
    response = re.sub(r"\n{3,}", "\n\n", response)
    response = "\n".join(line.rstrip() for line in response.split("\n"))
    return response.strip()


def create_system_prompt(
    role: str,
    context: Optional[str] = None,
    constraints: Optional[List[str]] = None,
) -> str:
    """Build a structured system prompt."""
    parts = [f"You are a {role}."]
    if context:
        parts.append(f"\nContext: {context}")
    if constraints:
        parts.append("\nPlease follow these guidelines:")
        for i, c in enumerate(constraints, 1):
            parts.append(f"{i}. {c}")
    return "\n".join(parts)


def batch_process(
    items: List[str],
    process_func,
    batch_size: int = 10,
    show_progress: bool = True,
) -> List[Any]:
    """Process *items* in batches, applying *process_func* to each."""
    results: List[Any] = []
    total = len(items)
    for i in range(0, total, batch_size):
        batch = items[i : i + batch_size]
        if show_progress:
            print(
                f"Processing batch "
                f"{i // batch_size + 1}/"
                f"{(total + batch_size - 1) // batch_size}..."
            )
        for item in batch:
            results.append(process_func(item))
    return results


def validate_model_name(model_name: str) -> bool:
    """Validate that *model_name* follows Ollama naming conventions."""
    pattern = r"^[a-zA-Z0-9_-]+(?::[a-zA-Z0-9_.-]+)?$"
    return bool(re.match(pattern, model_name))


def format_chat_history(messages: List[Dict[str, str]]) -> str:
    """Pretty-print a list of chat messages."""
    parts: List[str] = []
    for msg in messages:
        role = msg["role"].upper()
        content = msg["content"]
        if role == "SYSTEM":
            parts.append(f"[SYSTEM]\n{content}\n")
        elif role == "USER":
            parts.append(f"USER:\n{content}\n")
        elif role == "ASSISTANT":
            parts.append(f"ASSISTANT:\n{content}\n")
    return "\n".join(parts)
