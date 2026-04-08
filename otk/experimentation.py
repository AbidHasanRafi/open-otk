"""
Experimentation and benchmarking toolkit.

Extends the original speed-only comparisons with quality-based evaluation
via the LLM-as-Judge framework, a standard benchmark suite, and
SQLite-backed result persistence for longitudinal analysis.
"""

import time
import statistics
import sqlite3
import os
import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional, Callable

logger = logging.getLogger(__name__)


@dataclass
class ExperimentResult:
    """Result from a single experiment."""
    model: str
    prompt: str
    response: str
    time_taken: float
    tokens_estimated: int
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    quality_scores: Dict[str, float] = field(default_factory=dict)


@dataclass
class ComparisonResult:
    """Results from comparing multiple models."""
    models: List[str]
    prompt: str
    results: List[ExperimentResult]
    winner: Optional[str] = None
    rankings: Dict[str, float] = field(default_factory=dict)


# ======================================================================
# Result store
# ======================================================================

_EXPERIMENT_TABLE = """
CREATE TABLE IF NOT EXISTS experiment_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    model TEXT NOT NULL,
    prompt TEXT,
    response TEXT,
    time_taken REAL,
    tokens_estimated INTEGER,
    quality_json TEXT,
    error TEXT,
    timestamp REAL
)
"""


class ExperimentStore:
    """Persist experiment results to SQLite."""

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            db_path = os.path.join(
                os.path.expanduser("~"), ".otk", "experiments.db",
            )
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._conn = sqlite3.connect(db_path)
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(_EXPERIMENT_TABLE)

    def save(self, r: ExperimentResult) -> None:
        self._conn.execute(
            "INSERT INTO experiment_results "
            "(model,prompt,response,time_taken,tokens_estimated,quality_json,error,timestamp) "
            "VALUES (?,?,?,?,?,?,?,?)",
            (r.model, r.prompt, r.response, r.time_taken,
             r.tokens_estimated, json.dumps(r.quality_scores),
             r.error, time.time()),
        )
        self._conn.commit()

    def query(self, model: Optional[str] = None, limit: int = 50) -> List[Dict]:
        sql = "SELECT * FROM experiment_results"
        params: list = []
        if model:
            sql += " WHERE model=?"
            params.append(model)
        sql += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        return [dict(r) for r in self._conn.execute(sql, params).fetchall()]

    def close(self) -> None:
        self._conn.close()


# ======================================================================
# Model Experiment
# ======================================================================

class ModelExperiment:
    """
    Run experiments with one or more models.

    Optionally evaluates output quality using the LLM-as-Judge
    framework and persists results to SQLite.

    Example:
        >>> exp = ModelExperiment()
        >>> results = exp.compare_models(
        ...     models=["llama2", "mistral"],
        ...     prompt="What is Python?",
        ... )
        >>> exp.print_comparison(results)
    """

    def __init__(
        self,
        client: Optional[Any] = None,
        store: Optional[ExperimentStore] = None,
        evaluate_quality: bool = False,
        judge_model: Optional[str] = None,
    ):
        from .client import OllamaClient
        self.client = client or OllamaClient()
        self.store = store or ExperimentStore()
        self.evaluate_quality = evaluate_quality
        self.judge_model = judge_model

    def run_single(
        self, model: str, prompt: str, **kwargs,
    ) -> ExperimentResult:
        start_time = time.time()
        try:
            response = self.client.generate(model, prompt, **kwargs)
            time_taken = time.time() - start_time
            from .utils import estimate_tokens
            tokens = estimate_tokens(response)
            result = ExperimentResult(
                model=model, prompt=prompt, response=response,
                time_taken=time_taken, tokens_estimated=tokens,
                metadata={"success": True},
            )
            if self.evaluate_quality and self.judge_model:
                result.quality_scores = self._evaluate(prompt, response)
            self.store.save(result)
            return result
        except Exception as e:
            result = ExperimentResult(
                model=model, prompt=prompt, response="",
                time_taken=time.time() - start_time,
                tokens_estimated=0, error=str(e),
                metadata={"success": False},
            )
            self.store.save(result)
            return result

    def compare_models(
        self,
        models: List[str],
        prompt: str,
        parallel: bool = False,
        **kwargs,
    ) -> ComparisonResult:
        results: List[ExperimentResult] = []
        if parallel:
            with ThreadPoolExecutor(max_workers=len(models)) as executor:
                futures = {
                    executor.submit(self.run_single, m, prompt, **kwargs): m
                    for m in models
                }
                for future in as_completed(futures):
                    results.append(future.result())
        else:
            for model in models:
                results.append(self.run_single(model, prompt, **kwargs))

        rankings = {
            r.model: r.time_taken for r in results if not r.error
        }
        winner = min(rankings, key=rankings.get) if rankings else None
        return ComparisonResult(
            models=models, prompt=prompt, results=results,
            winner=winner, rankings=rankings,
        )

    def batch_test(
        self, model: str, prompts: List[str], **kwargs,
    ) -> List[ExperimentResult]:
        return [self.run_single(model, p, **kwargs) for p in prompts]

    def benchmark(
        self, model: str, prompt: str, iterations: int = 5, **kwargs,
    ) -> Dict[str, Any]:
        results = [
            r for r in (self.run_single(model, prompt, **kwargs) for _ in range(iterations))
            if not r.error
        ]
        if not results:
            return {"error": "All iterations failed"}
        times = [r.time_taken for r in results]
        tokens = [r.tokens_estimated for r in results]
        return {
            "model": model,
            "iterations": len(results),
            "avg_time": statistics.mean(times),
            "min_time": min(times),
            "max_time": max(times),
            "std_dev": statistics.stdev(times) if len(times) > 1 else 0,
            "avg_tokens": statistics.mean(tokens),
            "tokens_per_second": statistics.mean(
                [t / tm for t, tm in zip(tokens, times) if tm > 0]
            ),
        }

    def benchmark_suite(
        self,
        models: Optional[List[str]] = None,
        prompts: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Run a standard benchmark across all installed models (or a subset).

        Returns a summary dict suitable for report generation.
        """
        if prompts is None:
            prompts = [
                "What is the capital of France?",
                "Write a Python function that reverses a string.",
                "Summarize the theory of relativity in three sentences.",
                "Translate 'Hello, how are you?' to Spanish.",
                "Solve: What is 15% of 240?",
            ]
        if models is None:
            models = [
                m.get("name", m.get("model", ""))
                for m in self.client.list_models()
            ]
            models = [m for m in models if m]

        suite_results: Dict[str, List[ExperimentResult]] = {}
        for model in models:
            suite_results[model] = self.batch_test(model, prompts)

        summary: Dict[str, Any] = {}
        for model, res_list in suite_results.items():
            ok = [r for r in res_list if not r.error]
            if ok:
                summary[model] = {
                    "prompts_tested": len(prompts),
                    "success_rate": len(ok) / len(res_list),
                    "avg_time": statistics.mean([r.time_taken for r in ok]),
                    "avg_tokens": statistics.mean([r.tokens_estimated for r in ok]),
                    "quality": (
                        {dim: statistics.mean([r.quality_scores.get(dim, 0) for r in ok if r.quality_scores])
                         for dim in (ok[0].quality_scores or {})}
                        if any(r.quality_scores for r in ok) else {}
                    ),
                }
        return summary

    def _evaluate(self, prompt: str, response: str) -> Dict[str, float]:
        try:
            from .evaluation import LLMJudge, JudgeConfig
            judge = LLMJudge(
                JudgeConfig(model=self.judge_model, dimensions=["coherence", "relevance"]),
                client=self.client,
            )
            scores = judge.evaluate(prompt, response)
            return {s.dimension: s.score for s in scores}
        except Exception as exc:
            logger.warning("Quality evaluation failed: %s", exc)
            return {}

    def print_comparison(self, result: ComparisonResult) -> None:
        print("\n" + "=" * 70)
        print(f"Model Comparison: {result.prompt[:50]}...")
        print("=" * 70)
        for exp in result.results:
            print(f"\n  {exp.model}")
            print(f"  {'─' * 66}")
            if exp.error:
                print(f"  Error: {exp.error}")
            else:
                print(f"  Response: {exp.response[:200]}...")
                print(f"  Time: {exp.time_taken:.2f}s")
                print(f"  Tokens: ~{exp.tokens_estimated}")
                tps = exp.tokens_estimated / exp.time_taken if exp.time_taken > 0 else 0
                print(f"  Speed: ~{tps:.1f} tokens/s")
                if exp.quality_scores:
                    qs = ", ".join(f"{k}={v:.1f}" for k, v in exp.quality_scores.items())
                    print(f"  Quality: {qs}")
        if result.winner:
            print(f"\n  Fastest: {result.winner} ({result.rankings[result.winner]:.2f}s)")

    def print_benchmark(self, stats: Dict[str, Any]) -> None:
        print("\n" + "=" * 70)
        print(f"Benchmark Results: {stats.get('model', 'Unknown')}")
        print("=" * 70)
        if "error" in stats:
            print(f"  {stats['error']}")
            return
        print(f"  Iterations: {stats['iterations']}")
        print(f"  Average Time: {stats['avg_time']:.2f}s")
        print(f"  Min Time: {stats['min_time']:.2f}s")
        print(f"  Max Time: {stats['max_time']:.2f}s")
        print(f"  Std Dev: {stats['std_dev']:.2f}s")
        print(f"  Avg Tokens: {stats['avg_tokens']:.0f}")
        print(f"  Tokens/Second: {stats['tokens_per_second']:.1f}")


class ModelPlayground:
    """Interactive playground for experimenting with models."""

    def __init__(self, client: Optional[Any] = None):
        from .client import OllamaClient
        self.client = client or OllamaClient()
        self.experiment = ModelExperiment(client=self.client)

    def try_temperatures(
        self, model: str, prompt: str, temperatures: Optional[List[float]] = None,
    ) -> None:
        if temperatures is None:
            temperatures = [0.1, 0.5, 0.7, 0.9, 1.2]
        print(f"\n  Temperature Experiment: {model}")
        print(f"  Prompt: {prompt}")
        print("=" * 70)
        for temp in temperatures:
            print(f"\n  Temperature: {temp}")
            print("  " + "-" * 66)
            try:
                response = self.client.generate(model, prompt, temperature=temp)
                print(f"  {response[:300]}")
            except Exception as e:
                print(f"  Error: {e}")

    def try_prompt_variations(
        self, model: str, base_prompt: str, variations: List[str],
    ) -> None:
        print(f"\n  Prompt Variations Experiment: {model}")
        print("=" * 70)
        for i, variation in enumerate(variations, 1):
            full_prompt = f"{variation} {base_prompt}"
            print(f"\n  {i}. {full_prompt}")
            print("  " + "-" * 66)
            try:
                response = self.client.generate(model, full_prompt)
                print(f"  {response[:200]}")
            except Exception as e:
                print(f"  Error: {e}")

    def try_system_messages(
        self, model: str, prompt: str, system_messages: List[str],
    ) -> None:
        print(f"\n  System Message Experiment: {model}")
        print(f"  Prompt: {prompt}")
        print("=" * 70)
        for i, system in enumerate(system_messages, 1):
            print(f"\n  {i}. System: {system}")
            print("  " + "-" * 66)
            try:
                response = self.client.generate(model, prompt, system=system)
                print(f"  {response[:250]}")
            except Exception as e:
                print(f"  Error: {e}")

    def find_best_temperature(
        self,
        model: str,
        prompt: str,
        eval_func: Callable[[str], float],
        temperature_range: tuple = (0.1, 1.5),
        steps: int = 10,
    ) -> float:
        min_temp, max_temp = temperature_range
        step_size = (max_temp - min_temp) / steps
        best_temp = min_temp
        best_score = -float("inf")
        print(f"\n  Finding Best Temperature for: {model}")
        print("=" * 70)
        for i in range(steps + 1):
            temp = min_temp + (i * step_size)
            try:
                response = self.client.generate(model, prompt, temperature=temp)
                score = eval_func(response)
                print(f"  Temp {temp:.2f}: Score {score:.2f}")
                if score > best_score:
                    best_score = score
                    best_temp = temp
            except Exception as e:
                print(f"  Temp {temp:.2f}: Error - {e}")
        print(f"\n  Best Temperature: {best_temp:.2f} (Score: {best_score:.2f})")
        return best_temp


class ABTest:
    """A/B testing for model outputs."""

    def __init__(self, client: Optional[Any] = None):
        from .client import OllamaClient
        self.client = client or OllamaClient()

    def test(
        self,
        model_a: str,
        model_b: str,
        prompts: List[str],
        judge_func: Optional[Callable[[str, str], str]] = None,
    ) -> Dict[str, Any]:
        results: Dict[str, Any] = {
            "model_a": model_a, "model_b": model_b,
            "wins_a": 0, "wins_b": 0, "ties": 0, "details": [],
        }
        print(f"\n  A/B Test: {model_a} vs {model_b}")
        print("=" * 70)
        for i, prompt in enumerate(prompts, 1):
            print(f"\n  Test {i}/{len(prompts)}: {prompt[:50]}...")
            try:
                resp_a = self.client.generate(model_a, prompt)
                resp_b = self.client.generate(model_b, prompt)
                winner = judge_func(resp_a, resp_b) if judge_func else None
                if winner == "a":
                    results["wins_a"] += 1
                elif winner == "b":
                    results["wins_b"] += 1
                else:
                    results["ties"] += 1
                results["details"].append({
                    "prompt": prompt, "response_a": resp_a,
                    "response_b": resp_b, "winner": winner,
                })
            except Exception as e:
                print(f"  Error: {e}")
        print(f"\n{'=' * 70}")
        print("  A/B Test Results")
        print(f"  {model_a}: {results['wins_a']} wins")
        print(f"  {model_b}: {results['wins_b']} wins")
        print(f"  Ties: {results['ties']}")
        return results
