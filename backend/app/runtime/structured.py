"""Structured output: coerce a run's answer into a template schema and render it.

We use LiteLLM's JSON mode (response_format) with the template's output_schema in
the prompt to obtain typed JSON, then render it with a sandboxed Jinja2 template.
LiteLLM's native structured output is used instead of Instructor because the
cockpit's schemas are dynamic JSON Schema, not static Pydantic models.
"""

import json

from jinja2.sandbox import SandboxedEnvironment

from app.integrations.litellm_gateway import complete
from app.models.llm_connection import LLMConnection

# Sandboxed (no arbitrary attribute/code access) and autoescaping, so run/agent
# data rendered into an HTML template cannot inject markup (XSS).
_JINJA = SandboxedEnvironment(autoescape=True, trim_blocks=True, lstrip_blocks=True)


async def structure_output(connection: LLMConnection, text: str, output_schema: dict) -> dict:
    """Coerce ``text`` into a JSON object matching ``output_schema`` via the LLM."""
    messages = [
        {
            "role": "system",
            "content": (
                "Convert the user's text into a single JSON object matching this "
                "JSON Schema. Output only the JSON object.\n" + json.dumps(output_schema)
            ),
        },
        {"role": "user", "content": text},
    ]
    result = await complete(connection, messages, response_format={"type": "json_object"})
    try:
        return json.loads(result.content)
    except json.JSONDecodeError:
        # Degrade gracefully: keep the model's text if it wasn't valid JSON.
        return {"_unstructured": result.content}


def render_output(template_str: str, data: dict) -> str:
    """Render a Jinja2 template (sandboxed) with the structured data.

    Identifier-named fields are exposed as top-level variables; the full object is
    also available as ``data`` for non-identifier keys.
    """
    safe = {k: v for k, v in data.items() if isinstance(k, str) and k.isidentifier()}
    return _JINJA.from_string(template_str).render(data=data, **safe)


def compare_results(a: dict, b: dict, fields: list[str] | None = None) -> dict:
    """Structured diff of two run results, over the given fields (or all keys)."""
    keys = list(fields) if fields else sorted(set(a) | set(b))
    rows = [{"field": k, "a": a.get(k), "b": b.get(k), "equal": a.get(k) == b.get(k)} for k in keys]
    return {"fields": rows, "all_equal": all(r["equal"] for r in rows)}
