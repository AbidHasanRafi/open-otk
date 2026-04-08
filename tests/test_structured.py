"""Tests for the StructuredGenerator."""

import json
import pytest
from unittest.mock import MagicMock
from otk.structured import (
    StructuredGenerator,
    StructuredOutputError,
    _extract_json,
    _coerce_value,
    _schema_to_instruction,
)


class TestHelpers:
    def test_extract_json_from_plain(self):
        text = '{"name": "Alice", "age": 30}'
        assert json.loads(_extract_json(text)) == {"name": "Alice", "age": 30}

    def test_extract_json_from_markdown(self):
        text = "Here is the result:\n```json\n{\"x\": 1}\n```"
        assert json.loads(_extract_json(text)) == {"x": 1}

    def test_extract_json_no_json_raises(self):
        with pytest.raises(ValueError, match="No JSON"):
            _extract_json("no json here")

    def test_coerce_int(self):
        assert _coerce_value("42", "int") == 42

    def test_coerce_bool(self):
        assert _coerce_value("true", "bool") is True
        assert _coerce_value("false", "bool") is False

    def test_coerce_float(self):
        assert _coerce_value("3.14", "float") == pytest.approx(3.14)

    def test_coerce_noop(self):
        assert _coerce_value(42, "int") == 42

    def test_schema_to_instruction(self):
        instr = _schema_to_instruction({"name": "str", "age": "int"})
        assert '"name"' in instr
        assert '"age"' in instr
        assert "JSON object" in instr


class TestStructuredGenerator:
    def _make_gen(self, responses):
        """Create a generator with a mock client that returns canned responses."""
        gen = StructuredGenerator(model="test", max_retries=2, temperature=0.1)
        mock = MagicMock()
        call_count = {"n": 0}

        def side_effect(*args, **kwargs):
            idx = min(call_count["n"], len(responses) - 1)
            call_count["n"] += 1
            return responses[idx]

        mock.generate = MagicMock(side_effect=side_effect)
        gen.client = mock
        return gen

    def test_simple_generation(self):
        gen = self._make_gen(['{"name": "Alice", "age": 30}'])
        result = gen.generate(
            prompt="Extract info",
            schema={"name": "str", "age": "int"},
        )
        assert result["name"] == "Alice"
        assert result["age"] == 30

    def test_type_coercion(self):
        gen = self._make_gen(['{"name": "Bob", "age": "25"}'])
        result = gen.generate(
            prompt="Extract",
            schema={"name": "str", "age": "int"},
        )
        assert result["age"] == 25

    def test_retry_on_invalid_json(self):
        gen = self._make_gen([
            "not json at all",
            '{"name": "Carol", "age": 28}',
        ])
        result = gen.generate(
            prompt="Extract",
            schema={"name": "str", "age": "int"},
        )
        assert result["name"] == "Carol"

    def test_failure_after_retries(self):
        gen = self._make_gen(["bad", "still bad", "nope"])
        with pytest.raises(StructuredOutputError):
            gen.generate(prompt="X", schema={"name": "str"})

    def test_missing_fields_triggers_retry(self):
        gen = self._make_gen([
            '{"name": "Dan"}',
            '{"name": "Dan", "age": 40}',
        ])
        result = gen.generate(
            prompt="Extract",
            schema={"name": "str", "age": "int"},
        )
        assert result["age"] == 40

    def test_generate_list(self):
        gen = self._make_gen(['[{"item": "a"}, {"item": "b"}]'])
        result = gen.generate_list(
            prompt="List items",
            item_schema={"item": "str"},
        )
        assert len(result) == 2
        assert result[0]["item"] == "a"
