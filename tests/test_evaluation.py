"""Tests for the LLM-as-Judge evaluation framework."""

import pytest
from unittest.mock import MagicMock
from otk.evaluation import (
    LLMJudge,
    JudgeConfig,
    EvaluationSuite,
    StatisticalAnalysis,
    EvaluationReport,
    EvaluationDimension,
)
from tests.mock_ollama import MockOllamaClient


class TestStatisticalAnalysis:
    def test_paired_t_test_equal(self):
        a = [3.0, 3.0, 3.0, 3.0]
        b = [3.0, 3.0, 3.0, 3.0]
        t, p = StatisticalAnalysis.paired_t_test(a, b)
        assert t == pytest.approx(0.0)

    def test_paired_t_test_different(self):
        a = [5.0, 5.0, 5.0, 5.0, 5.0]
        b = [1.0, 1.0, 1.0, 1.0, 1.0]
        t, p = StatisticalAnalysis.paired_t_test(a, b)
        assert t > 0
        assert p < 0.05

    def test_bootstrap_ci(self):
        a = [5.0] * 20
        b = [3.0] * 20
        lo, hi = StatisticalAnalysis.bootstrap_ci(a, b)
        assert lo > 0
        assert hi > 0

    def test_cohens_d(self):
        a = [5.0, 4.5, 5.5, 5.0]
        b = [1.0, 1.5, 0.5, 1.0]
        d = StatisticalAnalysis.cohens_d(a, b)
        assert d > 1.0  # large effect

    def test_full_comparison(self):
        a = [4.0, 5.0, 3.0, 4.0, 5.0]
        b = [2.0, 3.0, 1.0, 2.0, 3.0]
        result = StatisticalAnalysis.full_comparison(a, b)
        assert result.mean_diff > 0
        assert result.n == 5
        assert result.cohens_d > 0


class TestLLMJudge:
    def _make_judge(self, score_text="4"):
        """Create a judge with a mock client returning a fixed score."""
        config = JudgeConfig(model="judge-model", dimensions=["coherence", "relevance"])
        client = MagicMock()
        client.generate = MagicMock(return_value=score_text)
        return LLMJudge(config, client=client)

    def test_score_single_dimension(self):
        judge = self._make_judge("4")
        s = judge.score("What is 2+2?", "4", "coherence")
        assert s.dimension == "coherence"
        assert s.score == 4.0

    def test_evaluate_all_dimensions(self):
        judge = self._make_judge("5")
        scores = judge.evaluate("prompt", "response")
        assert len(scores) == 2
        assert all(s.score == 5.0 for s in scores)

    def test_invalid_score_defaults_to_3(self):
        judge = self._make_judge("no number here")
        s = judge.score("p", "r", "coherence")
        assert s.score == 3.0


class TestEvaluationSuite:
    def test_run_single(self):
        client = MagicMock()
        client.generate = MagicMock(return_value="3")
        config = JudgeConfig(model="judge", dimensions=["coherence"])
        suite = EvaluationSuite(
            judge_config=config,
            dataset=[{"prompt": "Hi", "response": "Hello"}],
            client=client,
        )
        report = suite.run_single()
        assert len(report.items) == 1
        assert report.items[0].scores[0].dimension == "coherence"

    def test_run_comparative(self):
        client = MagicMock()
        # Return alternating scores: 5 for A, 2 for B
        call_count = {"n": 0}

        def side_effect(*args, **kwargs):
            call_count["n"] += 1
            return "5" if call_count["n"] % 2 == 1 else "2"

        client.generate = MagicMock(side_effect=side_effect)
        config = JudgeConfig(model="judge", dimensions=["coherence"])
        suite = EvaluationSuite(
            judge_config=config,
            dataset=[
                {"prompt": "Q1", "response_a": "A1", "response_b": "B1"},
                {"prompt": "Q2", "response_a": "A2", "response_b": "B2"},
            ],
            client=client,
        )
        report = suite.run_comparative(model_a_name="ModelA", model_b_name="ModelB")
        assert len(report.items) == 2
        assert "coherence" in report.stats


class TestEvaluationReport:
    def test_export_json(self, tmp_path):
        report = EvaluationReport(
            dimensions=["coherence"],
            wins_a=3, wins_b=1, ties=1,
            model_a="A", model_b="B",
        )
        path = str(tmp_path / "report.json")
        report.export_json(path)
        import json
        with open(path) as f:
            data = json.load(f)
        assert data["wins_a"] == 3

    def test_export_html(self, tmp_path):
        from otk.evaluation import StatResult
        report = EvaluationReport(
            dimensions=["coherence"],
            stats={"coherence": StatResult(
                mean_diff=1.5, t_statistic=3.2, p_value=0.01,
                ci_lower=0.8, ci_upper=2.2, cohens_d=1.1, n=10,
            )},
        )
        path = str(tmp_path / "report.html")
        report.export_html(path)
        with open(path) as f:
            html = f.read()
        assert "OTK Evaluation Report" in html
        assert "coherence" in html
