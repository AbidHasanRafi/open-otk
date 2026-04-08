"""
Intelligent task-aware model router with performance learning.

Classifies incoming prompts by task type, maintains a capability matrix
for known model families, and uses an epsilon-greedy multi-armed bandit
strategy informed by historical latency and quality data stored in SQLite.
"""

import os
import re
import random
import sqlite3
import time
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# ======================================================================
# Task taxonomy
# ======================================================================

class TaskType(Enum):
    CODE = "code"
    CREATIVE_WRITING = "creative_writing"
    FACTUAL_QA = "factual_qa"
    SUMMARIZATION = "summarization"
    TRANSLATION = "translation"
    MATH = "math"
    GENERAL = "general"


# Keyword sets for lightweight classification (no LLM call required)
_TASK_KEYWORDS: Dict[TaskType, List[str]] = {
    TaskType.CODE: [
        "code", "function", "class", "implement", "debug", "programming",
        "python", "javascript", "java", "rust", "sql", "html", "css",
        "algorithm", "compile", "syntax", "refactor", "bug", "api",
    ],
    TaskType.CREATIVE_WRITING: [
        "story", "poem", "creative", "fiction", "write a", "imagine",
        "narrative", "character", "dialogue", "plot", "essay",
    ],
    TaskType.FACTUAL_QA: [
        "what is", "who is", "when did", "where is", "how does",
        "explain", "define", "describe", "why does", "fact",
    ],
    TaskType.SUMMARIZATION: [
        "summarize", "summarise", "summary", "tldr", "brief",
        "condense", "shorten", "key points", "main ideas",
    ],
    TaskType.TRANSLATION: [
        "translate", "translation", "convert to", "in french",
        "in spanish", "in german", "in chinese", "in japanese",
    ],
    TaskType.MATH: [
        "calculate", "solve", "equation", "math", "integral",
        "derivative", "probability", "statistics", "formula", "proof",
    ],
}


# ======================================================================
# Task Classifier
# ======================================================================

class TaskClassifier:
    """Classify a prompt into a ``TaskType`` using keyword matching."""

    @staticmethod
    def _keyword_matches(keyword: str, text: str) -> bool:
        """Word-boundary match to avoid partial hits (e.g. 'api' in 'capital')."""
        import re
        return bool(re.search(r'\b' + re.escape(keyword) + r'\b', text))

    def classify(self, prompt: str) -> TaskType:
        lower = prompt.lower()
        scores: Dict[TaskType, int] = {}
        for task, keywords in _TASK_KEYWORDS.items():
            scores[task] = sum(1 for kw in keywords if self._keyword_matches(kw, lower))
        best = max(scores, key=lambda t: scores[t])
        return best if scores[best] > 0 else TaskType.GENERAL

    def classify_with_confidence(
        self, prompt: str,
    ) -> Tuple[TaskType, float]:
        lower = prompt.lower()
        scores: Dict[TaskType, int] = {}
        for task, keywords in _TASK_KEYWORDS.items():
            scores[task] = sum(1 for kw in keywords if self._keyword_matches(kw, lower))
        total = sum(scores.values())
        if total == 0:
            return TaskType.GENERAL, 0.0
        best = max(scores, key=lambda t: scores[t])
        confidence = scores[best] / total
        return best, confidence


# ======================================================================
# Capability Matrix
# ======================================================================

_DEFAULT_CAPABILITIES: Dict[str, Dict[str, float]] = {
    "codellama":        {"code": 0.95, "general": 0.4, "math": 0.6},
    "deepseek-coder":   {"code": 0.95, "general": 0.5, "math": 0.7},
    "starcoder":        {"code": 0.9,  "general": 0.3},
    "phind-codellama":  {"code": 0.9,  "general": 0.4},
    "llama":            {"general": 0.8, "factual_qa": 0.8, "creative_writing": 0.7, "summarization": 0.8},
    "mistral":          {"general": 0.85, "factual_qa": 0.85, "code": 0.6, "summarization": 0.8},
    "qwen":             {"general": 0.8, "code": 0.7, "math": 0.75},
    "gemma":            {"general": 0.8, "factual_qa": 0.8, "creative_writing": 0.7},
    "phi":              {"general": 0.75, "code": 0.7, "math": 0.7},
    "deepseek-r1":      {"math": 0.9, "code": 0.8, "general": 0.7, "factual_qa": 0.8},
    "wizardcoder":      {"code": 0.85, "general": 0.4},
}


class CapabilityMatrix:
    """Map model name patterns to per-task capability scores (0-1)."""

    def __init__(self, overrides: Optional[Dict[str, Dict[str, float]]] = None):
        self._matrix = dict(_DEFAULT_CAPABILITIES)
        if overrides:
            self._matrix.update(overrides)

    def score(self, model_name: str, task: TaskType) -> float:
        """Return the capability score for *model_name* on *task*."""
        lower = model_name.lower()
        for pattern, caps in self._matrix.items():
            if pattern in lower:
                return caps.get(task.value, 0.5)
        return 0.5  # unknown model -> neutral

    def register(self, pattern: str, capabilities: Dict[str, float]) -> None:
        self._matrix[pattern] = capabilities


# ======================================================================
# Performance History (SQLite)
# ======================================================================

_HISTORY_TABLE = """
CREATE TABLE IF NOT EXISTS model_performance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    model TEXT NOT NULL,
    task_type TEXT NOT NULL,
    latency_ms REAL,
    quality_score REAL,
    timestamp REAL
)
"""


class PerformanceHistory:
    """SQLite-backed record of model performance by task type."""

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            db_path = os.path.join(
                os.path.expanduser("~"), ".otk", "router_history.db",
            )
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._conn = sqlite3.connect(db_path)
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(_HISTORY_TABLE)

    def record(
        self,
        model: str,
        task_type: str,
        latency_ms: float,
        quality_score: Optional[float] = None,
    ) -> None:
        self._conn.execute(
            "INSERT INTO model_performance "
            "(model, task_type, latency_ms, quality_score, timestamp) "
            "VALUES (?,?,?,?,?)",
            (model, task_type, latency_ms, quality_score, time.time()),
        )
        self._conn.commit()

    def avg_latency(self, model: str, task_type: str) -> Optional[float]:
        row = self._conn.execute(
            "SELECT AVG(latency_ms) as v FROM model_performance "
            "WHERE model=? AND task_type=?",
            (model, task_type),
        ).fetchone()
        return row["v"] if row and row["v"] is not None else None

    def avg_quality(self, model: str, task_type: str) -> Optional[float]:
        row = self._conn.execute(
            "SELECT AVG(quality_score) as v FROM model_performance "
            "WHERE model=? AND task_type=? AND quality_score IS NOT NULL",
            (model, task_type),
        ).fetchone()
        return row["v"] if row and row["v"] is not None else None

    def call_count(self, model: str, task_type: str) -> int:
        row = self._conn.execute(
            "SELECT COUNT(*) as c FROM model_performance "
            "WHERE model=? AND task_type=?",
            (model, task_type),
        ).fetchone()
        return row["c"] if row else 0

    def close(self) -> None:
        self._conn.close()


# ======================================================================
# Model Router
# ======================================================================

@dataclass
class RoutingDecision:
    selected_model: str
    task_type: TaskType
    score: float
    reason: str


class ModelRouter:
    """
    Automatically select the best available local model for a given prompt.

    Uses an epsilon-greedy strategy:
    - With probability ``epsilon``, pick a random model (exploration).
    - Otherwise, pick the model that maximises a weighted score of
      capability, historical quality, and inverse latency (exploitation).

    Example:
        >>> router = ModelRouter()
        >>> decision = router.route("Write a Python function to sort a list")
        >>> print(decision.selected_model, decision.task_type)
    """

    def __init__(
        self,
        client: Optional[Any] = None,
        capability_matrix: Optional[CapabilityMatrix] = None,
        history: Optional[PerformanceHistory] = None,
        epsilon: float = 0.1,
        alpha: float = 0.4,
        beta: float = 0.4,
        gamma: float = 0.2,
    ):
        from .client import OllamaClient
        self.client: OllamaClient = client or OllamaClient()
        self.classifier = TaskClassifier()
        self.capabilities = capability_matrix or CapabilityMatrix()
        self.history = history or PerformanceHistory()
        self.epsilon = epsilon
        self.alpha = alpha   # weight for capability score
        self.beta = beta     # weight for historical quality
        self.gamma = gamma   # weight for speed (1/latency)

    def route(self, prompt: str) -> RoutingDecision:
        """Select the best model for *prompt*."""
        task = self.classifier.classify(prompt)
        models = self._available_models()
        if not models:
            raise RuntimeError("No local models available")

        if random.random() < self.epsilon:
            chosen = random.choice(models)
            return RoutingDecision(
                selected_model=chosen, task_type=task,
                score=0.0, reason="exploration (epsilon-greedy)",
            )

        scored: List[Tuple[str, float]] = []
        for m in models:
            s = self._score_model(m, task)
            scored.append((m, s))
        scored.sort(key=lambda x: x[1], reverse=True)
        best_model, best_score = scored[0]
        return RoutingDecision(
            selected_model=best_model, task_type=task,
            score=best_score, reason="exploitation (highest score)",
        )

    def generate(self, prompt: str, **kwargs: Any) -> str:
        """Route + generate in one call, recording performance."""
        decision = self.route(prompt)
        t0 = time.perf_counter()
        response = self.client.generate(decision.selected_model, prompt, **kwargs)
        latency = (time.perf_counter() - t0) * 1000
        self.history.record(
            decision.selected_model, decision.task_type.value, latency,
        )
        return response

    def generate_with_fallback(
        self, prompt: str, max_attempts: int = 3, **kwargs: Any,
    ) -> Tuple[str, RoutingDecision]:
        """Try the top-N models in score order until one succeeds."""
        task = self.classifier.classify(prompt)
        models = self._available_models()
        scored = sorted(
            ((m, self._score_model(m, task)) for m in models),
            key=lambda x: x[1], reverse=True,
        )
        for model, score in scored[:max_attempts]:
            try:
                t0 = time.perf_counter()
                resp = self.client.generate(model, prompt, **kwargs)
                latency = (time.perf_counter() - t0) * 1000
                self.history.record(model, task.value, latency)
                return resp, RoutingDecision(
                    selected_model=model, task_type=task,
                    score=score, reason="fallback chain",
                )
            except Exception as exc:
                logger.warning("Model %s failed: %s, trying next", model, exc)

        raise RuntimeError(
            f"All {max_attempts} models failed for task {task.value}"
        )

    def _score_model(self, model: str, task: TaskType) -> float:
        cap = self.capabilities.score(model, task)
        avg_q = self.history.avg_quality(model, task.value)
        avg_l = self.history.avg_latency(model, task.value)

        quality = avg_q / 5.0 if avg_q else 0.5
        speed = 1.0 / (1.0 + (avg_l or 5000.0) / 1000.0)

        return self.alpha * cap + self.beta * quality + self.gamma * speed

    def _available_models(self) -> List[str]:
        raw = self.client.list_models()
        names: List[str] = []
        for m in raw:
            name = m.get("name") or m.get("model", "")
            if isinstance(name, str) and name:
                names.append(name)
        return names
