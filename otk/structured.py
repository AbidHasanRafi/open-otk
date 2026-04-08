"""
Structured output engine with JSON schema validation, auto-retry
with self-correction, type coercion, and optional Pydantic support.
"""

import json
import re
import logging
from typing import Any, Callable, Dict, List, Optional, Type, Union

logger = logging.getLogger(__name__)

try:
    from pydantic import BaseModel as PydanticBaseModel, ValidationError
    _HAS_PYDANTIC = True
except ImportError:
    PydanticBaseModel = None  # type: ignore[assignment,misc]
    ValidationError = None  # type: ignore[assignment,misc]
    _HAS_PYDANTIC = False


_TYPE_MAP = {
    "str": str, "string": str,
    "int": int, "integer": int,
    "float": float, "number": float,
    "bool": bool, "boolean": bool,
    "list": list, "array": list,
    "dict": dict, "object": dict,
}


def _coerce_value(value: Any, target_type: str) -> Any:
    """Best-effort coercion of *value* to *target_type*."""
    py_type = _TYPE_MAP.get(target_type.lower())
    if py_type is None or isinstance(value, py_type):
        return value
    if py_type is bool:
        if isinstance(value, str):
            return value.lower() in ("true", "1", "yes")
        return bool(value)
    try:
        return py_type(value)
    except (ValueError, TypeError):
        return value


def _schema_to_instruction(schema: Dict[str, Any]) -> str:
    """Convert a simple {field: type} schema into a prompt instruction."""
    lines = ["Respond with a JSON object using exactly these fields:"]
    for key, typ in schema.items():
        lines.append(f'  "{key}": <{typ}>')
    lines.append("Do NOT include any text outside the JSON object.")
    return "\n".join(lines)


def _extract_json(text: str) -> str:
    """Pull the first JSON object from *text*, tolerating markdown fences."""
    text = re.sub(r"```(?:json)?\s*", "", text)
    text = text.replace("```", "")
    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        return match.group(0)
    raise ValueError("No JSON object found in response")


class StructuredGenerator:
    """
    Generate structured (JSON) output from an LLM with schema validation,
    automatic retry with self-correction, and type coercion.

    Example:
        >>> gen = StructuredGenerator(model="mistral")
        >>> result = gen.generate(
        ...     prompt="Extract info: John Smith, age 30, engineer at Google",
        ...     schema={"name": "str", "age": "int", "company": "str"},
        ... )
        >>> result
        {'name': 'John Smith', 'age': 30, 'company': 'Google'}
    """

    def __init__(
        self,
        model: str,
        client: Optional[Any] = None,
        max_retries: int = 3,
        temperature: float = 0.3,
    ):
        from .client import OllamaClient
        self.model = model
        self.client: OllamaClient = client or OllamaClient()
        self.max_retries = max_retries
        self.temperature = temperature

    def generate(
        self,
        prompt: str,
        schema: Dict[str, str],
        system: Optional[str] = None,
        coerce_types: bool = True,
    ) -> Dict[str, Any]:
        """
        Generate a JSON object matching *schema*.

        Args:
            prompt: User prompt describing what to extract/generate.
            schema: Mapping of field names to type strings
                    (e.g. ``{"name": "str", "age": "int"}``).
            system: Optional system message.
            coerce_types: Whether to coerce values to declared types.

        Returns:
            Validated and optionally coerced dictionary.
        """
        instruction = _schema_to_instruction(schema)
        full_prompt = f"{instruction}\n\n{prompt}"

        last_error: Optional[str] = None
        for attempt in range(self.max_retries + 1):
            if attempt > 0 and last_error:
                full_prompt = (
                    f"{instruction}\n\n{prompt}\n\n"
                    f"Your previous output was invalid JSON. "
                    f"The error was: {last_error}\nPlease output ONLY valid JSON."
                )

            try:
                raw = self.client.generate(
                    self.model, full_prompt,
                    system=system, temperature=self.temperature,
                )
                json_str = _extract_json(raw)
                data = json.loads(json_str)

                if not isinstance(data, dict):
                    raise ValueError("Response is not a JSON object")

                missing = set(schema.keys()) - set(data.keys())
                if missing:
                    raise ValueError(f"Missing fields: {missing}")

                if coerce_types:
                    data = {
                        k: _coerce_value(data[k], schema[k])
                        if k in schema else data[k]
                        for k in data
                    }

                return data

            except (json.JSONDecodeError, ValueError) as exc:
                last_error = str(exc)
                logger.warning(
                    "Structured generation attempt %d/%d failed: %s",
                    attempt + 1, self.max_retries + 1, exc,
                )

        raise StructuredOutputError(
            f"Failed to produce valid structured output after "
            f"{self.max_retries + 1} attempts. Last error: {last_error}"
        )

    def generate_pydantic(
        self,
        prompt: str,
        model_class: Any,
        system: Optional[str] = None,
    ) -> Any:
        """
        Generate output validated against a Pydantic model.

        Requires ``pydantic>=2.0`` to be installed.

        Args:
            prompt: User prompt.
            model_class: A Pydantic ``BaseModel`` subclass.
            system: Optional system message.

        Returns:
            An instance of *model_class*.
        """
        if not _HAS_PYDANTIC:
            raise ImportError(
                "pydantic is required for generate_pydantic(). "
                "Install with: pip install pydantic"
            )

        schema_fields = {}
        for name, field_info in model_class.model_fields.items():
            annotation = field_info.annotation
            type_name = getattr(annotation, "__name__", str(annotation))
            schema_fields[name] = type_name

        raw_dict = self.generate(prompt, schema_fields, system=system, coerce_types=False)

        last_error: Optional[str] = None
        for attempt in range(self.max_retries + 1):
            try:
                return model_class.model_validate(raw_dict)
            except ValidationError as exc:
                last_error = str(exc)
                correction_prompt = (
                    f"{_schema_to_instruction(schema_fields)}\n\n{prompt}\n\n"
                    f"Your previous output failed validation: {last_error}\n"
                    f"Please fix and output ONLY valid JSON."
                )
                try:
                    raw = self.client.generate(
                        self.model, correction_prompt,
                        system=system, temperature=self.temperature,
                    )
                    raw_dict = json.loads(_extract_json(raw))
                except Exception:
                    continue

        raise StructuredOutputError(
            f"Pydantic validation failed after retries. Last error: {last_error}"
        )

    def generate_list(
        self,
        prompt: str,
        item_schema: Dict[str, str],
        system: Optional[str] = None,
        coerce_types: bool = True,
    ) -> List[Dict[str, Any]]:
        """Generate a JSON array of objects matching *item_schema*."""
        instruction = (
            f"Respond with a JSON array where each element has these fields:\n"
        )
        for key, typ in item_schema.items():
            instruction += f'  "{key}": <{typ}>\n'
        instruction += "Do NOT include any text outside the JSON array."

        full_prompt = f"{instruction}\n\n{prompt}"

        last_error: Optional[str] = None
        for attempt in range(self.max_retries + 1):
            if attempt > 0 and last_error:
                full_prompt = (
                    f"{instruction}\n\n{prompt}\n\n"
                    f"Previous output was invalid: {last_error}\n"
                    f"Output ONLY a valid JSON array."
                )
            try:
                raw = self.client.generate(
                    self.model, full_prompt,
                    system=system, temperature=self.temperature,
                )
                cleaned = re.sub(r"```(?:json)?\s*", "", raw).replace("```", "")
                match = re.search(r"\[[\s\S]*\]", cleaned)
                if not match:
                    raise ValueError("No JSON array found")
                data = json.loads(match.group(0))
                if not isinstance(data, list):
                    raise ValueError("Response is not a JSON array")

                if coerce_types:
                    data = [
                        {
                            k: _coerce_value(item[k], item_schema[k])
                            if k in item_schema else item[k]
                            for k in item
                        }
                        for item in data
                    ]
                return data
            except (json.JSONDecodeError, ValueError) as exc:
                last_error = str(exc)

        raise StructuredOutputError(
            f"Failed to produce valid list output after retries. "
            f"Last error: {last_error}"
        )


class StructuredOutputError(Exception):
    """Raised when structured output generation fails after all retries."""
