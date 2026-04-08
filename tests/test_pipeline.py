"""Tests for the Pipeline Composition Engine."""

import json
import pytest
from otk.pipeline import (
    Pipeline,
    PipelineBuilder,
    PipelineNode,
    LLMNode,
    TransformNode,
    ConditionalNode,
    ReduceNode,
    PipelineContext,
    PipelineResult,
    PipelineAbort,
)
from tests.mock_ollama import MockOllamaClient


class TestPipelineContext:
    def test_set_and_get(self):
        ctx = PipelineContext()
        ctx.set("key", "value")
        assert ctx.get("key") == "value"
        assert ctx["key"] == "value"

    def test_initial_input(self):
        ctx = PipelineContext(initial_input="hello")
        assert ctx["input"] == "hello"

    def test_contains(self):
        ctx = PipelineContext()
        ctx.set("x", 1)
        assert "x" in ctx
        assert "y" not in ctx

    def test_snapshot(self):
        ctx = PipelineContext()
        ctx.set("a", 1)
        ctx.set("b", 2)
        snap = ctx.snapshot()
        assert snap == {"a": 1, "b": 2}


class TestTransformNode:
    def test_basic_transform(self):
        node = TransformNode("upper", func=lambda ctx: ctx["input"].upper())
        ctx = PipelineContext(initial_input="hello")
        result = node.run(ctx)
        assert result.output == "HELLO"
        assert result.error is None

    def test_transform_error(self):
        def failing(ctx):
            raise ValueError("broken")
        node = TransformNode("fail", func=failing, max_retries=1)
        ctx = PipelineContext()
        result = node.run(ctx)
        assert result.error is not None
        assert "broken" in result.error


class TestPipeline:
    def test_simple_linear_pipeline(self):
        p = Pipeline("test")
        p.add_node(TransformNode("a", func=lambda ctx: ctx["input"] + " processed"))
        p.add_node(TransformNode("b", func=lambda ctx: ctx["a.output"].upper()))
        p.add_edge("a", "b")

        result = p.execute(input="hello")
        assert result.success
        assert result.outputs["a"] == "hello processed"
        assert result.outputs["b"] == "HELLO PROCESSED"

    def test_parallel_branches(self):
        p = Pipeline("parallel")
        p.add_node(TransformNode("src", func=lambda ctx: ctx["input"]))
        p.add_node(TransformNode("branch_a", func=lambda ctx: ctx["src.output"] + "_a"))
        p.add_node(TransformNode("branch_b", func=lambda ctx: ctx["src.output"] + "_b"))
        p.add_edge("src", "branch_a")
        p.add_edge("src", "branch_b")

        result = p.execute(input="data")
        assert result.success
        assert "branch_a" in result.outputs
        assert "branch_b" in result.outputs

    def test_cycle_detection(self):
        p = Pipeline("cycle")
        p.add_node(TransformNode("a", func=lambda ctx: None))
        p.add_node(TransformNode("b", func=lambda ctx: None))
        p.add_edge("a", "b")
        p.add_edge("b", "a")
        with pytest.raises(ValueError, match="cycle"):
            p.execute()

    def test_reduce_node(self):
        p = Pipeline("reduce")
        p.add_node(TransformNode("a", func=lambda ctx: 10))
        p.add_node(TransformNode("b", func=lambda ctx: 20))
        p.add_node(ReduceNode("sum", source_keys=["a.output", "b.output"],
                               reducer=lambda vals: sum(v for v in vals if v)))
        p.add_edge("a", "sum")
        p.add_edge("b", "sum")
        result = p.execute()
        assert result.outputs["sum"] == 30

    def test_conditional_node(self):
        p = Pipeline("cond")
        p.add_node(TransformNode("data", func=lambda ctx: 42))
        p.add_node(ConditionalNode("check", predicate=lambda ctx: ctx.get("data.output", 0) > 10))
        p.add_edge("data", "check")
        result = p.execute()
        assert result.outputs["check"] is True

    def test_node_failure_aborts_pipeline(self):
        def fail(ctx):
            raise RuntimeError("boom")
        p = Pipeline("fail")
        p.add_node(TransformNode("a", func=fail, max_retries=1))
        result = p.execute()
        assert not result.success
        assert "boom" in result.error


class TestPipelineBuilder:
    def test_builder_chain(self):
        pipeline = (
            PipelineBuilder("chain")
            .add_node(TransformNode("a", func=lambda ctx: 1))
            .add_node(TransformNode("b", func=lambda ctx: ctx["a.output"] + 1))
            .add_node(TransformNode("c", func=lambda ctx: ctx["b.output"] + 1))
            .chain("a", "b", "c")
            .build()
        )
        result = pipeline.execute()
        assert result.outputs["c"] == 3

    def test_build_validates_dag(self):
        builder = (
            PipelineBuilder("bad")
            .add_node(TransformNode("x", func=lambda ctx: None))
            .add_node(TransformNode("y", func=lambda ctx: None))
            .add_edge("x", "y")
            .add_edge("y", "x")
        )
        with pytest.raises(ValueError):
            builder.build()


class TestPipelineSerialization:
    def test_to_dict_and_from_dict(self):
        p = Pipeline("ser")
        p.add_node(LLMNode("s1", model="mistral", prompt_template="Q: {input}"))
        p.add_node(LLMNode("s2", model="llama3", prompt_template="A: {s1.output}"))
        p.add_edge("s1", "s2")

        data = p.to_dict()
        assert data["name"] == "ser"
        assert "s1" in data["nodes"]
        assert "s2" in data["edges"]["s1"]

        p2 = Pipeline.from_dict(data)
        assert "s1" in p2._nodes
        assert "s2" in p2._nodes

    def test_to_json(self, tmp_path):
        p = Pipeline("json")
        p.add_node(LLMNode("n1", model="m", prompt_template="{input}"))
        path = str(tmp_path / "pipeline.json")
        json_str = p.to_json(path)
        data = json.loads(json_str)
        assert data["name"] == "json"
        with open(path) as f:
            assert json.load(f) == data
