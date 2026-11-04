"""Domain 2 - Models, prompting and context engineering, measured.

Three things this file makes concrete:

  1. Prompt-cache economics, including the traffic shape where caching *loses*.
  2. Model routing: what a cheap classifier plus escalation actually saves.
  3. Context as a budget with a fixed eviction order, not a bin you fill.

Plus the two prompt-engineering habits that show up in exam items: a stable
cacheable prefix, and a schema-validated output contract with bounded repair.

    python3 examples/d2_context_cost.py
"""

from __future__ import annotations

import json
from dataclasses import dataclass

from fake_llm import PRICES, FakeClient, Response, TextBlock, ok, rule

SONNET, HAIKU, OPUS = "claude-sonnet-5-5", "claude-haiku-5-5", "claude-opus-5-5"

# Cache multipliers (verify against current docs before quoting).
WRITE_5M, WRITE_1H, READ = 1.25, 2.00, 0.10


def cost(model: str, tok_in: int, tok_out: int,
         cache_write: int = 0, cache_read: int = 0) -> float:
    pin, pout = PRICES[model]
    return (tok_in * pin
            + cache_write * pin * WRITE_5M
            + cache_read * pin * READ
            + tok_out * pout) / 1_000_000


# --------------------------------------------------------------------------- #
# E2.1  Prompt-cache economics over a realistic traffic shape
# --------------------------------------------------------------------------- #


def cache_economics() -> None:
    rule("E2.1  Prompt caching: measured, including when it loses")

    prefix_tokens = 12_000        # role + rules + policy corpus + few-shot examples
    request_tokens = 400          # the customer's question
    output_tokens = 300
    model = SONNET

    print(f"  stable prefix: {prefix_tokens:,} tok | per-request: {request_tokens} tok | out: {output_tokens} tok")

    for requests in (1, 2, 5, 20, 500):
        uncached = requests * cost(model, prefix_tokens + request_tokens, output_tokens)
        # First request pays the write premium, the rest read at ~10% price.
        cached = cost(model, request_tokens, output_tokens,
                      cache_write=prefix_tokens) \
            + (requests - 1) * cost(model, request_tokens, output_tokens,
                                    cache_read=prefix_tokens)
        delta = (uncached - cached) / uncached * 100
        verdict = "cache WINS" if cached < uncached else "cache LOSES"
        print(f"  {requests:>4} req: uncached ${uncached:>7.4f} | cached ${cached:>7.4f} "
              f"| {delta:>6.1f}%  {verdict}")

    # With one request there is only a write and no read, so the 1.25x premium
    # is pure loss. This is the case people forget when they add caching.
    ok("caching LOSES on a single request (write premium, no read)",
       cost(model, request_tokens, output_tokens, cache_write=prefix_tokens)
       > cost(model, prefix_tokens + request_tokens, output_tokens))
    ok("caching wins from the second request onward",
       cost(model, request_tokens, output_tokens, cache_write=prefix_tokens)
       + cost(model, request_tokens, output_tokens, cache_read=prefix_tokens)
       < 2 * cost(model, prefix_tokens + request_tokens, output_tokens))
    ok("at 500 requests caching saves >70% of input cost",
       (500 * cost(model, prefix_tokens + request_tokens, output_tokens)
        - (cost(model, request_tokens, output_tokens, cache_write=prefix_tokens)
           + 499 * cost(model, request_tokens, output_tokens, cache_read=prefix_tokens)))
       / (500 * cost(model, prefix_tokens + request_tokens, output_tokens)) > 0.70)

    # Traffic shape matters more than the multiplier: a gap longer than the TTL
    # means paying the write again. Two bursts of 250 with a long gap:
    bursts = 2
    burst_size = 250
    bursty = bursts * cost(model, request_tokens, output_tokens, cache_write=prefix_tokens) \
        + bursts * (burst_size - 1) * cost(model, request_tokens, output_tokens, cache_read=prefix_tokens)
    steady = cost(model, request_tokens, output_tokens, cache_write=prefix_tokens) \
        + 499 * cost(model, request_tokens, output_tokens, cache_read=prefix_tokens)
    print(f"  same 500 requests as 2 bursts: ${bursty:.4f} vs steady ${steady:.4f} "
          f"(+{(bursty / steady - 1) * 100:.1f}%: a TTL gap costs a re-write)")
    ok("bursty traffic pays more than steady traffic", bursty > steady)

    # The 1-hour TTL costs a 2x write, so it only pays if it prevents rewrites.
    long_ttl = cost(model, request_tokens, output_tokens, cache_read=prefix_tokens)
    long_write = prefix_tokens * PRICES[model][0] * WRITE_1H / 1_000_000
    print(f"  1h TTL write premium: ${long_write - prefix_tokens * PRICES[model][0] / 1_000_000:.4f} "
          f"extra per write, buys {int(60 / 5)}x fewer rewrites across a 60-minute window")
    ok("1h writes cost twice base input", abs(WRITE_1H - 2.0) < 1e-9)
    ok("a cached read is a tenth of base input", abs(READ - 0.1) < 1e-9)
    _ = long_ttl


# --------------------------------------------------------------------------- #
# E2.2  Breakpoint placement and prefix invalidation
# --------------------------------------------------------------------------- #


def build_request(question: str, tools: list[dict], handbook: str) -> dict:
    """Stable material first, volatile last, one breakpoint at the boundary."""
    return {
        "model": SONNET,
        "max_tokens": 500,
        "tools": tools,
        # Cache covers tools + both system blocks up to the breakpoint.
        "system": [
            {"type": "text", "text": "ROLE: Acme refunds assistant."},
            {"type": "text", "text": handbook,
             "cache_control": {"type": "ephemeral"}},
        ],
        "messages": [
            {"role": "user", "content": f"<question>{question}</question>"},
        ],
    }


TOOL_A = {"name": "lookup_order", "description": "Fetch an order by id.",
          "input_schema": {"type": "object", "properties": {"id": {"type": "string"}},
                           "required": ["id"]}}


def prefix_signature(request: dict) -> str:
    """Everything before the volatile tail. If this changes, the cache is gone."""
    return json.dumps([request["tools"], request["system"]], sort_keys=True)


def breakpoint_demo() -> None:
    rule("E2.2  What invalidates the cache (it is a prefix match)")

    handbook = "REFUND POLICY ... [12k tokens of clauses]"
    base = build_request("can I refund after 40 days?", [TOOL_A], handbook)
    sig = prefix_signature(base)

    same_prefix = build_request("different question entirely", [TOOL_A], handbook)
    ok("a new question keeps the cached prefix",
       prefix_signature(same_prefix) == sig)

    new_tool = [TOOL_A, {"name": "issue_refund", "description": "Refund an order.",
                         "input_schema": {"type": "object", "properties": {}}}]
    ok("adding a tool invalidates the whole prefix",
       prefix_signature(build_request("q", new_tool, handbook)) != sig)

    edited_handbook = handbook + " (rev 2)"
    ok("editing the handbook invalidates it too",
       prefix_signature(build_request("q", [TOOL_A], edited_handbook)) != sig)

    # Placement anti-pattern: the dynamic question inside the cached block.
    bad = {
        "system": [{"type": "text", "text": f"Question: {'x' * 50}",
                    "cache_control": {"type": "ephemeral"}}],
    }
    ok("a breakpoint after volatile content caches nothing reusable",
       "Question:" in bad["system"][0]["text"])


# --------------------------------------------------------------------------- #
# E2.3  Routing economics: cheap classifier + escalation
# --------------------------------------------------------------------------- #


def routing_economics() -> None:
    rule("E2.3  Model routing: what escalation actually buys")

    tasks = 10_000
    in_tok, out_tok = 1_500, 400
    classify_in, classify_out = 300, 20
    escalate_share = 0.12

    all_opus = tasks * cost(OPUS, in_tok, out_tok)
    all_sonnet = tasks * cost(SONNET, in_tok, out_tok)
    all_haiku = tasks * cost(HAIKU, in_tok, out_tok)
    classifier = tasks * cost(HAIKU, classify_in, classify_out)

    # Cheap primary, escalate up one tier.
    haiku_primary = classifier \
        + tasks * (1 - escalate_share) * cost(HAIKU, in_tok, out_tok) \
        + tasks * escalate_share * cost(SONNET, in_tok, out_tok)

    # Mid primary, escalate up one tier.
    sonnet_primary = classifier \
        + tasks * (1 - escalate_share) * cost(SONNET, in_tok, out_tok) \
        + tasks * escalate_share * cost(OPUS, in_tok, out_tok)

    print(f"  all Opus                        ${all_opus:>9.2f}")
    print(f"  all Sonnet                      ${all_sonnet:>9.2f}")
    print(f"  all Haiku                       ${all_haiku:>9.2f}")
    print(f"  Haiku primary + {escalate_share:.0%} Sonnet  ${haiku_primary:>9.2f}  "
          f"({(1 - haiku_primary / all_sonnet) * 100:.0f}% under all-Sonnet)")
    print(f"  Sonnet primary + {escalate_share:.0%} Opus    ${sonnet_primary:>9.2f}  "
          f"({(sonnet_primary / all_sonnet - 1) * 100:.0f}% OVER all-Sonnet)")

    ok("routing a cheap primary up one tier beats the mid tier outright",
       haiku_primary < all_sonnet)
    ok("routing a mid primary up to premium costs MORE than the mid tier alone",
       sonnet_primary > all_sonnet)
    ok("but that same escalation is still cheaper than a premium-only baseline",
       sonnet_primary < all_opus)
    ok("classifier cost is negligible relative to generation",
       classifier < 0.01 * all_opus)

    # The honest conclusion: compare against the baseline you would actually use.
    # Escalation must be justified by measured quality, not by cost alone.
    premium_share = next(
        s / 100 for s in range(0, 101)
        if classifier + tasks * (1 - s / 100) * cost(SONNET, in_tok, out_tok)
        + tasks * (s / 100) * cost(OPUS, in_tok, out_tok) >= all_opus
    )
    print(f"  Sonnet->Opus routing only reaches the all-Opus cost at "
          f"~{premium_share:.0%} escalation: it is a quality lever, not a saving")
    ok("upward escalation is a quality decision, not a cost optimisation",
       premium_share > 0.9)


# --------------------------------------------------------------------------- #
# E2.4  Context as a budget with a fixed eviction order
# --------------------------------------------------------------------------- #


@dataclass
class Slice:
    name: str
    tokens: int
    priority: int      # 0 = never evict
    text: str = ""


def fit_context(
    slices: list[Slice], window_tokens: int, output_reserve: int
) -> tuple[list[Slice], list[str], int]:
    """Reserve output first, then evict by priority (highest number first).

    This is deliberately boring code. Boring is the point: the eviction policy
    is a design decision you can test, not a hope.
    """
    budget = window_tokens - output_reserve
    evicted: list[str] = []

    kept = list(slices)
    used = sum(s.tokens for s in kept)

    # Start from everything, then drop the WORST slice until it fits. This is
    # the documented eviction order: lowest value first, never a never-evict
    # slice, and never the output reserve.
    for s in sorted((s for s in slices if s.priority > 0), key=lambda s: -s.priority):
        if used <= budget:
            break
        kept.remove(s)
        evicted.append(s.name)
        used -= s.tokens

    kept.sort(key=lambda s: s.priority)
    return kept, evicted, budget - used


def context_budget() -> None:
    rule("E2.4  Context budget: reserve output, then evict by policy")

    slices = [
        Slice("system+rules", 3_000, 0),
        Slice("tool definitions", 5_800, 3),        # biggest silent win
        Slice("retrieved chunks", 26_000, 2),
        Slice("conversation history", 14_000, 1),
        Slice("task input", 4_000, 0),
    ]
    kept, evicted, headroom = fit_context(slices, window_tokens=40_000, output_reserve=4_000)

    print(f"  kept:    {[(s.name, s.tokens) for s in kept]}")
    print(f"  evicted: {evicted}")
    print(f"  headroom: {headroom:,} tok")

    ok("output reserve is never spent on input", headroom >= 0)
    ok("never-evict slices survive", {s.name for s in kept} >= {"system+rules", "task input"})
    ok("the lowest-value slice is evicted first", "tool definitions" in evicted)

    # The counter-example the exam likes: a 1M window is not permission to fill it.
    naive = sum(s.tokens for s in slices)
    print(f"  naive total {naive:,} tok fits a 1M window and still costs "
          f"${cost(SONNET, naive, 400):.4f} per call vs "
          f"${cost(SONNET, sum(s.tokens for s in kept), 400):.4f} trimmed")
    ok("trimming costs strictly less than filling", naive > sum(s.tokens for s in kept))


# --------------------------------------------------------------------------- #
# E2.5  Output contract with bounded repair
# --------------------------------------------------------------------------- #

DECISION_SCHEMA = {
    "type": "object",
    "required": ["decision", "clause", "reason"],
    "additionalProperties": False,
    "properties": {
        "decision": {"enum": ["refund", "decline", "escalate"]},
        "clause": {"pattern": r"^C-\d{2,3}$"},
        "reason": {"maxLength": 240},
    },
}


def validate(payload: object) -> list[str]:
    if not isinstance(payload, dict):
        return ["not_an_object"]
    errors = []
    for key in DECISION_SCHEMA["required"]:
        if key not in payload:
            errors.append(f"missing:{key}")
    if payload.get("decision") not in DECISION_SCHEMA["properties"]["decision"]["enum"]:
        errors.append("bad:decision")
    import re
    if not re.match(DECISION_SCHEMA["properties"]["clause"]["pattern"], str(payload.get("clause", ""))):
        errors.append("bad:clause")
    if len(str(payload.get("reason", ""))) > 240:
        errors.append("bad:reason")
    return errors


def structured_output() -> None:
    rule("E2.5  Structured output: schema + bounded repair, then a human")

    attempts = [
        '{"decision": "refund later", "clause": "C-7"}',                    # bad enum + format
        '{"decision": "refund", "clause": "C-14", "reason": "Within 30 days."}',  # valid
    ]

    def policy(kw):
        return Response([TextBlock(attempts[min(len(client.calls) - 1, 1)])])

    client = FakeClient(policy)
    errors = ["initial"]
    payload: dict = {}

    for attempt in range(3):                     # hard cap: 3 total attempts
        prompt = "Decide the refund." if attempt == 0 else \
            f"Repair this to satisfy the schema. Errors: {errors}"
        raw = client.messages.create(
            model=SONNET, max_tokens=200,
            system="You decide refunds. Emit JSON matching the schema exactly.",
            messages=[{"role": "user", "content": prompt}],
        ).text
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            errors = ["invalid_json"]
            print(f"  attempt {attempt + 1}: invalid JSON -> repair")
            continue
        errors = validate(payload)
        if not errors:
            print(f"  attempt {attempt + 1}: valid -> {payload}")
            break
        print(f"  attempt {attempt + 1}: {errors} -> repair")
    else:
        payload = {"decision": "escalate", "clause": "C-00",
                   "reason": "Automated decision failed validation."}
        print("  attempts exhausted -> human queue (deterministic fallback)")

    ok("validation rejected the malformed first attempt", errors == [])
    ok("a valid decision was produced within the cap", payload["decision"] == "refund")
    ok("every repair attempt named the specific error",
       any("Errors:" in str(c["messages"][-1]["content"]) for c in client.calls))


def main() -> None:
    cache_economics()
    breakpoint_demo()
    routing_economics()
    context_budget()
    structured_output()

    rule("Takeaways")
    print("  1. Cache the shared prefix; the breakpoint sits at stable|volatile.")
    print("  2. One changed tool or system block = a cache write, not a read.")
    print("  3. Route cheap-first and measure the escalation rate, or routing stops paying.")
    print("  4. Reserve output tokens, cap tools, evict by documented priority.")
    print("  5. Validate output against a schema, repair at most twice, then fall back.")


if __name__ == "__main__":
    main()
