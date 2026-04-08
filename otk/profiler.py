"""
Resource profiling and telemetry for Ollama inference.

Tracks tokens/sec, time-to-first-token, CPU/RAM usage, and optional
GPU memory.  All metrics are persisted to a local SQLite database for
longitudinal analysis.
"""

import os
import time
import sqlite3
import subprocess
import logging
from contextlib import contextmanager
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

try:
    import psutil
    _HAS_PSUTIL = True
except ImportError:
    _HAS_PSUTIL = False


@dataclass
class InferenceMetrics:
    """Metrics captured for a single inference call."""
    model: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    prompt_eval_duration_ms: float = 0.0
    eval_duration_ms: float = 0.0
    total_duration_ms: float = 0.0
    tokens_per_second: float = 0.0
    time_to_first_token_ms: float = 0.0
    wall_clock_ms: float = 0.0
    cpu_percent: float = 0.0
    ram_used_mb: float = 0.0
    gpu_mem_used_mb: Optional[float] = None
    timestamp: float = field(default_factory=time.time)
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d.pop("extra", None)
        d.update(self.extra)
        return d


_CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS inference_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    model TEXT NOT NULL,
    prompt_tokens INTEGER,
    completion_tokens INTEGER,
    total_tokens INTEGER,
    prompt_eval_duration_ms REAL,
    eval_duration_ms REAL,
    total_duration_ms REAL,
    tokens_per_second REAL,
    time_to_first_token_ms REAL,
    wall_clock_ms REAL,
    cpu_percent REAL,
    ram_used_mb REAL,
    gpu_mem_used_mb REAL,
    timestamp REAL
)
"""


def _gpu_mem_mb() -> Optional[float]:
    """Best-effort GPU memory query via nvidia-smi."""
    try:
        out = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=memory.used",
             "--format=csv,noheader,nounits"],
            timeout=3,
        )
        return float(out.decode().strip().split("\n")[0])
    except Exception:
        return None


class TelemetryStore:
    """Thin SQLite wrapper for metrics persistence."""

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            db_path = os.path.join(
                os.path.expanduser("~"), ".otk", "telemetry.db",
            )
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._db_path = db_path
        self._conn: Optional[sqlite3.Connection] = None
        self._ensure_table()

    def _get_conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(self._db_path)
            self._conn.row_factory = sqlite3.Row
        return self._conn

    def _ensure_table(self) -> None:
        self._get_conn().executescript(_CREATE_TABLE_SQL)

    def insert(self, m: InferenceMetrics) -> None:
        conn = self._get_conn()
        conn.execute(
            """INSERT INTO inference_metrics
               (model, prompt_tokens, completion_tokens, total_tokens,
                prompt_eval_duration_ms, eval_duration_ms, total_duration_ms,
                tokens_per_second, time_to_first_token_ms, wall_clock_ms,
                cpu_percent, ram_used_mb, gpu_mem_used_mb, timestamp)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                m.model, m.prompt_tokens, m.completion_tokens, m.total_tokens,
                m.prompt_eval_duration_ms, m.eval_duration_ms,
                m.total_duration_ms, m.tokens_per_second,
                m.time_to_first_token_ms, m.wall_clock_ms,
                m.cpu_percent, m.ram_used_mb, m.gpu_mem_used_mb,
                m.timestamp,
            ),
        )
        conn.commit()

    def query(
        self,
        model: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        conn = self._get_conn()
        sql = "SELECT * FROM inference_metrics"
        params: list = []
        if model:
            sql += " WHERE model = ?"
            params.append(model)
        sql += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        rows = conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]

    def summary(self, model: Optional[str] = None) -> Dict[str, Any]:
        conn = self._get_conn()
        where = "WHERE model = ?" if model else ""
        params = [model] if model else []
        row = conn.execute(
            f"""SELECT
                    COUNT(*) as total_calls,
                    AVG(tokens_per_second) as avg_tps,
                    AVG(time_to_first_token_ms) as avg_ttft_ms,
                    AVG(wall_clock_ms) as avg_wall_ms,
                    AVG(cpu_percent) as avg_cpu,
                    AVG(ram_used_mb) as avg_ram_mb
                FROM inference_metrics {where}""",
            params,
        ).fetchone()
        return dict(row) if row else {}

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None


class InferenceProfiler:
    """
    Profile Ollama inference calls.

    Can be used as a context manager or by calling ``record`` directly
    with the raw Ollama response dict.

    Example:
        >>> profiler = InferenceProfiler()
        >>> resp = client.generate_with_metadata("llama2", "Hi")
        >>> metrics = profiler.record("llama2", resp, wall_clock_ms=320.5)
        >>> profiler.store.summary("llama2")
    """

    def __init__(self, store: Optional[TelemetryStore] = None):
        self.store = store or TelemetryStore()

    def record(
        self,
        model: str,
        ollama_response: Dict[str, Any],
        wall_clock_ms: Optional[float] = None,
    ) -> InferenceMetrics:
        """Extract metrics from an Ollama response dict and persist them."""
        prompt_tokens = ollama_response.get("prompt_eval_count", 0) or 0
        completion_tokens = ollama_response.get("eval_count", 0) or 0

        prompt_eval_ns = ollama_response.get("prompt_eval_duration", 0) or 0
        eval_ns = ollama_response.get("eval_duration", 0) or 0
        total_ns = ollama_response.get("total_duration", 0) or 0

        prompt_eval_ms = prompt_eval_ns / 1e6
        eval_ms = eval_ns / 1e6
        total_ms = total_ns / 1e6

        tps = (completion_tokens / (eval_ms / 1000.0)) if eval_ms > 0 else 0.0

        cpu = psutil.cpu_percent(interval=None) if _HAS_PSUTIL else 0.0
        ram = (psutil.virtual_memory().used / (1024 ** 2)) if _HAS_PSUTIL else 0.0

        m = InferenceMetrics(
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            prompt_eval_duration_ms=prompt_eval_ms,
            eval_duration_ms=eval_ms,
            total_duration_ms=total_ms,
            tokens_per_second=tps,
            time_to_first_token_ms=prompt_eval_ms,
            wall_clock_ms=wall_clock_ms or total_ms,
            cpu_percent=cpu,
            ram_used_mb=ram,
            gpu_mem_used_mb=_gpu_mem_mb(),
        )
        self.store.insert(m)
        return m

    @contextmanager
    def profile(self, model: str):
        """Context manager that yields a dict; populate it with the Ollama response."""
        ctx: Dict[str, Any] = {}
        t0 = time.perf_counter()
        try:
            yield ctx
        finally:
            wall_ms = (time.perf_counter() - t0) * 1000.0
            if "response" in ctx:
                self.record(model, ctx["response"], wall_clock_ms=wall_ms)
