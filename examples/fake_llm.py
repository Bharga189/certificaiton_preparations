"""Offline stand-ins for the Anthropic SDK response shapes.

Why this exists
---------------
Every example in this pack must run on a plane, in CI, and on a machine with no
API key. The classes below mirror the *parts of the real SDK that the examples
touch*, so the orchestration code you read here is the code you would ship:

    response = client.messages.create(
        model="claude-opus-5-5",
        max_tokens=1024,
        system=[{"type": "text", "text": SYSTEM, "cache_control": {"type": "ephemeral"}}],
        tools=TOOLS,
        messages=[{"role": "user", "content": "..."}],
    )
    response.content          # list[TextBlock | ToolUseBlock]
    response.stop_reason      # "end_turn" | "tool_use" | "max_tokens"
    response.usage            # input/output/cache tokens

What is *not* real here: the model. `FakeClient` calls a scripted `policy`
function, because these examples teach orchestration, measurement and control
flow -- not model quality. Swap `FakeClient` for `anthropic.Anthropic()` and the
surrounding code is unchanged.

Prices are USD per million tokens, from the Claude pricing page, Nov 2026.
They change: re-check before quoting them to anyone.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Iterable

# --------------------------------------------------------------------------- #
# Response shapes (mirroring anthropic.types)
# --------------------------------------------------------------------------- #


@dataclass
class TextBlock:
    text: str
    type: str = "text"


@dataclass
class ToolUseBlock:
    id: str
    name: str
    input: dict[str, Any]
    type: str = "tool_use"


@dataclass
class Usage:
    input_tokens: int = 0
    output_tokens: int = 0
    cache_creation_input_tokens: int = 0
    cache_read_input_tokens: int = 0

    def __add__(self, other: "Usage") -> "Usage":
        return Usage(
            self.input_tokens + other.input_tokens,
            self.output_tokens + other.output_tokens,
            self.cache_creation_input_tokens + other.cache_creation_input_tokens,
            self.cache_read_input_tokens + other.cache_read_input_tokens,
        )


@dataclass
class Response:
    content: list[Any]
    stop_reason: str = "end_turn"
    usage: Usage = field(default_factory=Usage)
    model: str = "claude-opus-5-5"

    @property
    def text(self) -> str:
        """Concatenate text blocks, like `response.content[0].text` in practice."""
        return "".join(b.text for b in self.content if isinstance(b, TextBlock))

    def tool_calls(self) -> list[ToolUseBlock]:
        return [b for b in self.content if isinstance(b, ToolUseBlock)]


# --------------------------------------------------------------------------- #
# Pricing
# --------------------------------------------------------------------------- #

#: model id -> (input $/MTok, output $/MTok)
PRICES: dict[str, tuple[float, float]] = {
    "claude-fable-5-1": (10.00, 50.00),
    "claude-opus-5-5": (4.00, 20.00),
    "claude-sonnet-5-5": (2.00, 10.00),
    "claude-haiku-5-5": (0.10, 0.50),
}

#: Relative price of each token class against base input price.
#: Cache writes cost more than base input; cache reads cost far less. VERIFY
#: these multipliers: 1.25x / 2x writes and 0.1x reads are the long-standing
#: values, and the 1-hour TTL write costs 2x.
CACHE_WRITE_5M = 1.25
CACHE_WRITE_1H = 2.00
CACHE_READ = 0.10


def cost_usd(model: str, usage: Usage) -> float:
    """Total cost of one or more calls, including cache accounting."""
    price_in, price_out = PRICES[model]
    uncached = usage.input_tokens * price_in
    write5 = usage.cache_creation_input_tokens * price_in * CACHE_WRITE_5M
    read = usage.cache_read_input_tokens * price_in * CACHE_READ
    out = usage.output_tokens * price_out
    return (uncached + write5 + read + out) / 1_000_000


def estimate_tokens(text: str) -> int:
    """Rough token count. Real tokenisation differs (~3.5-4 chars/token English).

    Never use an estimate to decide whether a prompt fits a context window in
    production: use the token counting endpoint / usage fields.
    """
    return max(1, len(text) // 4)


# --------------------------------------------------------------------------- #
# Scripted client
# --------------------------------------------------------------------------- #

#: A policy takes the kwargs of `messages.create` and returns either a string,
#: a list of blocks, or a `Response`.
Policy = Callable[[dict[str, Any]], "str | list[Any] | Response"]


class FakeMessages:
    def __init__(self, policy: Policy) -> None:
        self._policy = policy
        self.calls: list[dict[str, Any]] = []
        self.usage = Usage()

    def create(self, **kwargs: Any) -> Response:
        self.calls.append(kwargs)
        result = self._policy(kwargs)
        if isinstance(result, Response):
            response = result
        elif isinstance(result, str):
            response = Response(content=[TextBlock(result)])
        else:
            response = Response(content=result)

        # Simulate honest usage accounting so cost examples are not fiction.
        prompt_chars = len(str(kwargs.get("system", ""))) + len(str(kwargs.get("messages", "")))
        response.usage = response.usage or Usage()
        if not response.usage.input_tokens:
            response.usage.input_tokens = max(1, prompt_chars // 4)
        if not response.usage.output_tokens:
            response.usage.output_tokens = max(1, len(response.text) // 4)
        response.model = kwargs.get("model", response.model)
        self.usage = self.usage + response.usage
        return response


class FakeClient:
    """Drop-in for `anthropic.Anthropic()` in these examples."""

    def __init__(self, policy: Policy) -> None:
        self.messages = FakeMessages(policy)

    @property
    def calls(self) -> list[dict[str, Any]]:
        return self.messages.calls

    @property
    def spend(self) -> float:
        model = self.calls[0]["model"] if self.calls else "claude-sonnet-5-5"
        return cost_usd(model, self.messages.usage)


# --------------------------------------------------------------------------- #
# Helpers used across examples
# --------------------------------------------------------------------------- #


def blocks_text(response: Response) -> str:
    return response.text


def llm(messages: Iterable[dict[str, Any]]) -> str:
    """Last user message as text (handles string and block-list content)."""
    for message in reversed(list(messages)):
        if message.get("role") == "user":
            content = message.get("content")
            if isinstance(content, str):
                return content
            return " ".join(
                b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text"
            )
    return ""


def ok(label: str, condition: bool) -> None:
    """Tiny assertion helper so examples fail loudly when behaviour regresses."""
    if not condition:
        raise AssertionError(f"FAILED: {label}")
    print(f"  ok  {label}")


def rule(title: str = "") -> None:
    print("\n" + "=" * 78)
    if title:
        print(title)
        print("=" * 78)
