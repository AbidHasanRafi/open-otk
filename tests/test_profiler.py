"""Tests for the InferenceProfiler and TelemetryStore."""

import pytest
from otk.profiler import InferenceProfiler, TelemetryStore, InferenceMetrics


class TestTelemetryStore:
    def test_insert_and_query(self, tmp_db):
        store = TelemetryStore(db_path=tmp_db)
        m = InferenceMetrics(
            model="test-model",
            prompt_tokens=10,
            completion_tokens=20,
            total_tokens=30,
            tokens_per_second=15.0,
            wall_clock_ms=200.0,
        )
        store.insert(m)
        rows = store.query(model="test-model", limit=10)
        assert len(rows) == 1
        assert rows[0]["model"] == "test-model"
        assert rows[0]["total_tokens"] == 30

    def test_summary(self, tmp_db):
        store = TelemetryStore(db_path=tmp_db)
        for i in range(5):
            store.insert(InferenceMetrics(
                model="m", tokens_per_second=10.0 + i,
                wall_clock_ms=100.0 + i * 10,
            ))
        s = store.summary(model="m")
        assert s["total_calls"] == 5
        assert s["avg_tps"] == pytest.approx(12.0, abs=0.01)

    def test_query_no_model_filter(self, tmp_db):
        store = TelemetryStore(db_path=tmp_db)
        store.insert(InferenceMetrics(model="a"))
        store.insert(InferenceMetrics(model="b"))
        rows = store.query(limit=10)
        assert len(rows) == 2


class TestInferenceProfiler:
    def test_record_from_ollama_response(self, tmp_db):
        store = TelemetryStore(db_path=tmp_db)
        profiler = InferenceProfiler(store=store)
        resp = {
            "response": "Hello",
            "eval_count": 5,
            "eval_duration": 500_000_000,
            "prompt_eval_count": 3,
            "prompt_eval_duration": 200_000_000,
            "total_duration": 700_000_000,
        }
        m = profiler.record("test-model", resp, wall_clock_ms=700.0)
        assert m.model == "test-model"
        assert m.completion_tokens == 5
        assert m.prompt_tokens == 3
        assert m.tokens_per_second > 0
        rows = store.query(model="test-model")
        assert len(rows) == 1

    def test_profile_context_manager(self, tmp_db):
        store = TelemetryStore(db_path=tmp_db)
        profiler = InferenceProfiler(store=store)
        with profiler.profile("test-model") as ctx:
            ctx["response"] = {
                "eval_count": 10,
                "eval_duration": 1_000_000_000,
                "prompt_eval_count": 5,
                "prompt_eval_duration": 200_000_000,
                "total_duration": 1_200_000_000,
            }
        rows = store.query(model="test-model")
        assert len(rows) == 1
