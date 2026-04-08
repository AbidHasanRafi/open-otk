"""Tests for the Task-Aware Model Router."""

import pytest
from otk.router import (
    TaskClassifier,
    TaskType,
    CapabilityMatrix,
    PerformanceHistory,
    ModelRouter,
    RoutingDecision,
)
from tests.mock_ollama import MockOllamaClient


class TestTaskClassifier:
    def test_code_classification(self):
        c = TaskClassifier()
        assert c.classify("Write a Python function to sort a list") == TaskType.CODE

    def test_creative_classification(self):
        c = TaskClassifier()
        assert c.classify("Write a short story about a dragon") == TaskType.CREATIVE_WRITING

    def test_factual_qa(self):
        c = TaskClassifier()
        assert c.classify("What is the capital of France?") == TaskType.FACTUAL_QA

    def test_summarization(self):
        c = TaskClassifier()
        assert c.classify("Summarize the following article") == TaskType.SUMMARIZATION

    def test_translation(self):
        c = TaskClassifier()
        assert c.classify("Translate this to Spanish") == TaskType.TRANSLATION

    def test_math(self):
        c = TaskClassifier()
        assert c.classify("Calculate the integral of x^2") == TaskType.MATH

    def test_general_fallback(self):
        c = TaskClassifier()
        assert c.classify("xyzzy foobar baz") == TaskType.GENERAL

    def test_confidence(self):
        c = TaskClassifier()
        task, conf = c.classify_with_confidence("Write Python code to implement a class")
        assert task == TaskType.CODE
        assert conf > 0


class TestCapabilityMatrix:
    def test_known_model(self):
        m = CapabilityMatrix()
        assert m.score("codellama:7b", TaskType.CODE) > 0.8

    def test_unknown_model_returns_default(self):
        m = CapabilityMatrix()
        assert m.score("unknown-model-xyz", TaskType.CODE) == 0.5

    def test_register_custom(self):
        m = CapabilityMatrix()
        m.register("my-model", {"code": 0.99, "general": 0.8})
        assert m.score("my-model:latest", TaskType.CODE) == 0.99


class TestPerformanceHistory:
    def test_record_and_query(self, tmp_db):
        h = PerformanceHistory(db_path=tmp_db)
        h.record("m1", "code", 100.0, quality_score=4.0)
        h.record("m1", "code", 200.0, quality_score=5.0)
        assert h.avg_latency("m1", "code") == pytest.approx(150.0)
        assert h.avg_quality("m1", "code") == pytest.approx(4.5)
        assert h.call_count("m1", "code") == 2

    def test_no_records(self, tmp_db):
        h = PerformanceHistory(db_path=tmp_db)
        assert h.avg_latency("m1", "code") is None
        assert h.avg_quality("m1", "code") is None
        assert h.call_count("m1", "code") == 0


class TestModelRouter:
    def test_route_returns_decision(self, tmp_db):
        client = MockOllamaClient()
        history = PerformanceHistory(db_path=tmp_db)
        router = ModelRouter(client=client, history=history, epsilon=0.0)
        decision = router.route("Write a Python function")
        assert isinstance(decision, RoutingDecision)
        assert decision.task_type == TaskType.CODE
        assert decision.selected_model != ""

    def test_epsilon_zero_is_deterministic(self, tmp_db):
        client = MockOllamaClient()
        history = PerformanceHistory(db_path=tmp_db)
        router = ModelRouter(client=client, history=history, epsilon=0.0)
        d1 = router.route("What is Python?")
        d2 = router.route("What is Python?")
        assert d1.selected_model == d2.selected_model

    def test_generate_records_history(self, tmp_db):
        client = MockOllamaClient()
        history = PerformanceHistory(db_path=tmp_db)
        router = ModelRouter(client=client, history=history, epsilon=0.0)
        resp = router.generate("Explain gravity")
        assert isinstance(resp, str)
        assert history.call_count(router.route("Explain gravity").selected_model, "factual_qa") >= 1

    def test_generate_with_fallback(self, tmp_db):
        client = MockOllamaClient()
        history = PerformanceHistory(db_path=tmp_db)
        router = ModelRouter(client=client, history=history, epsilon=0.0)
        resp, decision = router.generate_with_fallback("What is 2+2?")
        assert isinstance(resp, str)
        assert decision.reason == "fallback chain"
