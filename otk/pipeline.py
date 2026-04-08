"""
DAG-based pipeline composition engine for multi-step LLM workflows.

Define multi-model workflows as directed acyclic graphs with LLM nodes,
transform nodes, conditional branches, parallel execution, and
map-reduce patterns.  Pipelines are serializable for reproducibility.
"""

import json
import time
import logging
from abc import ABC, abstractmethod
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field, asdict
from typing import Any, Callable, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


# ======================================================================
# Node results
# ======================================================================

@dataclass
class NodeResult:
    node_id: str
    output: Any = None
    error: Optional[str] = None
    latency_ms: float = 0.0
    model: Optional[str] = None
    retries: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PipelineResult:
    name: str
    outputs: Dict[str, Any] = field(default_factory=dict)
    node_results: Dict[str, NodeResult] = field(default_factory=dict)
    total_latency_ms: float = 0.0
    success: bool = True
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "outputs": {k: str(v)[:500] for k, v in self.outputs.items()},
            "total_latency_ms": self.total_latency_ms,
            "success": self.success,
            "error": self.error,
            "node_count": len(self.node_results),
        }


# ======================================================================
# Pipeline context (shared state across nodes)
# ======================================================================

class PipelineContext:
    """Mutable shared state for a pipeline execution run."""

    def __init__(self, initial_input: Any = None):
        self._store: Dict[str, Any] = {}
        if initial_input is not None:
            self._store["input"] = initial_input

    def set(self, key: str, value: Any) -> None:
        self._store[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        return self._store.get(key, default)

    def __getitem__(self, key: str) -> Any:
        return self._store[key]

    def __contains__(self, key: str) -> bool:
        return key in self._store

    def snapshot(self) -> Dict[str, Any]:
        return dict(self._store)


# ======================================================================
# Node base class + built-in types
# ======================================================================

class PipelineNode(ABC):
    """Base class for all pipeline nodes."""

    def __init__(
        self,
        node_id: str,
        max_retries: int = 1,
        timeout_s: Optional[float] = None,
    ):
        self.node_id = node_id
        self.max_retries = max_retries
        self.timeout_s = timeout_s

    @abstractmethod
    def execute(self, ctx: PipelineContext) -> Any:
        ...

    def run(self, ctx: PipelineContext) -> NodeResult:
        t0 = time.perf_counter()
        last_err: Optional[str] = None
        retries = 0
        for attempt in range(self.max_retries):
            try:
                output = self.execute(ctx)
                elapsed = (time.perf_counter() - t0) * 1000
                ctx.set(f"{self.node_id}.output", output)
                return NodeResult(
                    node_id=self.node_id, output=output,
                    latency_ms=elapsed, retries=retries,
                )
            except Exception as exc:
                last_err = str(exc)
                retries += 1
                logger.warning(
                    "Node %s attempt %d failed: %s",
                    self.node_id, attempt + 1, exc,
                )

        elapsed = (time.perf_counter() - t0) * 1000
        return NodeResult(
            node_id=self.node_id, error=last_err,
            latency_ms=elapsed, retries=retries,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.__class__.__name__,
            "node_id": self.node_id,
            "max_retries": self.max_retries,
            "timeout_s": self.timeout_s,
        }


class LLMNode(PipelineNode):
    """
    Node that calls an LLM to generate text.

    The ``prompt_template`` may reference context variables with
    ``{key}`` syntax, e.g. ``{input}`` or ``{extract.output}``.
    """

    def __init__(
        self,
        node_id: str,
        model: str,
        prompt_template: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        max_retries: int = 2,
        timeout_s: Optional[float] = None,
    ):
        super().__init__(node_id, max_retries, timeout_s)
        self.model = model
        self.prompt_template = prompt_template
        self.system = system
        self.temperature = temperature
        self.max_tokens = max_tokens

    def execute(self, ctx: PipelineContext) -> str:
        from .client import OllamaClient
        client = ctx.get("_client") or OllamaClient()
        prompt = self._render(ctx)
        return client.generate(
            self.model, prompt,
            system=self.system,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )

    def _render(self, ctx: PipelineContext) -> str:
        result = self.prompt_template
        snap = ctx.snapshot()
        for key, val in snap.items():
            placeholder = "{" + key + "}"
            if placeholder in result:
                result = result.replace(placeholder, str(val))
        return result

    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d.update({
            "model": self.model,
            "prompt_template": self.prompt_template,
            "system": self.system,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        })
        return d


class TransformNode(PipelineNode):
    """
    Node that applies a pure-Python transform function.

    The callable receives the ``PipelineContext`` and returns any value.
    """

    def __init__(
        self,
        node_id: str,
        func: Callable[[PipelineContext], Any],
        max_retries: int = 1,
    ):
        super().__init__(node_id, max_retries)
        self.func = func

    def execute(self, ctx: PipelineContext) -> Any:
        return self.func(ctx)


class ConditionalNode(PipelineNode):
    """
    Branching node: evaluates a predicate and writes a boolean result.

    Downstream edges should check ``{node_id.output}`` to decide
    whether to proceed.
    """

    def __init__(
        self,
        node_id: str,
        predicate: Callable[[PipelineContext], bool],
    ):
        super().__init__(node_id, max_retries=1)
        self.predicate = predicate

    def execute(self, ctx: PipelineContext) -> bool:
        return self.predicate(ctx)


class ReduceNode(PipelineNode):
    """
    Merge / reduce outputs from multiple upstream nodes.

    ``source_keys`` lists the context keys to aggregate; ``reducer``
    receives them as a list and returns the reduced value.
    """

    def __init__(
        self,
        node_id: str,
        source_keys: List[str],
        reducer: Callable[[List[Any]], Any],
    ):
        super().__init__(node_id, max_retries=1)
        self.source_keys = source_keys
        self.reducer = reducer

    def execute(self, ctx: PipelineContext) -> Any:
        values = [ctx.get(k) for k in self.source_keys]
        return self.reducer(values)


# ======================================================================
# Pipeline (DAG container + executor)
# ======================================================================

class Pipeline:
    """
    Directed acyclic graph of ``PipelineNode`` objects with
    topological-order execution.

    Example:
        >>> p = Pipeline("example")
        >>> p.add_node(LLMNode("step1", model="mistral", prompt_template="Summarise: {input}"))
        >>> p.add_node(TransformNode("step2", func=lambda ctx: ctx["step1.output"].upper()))
        >>> p.add_edge("step1", "step2")
        >>> result = p.execute(input="Hello world")
    """

    def __init__(self, name: str):
        self.name = name
        self._nodes: Dict[str, PipelineNode] = {}
        self._edges: Dict[str, Set[str]] = defaultdict(set)  # parent -> children
        self._reverse: Dict[str, Set[str]] = defaultdict(set)  # child -> parents

    def add_node(self, node: PipelineNode) -> "Pipeline":
        self._nodes[node.node_id] = node
        return self

    def add_edge(self, from_id: str, to_id: str) -> "Pipeline":
        self._edges[from_id].add(to_id)
        self._reverse[to_id].add(from_id)
        return self

    def _topo_sort(self) -> List[str]:
        """Kahn's algorithm for topological ordering."""
        in_degree: Dict[str, int] = {nid: 0 for nid in self._nodes}
        for parent, children in self._edges.items():
            for child in children:
                in_degree[child] = in_degree.get(child, 0) + 1

        queue = deque(nid for nid, deg in in_degree.items() if deg == 0)
        order: List[str] = []
        while queue:
            nid = queue.popleft()
            order.append(nid)
            for child in self._edges.get(nid, set()):
                in_degree[child] -= 1
                if in_degree[child] == 0:
                    queue.append(child)

        if len(order) != len(self._nodes):
            raise ValueError(
                "Pipeline contains a cycle — cannot topologically sort"
            )
        return order

    def _find_parallel_groups(self, order: List[str]) -> List[List[str]]:
        """Group nodes that can run concurrently (same topological level)."""
        levels: Dict[str, int] = {}
        for nid in order:
            parent_levels = [levels[p] for p in self._reverse.get(nid, set()) if p in levels]
            levels[nid] = (max(parent_levels) + 1) if parent_levels else 0

        groups: Dict[int, List[str]] = defaultdict(list)
        for nid in order:
            groups[levels[nid]].append(nid)
        return [groups[lv] for lv in sorted(groups)]

    def execute(self, _parallel: bool = True, **kwargs: Any) -> PipelineResult:
        """
        Run the pipeline.

        Keyword arguments are placed in the context (e.g. ``input="..."``)
        and are accessible inside prompt templates as ``{input}``.
        """
        from .client import OllamaClient

        ctx = PipelineContext()
        for k, v in kwargs.items():
            ctx.set(k, v)
        ctx.set("_client", OllamaClient())

        order = self._topo_sort()
        groups = self._find_parallel_groups(order)
        result = PipelineResult(name=self.name)
        t0 = time.perf_counter()

        try:
            for group in groups:
                if _parallel and len(group) > 1:
                    self._run_group_parallel(group, ctx, result)
                else:
                    for nid in group:
                        self._run_node(nid, ctx, result)
        except PipelineAbort as exc:
            result.success = False
            result.error = str(exc)

        result.total_latency_ms = (time.perf_counter() - t0) * 1000
        result.outputs = {
            nid: nr.output
            for nid, nr in result.node_results.items()
            if nr.error is None
        }
        return result

    def _run_node(
        self, nid: str, ctx: PipelineContext, result: PipelineResult,
    ) -> None:
        node = self._nodes[nid]
        nr = node.run(ctx)
        nr.model = getattr(node, "model", None)
        result.node_results[nid] = nr
        if nr.error:
            raise PipelineAbort(f"Node '{nid}' failed: {nr.error}")

    def _run_group_parallel(
        self, group: List[str], ctx: PipelineContext, result: PipelineResult,
    ) -> None:
        with ThreadPoolExecutor(max_workers=len(group)) as pool:
            futures = {
                pool.submit(self._nodes[nid].run, ctx): nid
                for nid in group
            }
            for future in as_completed(futures):
                nid = futures[future]
                nr = future.result()
                nr.model = getattr(self._nodes[nid], "model", None)
                result.node_results[nid] = nr
                if nr.error:
                    raise PipelineAbort(f"Node '{nid}' failed: {nr.error}")

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "nodes": {nid: n.to_dict() for nid, n in self._nodes.items()},
            "edges": {k: list(v) for k, v in self._edges.items()},
        }

    def to_json(self, path: Optional[str] = None) -> str:
        data = json.dumps(self.to_dict(), indent=2, default=str)
        if path:
            with open(path, "w") as f:
                f.write(data)
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Pipeline":
        """
        Reconstruct a pipeline from a serialised dict.

        Only ``LLMNode`` instances are restored; ``TransformNode`` and
        callable-based nodes cannot be serialised and are skipped with
        a warning.
        """
        p = cls(data["name"])
        for nid, nd in data.get("nodes", {}).items():
            ntype = nd.get("type", "")
            if ntype == "LLMNode":
                node = LLMNode(
                    node_id=nid,
                    model=nd["model"],
                    prompt_template=nd["prompt_template"],
                    system=nd.get("system"),
                    temperature=nd.get("temperature", 0.7),
                    max_tokens=nd.get("max_tokens"),
                    max_retries=nd.get("max_retries", 2),
                    timeout_s=nd.get("timeout_s"),
                )
                p.add_node(node)
            else:
                logger.warning(
                    "Cannot deserialise node '%s' of type '%s' "
                    "(callable-based nodes are not serialisable)",
                    nid, ntype,
                )
        for src, targets in data.get("edges", {}).items():
            for tgt in targets:
                if src in p._nodes and tgt in p._nodes:
                    p.add_edge(src, tgt)
        return p


class PipelineAbort(Exception):
    """Raised to halt pipeline execution on a node failure."""


# ======================================================================
# Fluent builder
# ======================================================================

class PipelineBuilder:
    """
    Fluent API for constructing pipelines.

    Example:
        >>> pipeline = (PipelineBuilder("demo")
        ...     .add_node(LLMNode("s1", model="mistral",
        ...                       prompt_template="Summarise: {input}"))
        ...     .add_node(LLMNode("s2", model="llama3",
        ...                       prompt_template="Critique: {s1.output}"))
        ...     .add_edge("s1", "s2")
        ...     .build())
        >>> result = pipeline.execute(input="...")
    """

    def __init__(self, name: str):
        self._pipeline = Pipeline(name)

    def add_node(self, node: PipelineNode) -> "PipelineBuilder":
        self._pipeline.add_node(node)
        return self

    def add_edge(self, from_id: str, to_id: str) -> "PipelineBuilder":
        self._pipeline.add_edge(from_id, to_id)
        return self

    def chain(self, *node_ids: str) -> "PipelineBuilder":
        """Add linear edges: a -> b -> c -> ..."""
        for i in range(len(node_ids) - 1):
            self.add_edge(node_ids[i], node_ids[i + 1])
        return self

    def build(self) -> Pipeline:
        self._pipeline._topo_sort()  # validate acyclicity
        return self._pipeline
