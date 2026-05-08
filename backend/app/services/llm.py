"""
Thin wrapper around the Anthropic client that logs every call.
Satisfies the §8 observability requirement: timestamp, model, prompt,
response, tokens, cost, latency, calling function — recorded from day one.

Cost table (update when Anthropic changes pricing):
  claude-haiku-4-5-*   : $0.80 / $4.00  per MTok in/out
  claude-sonnet-4-6     : $3.00 / $15.00 per MTok in/out
  claude-opus-4-7       : $15.00 / $75.00 per MTok in/out
"""
import json
import time
from dataclasses import dataclass, field
from pathlib import Path

import anthropic

from ..config import settings

_client: anthropic.Anthropic | None = None

# Cost in micro-dollars per token (input, output)
_COST_TABLE: dict[str, tuple[float, float]] = {
    "claude-haiku-4-5-20251001": (0.80 / 1_000_000, 4.00 / 1_000_000),
    "claude-sonnet-4-6":         (3.00 / 1_000_000, 15.00 / 1_000_000),
    "claude-opus-4-7":           (15.00 / 1_000_000, 75.00 / 1_000_000),
}


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    return _client


@dataclass
class _MockContent:
    text: str


@dataclass
class _MockUsage:
    input_tokens: int = 0
    output_tokens: int = 0


@dataclass
class _MockMessage:
    content: list = field(default_factory=list)
    usage: _MockUsage = field(default_factory=_MockUsage)


def _cost_cents(model: str, input_tokens: int, output_tokens: int) -> int:
    in_rate, out_rate = _COST_TABLE.get(model, (0.0, 0.0))
    dollars = in_rate * input_tokens + out_rate * output_tokens
    return round(dollars * 100)


def _write_jsonl_log(record: dict) -> None:
    log_path = Path(settings.llm_log_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a") as f:
        f.write(json.dumps(record) + "\n")


def create_message(
    *,
    model: str,
    messages: list[dict],
    system: str = "",
    max_tokens: int = 1024,
    calling_function: str = "unknown",
) -> anthropic.types.Message | _MockMessage:
    """
    Wrap client.messages.create with full observability logging.

    When ANTHROPIC_API_KEY is not set, returns a mock response so the pipeline
    can be exercised locally without an API key.
    """
    if not settings.anthropic_api_key:
        user_content = messages[-1]["content"] if messages else ""
        stub_text = f"[MOCK SUMMARY] {user_content[:120].strip()}..."
        return _MockMessage(content=[_MockContent(text=stub_text)])

    prompt_text = json.dumps(messages)
    start = time.monotonic()
    error_text = None
    response = None

    try:
        kwargs: dict = dict(model=model, messages=messages, max_tokens=max_tokens)
        if system:
            kwargs["system"] = system
        response = _get_client().messages.create(**kwargs)
        return response
    except Exception as exc:
        error_text = str(exc)
        raise
    finally:
        elapsed_ms = round((time.monotonic() - start) * 1000)
        input_tokens = response.usage.input_tokens if response else 0
        output_tokens = response.usage.output_tokens if response else 0
        response_text = response.content[0].text if response and response.content else ""

        record = {
            "called_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "calling_function": calling_function,
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost_cents": _cost_cents(model, input_tokens, output_tokens),
            "latency_ms": elapsed_ms,
            "prompt": prompt_text,
            "response": response_text,
            "error": error_text,
        }
        _write_jsonl_log(record)
