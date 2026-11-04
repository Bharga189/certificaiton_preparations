"""Domain 1 - Solution Design & Architecture, executed.

Runs every pattern in the ladder against a scripted client so you can see, side
by side: how many calls each pattern makes, what it costs, what happens when a
stage fails, and why a gate must be code rather than a prompt instruction.

    python3 examples/d1_patterns.py

Nothing here needs an API key. Swap `FakeClient` for `anthropic.Anthropic()`
and the orchestration code is what you would ship.
"""

from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field

from fake_llm import FakeClient, Response, TextBlock, ok, rule

# --------------------------------------------------------------------------- #
# A tiny "database" of freight quotes.
# Q-102 recovers on a second read; Q-103 is an unreadable scan.
# --------------------------------------------------------------------------- #

QUOTES: dict[str, dict] = {
    "Q-100": {"carrier": "NordFrakt", "cost_usd": 4180, "transit_days": 6},
    "Q-101": {"carrier": "AlpineAir", "cost_usd": 12950, "transit_days": 2},
    "Q-102": {"carrier": "BalticSea", "cost_usd": 7310, "transit_days": 9},
    "Q-103": {"carrier": "???", "cost_usd": None, "transit_days": None},   # unreadable
}

REQUIRED = ("carrier", "cost_usd", "transit_days")


def policy_violations(record: dict) -> list[str]:
    """Procurement policy as code -- the authority, not a prompt suggestion."""
    problems = []
    if record.get("cost_usd", 0) > 10_000 and record.get("transit_days", 99) <= 3:
        problems.append("air_freight_over_10k_requires_director_approval")
    return problems


# --------------------------------------------------------------------------- #
# E1.1  Prompt chaining with a code-enforced gate and selective retry
# --------------------------------------------------------------------------- #


def make_chain_client() -> FakeClient:
    def policy(kw):
        system = str(kw.get("system", ""))
        user = kw["messages"][-1]["content"]
        text = user if isinstance(user, str) else json.dumps(user)
        quote_id = text.split(":")[0].strip()

        if "EXTRACT" in system:
            record = dict(QUOTES[quote_id])
            # First pass on Q-102 misreads the scan; naming the missing fields fixes it.
            if quote_id == "Q-102" and "Missing fields" not in text:
                record = {**record, "transit_days": None}
            if quote_id == "Q-103":
                record = {"carrier": "???", "cost_usd": None, "transit_days": None}
            return Response([TextBlock(json.dumps(record))])

        if "VALIDATE" in system:
            return Response([TextBlock(json.dumps({"violations": policy_violations(json.loads(text))}))])

        if "RECOMMEND" in system:
            return Response([TextBlock("Recommend NordFrakt: lowest landed cost within policy.")])

        raise AssertionError(f"unexpected system prompt: {system[:40]}")

    return FakeClient(policy)


@dataclass
class ChainResult:
    quote_id: str
    status: str                      # "ok" | "dead_letter" | "needs_human"
    record: dict | None = None
    notes: list[str] = field(default_factory=list)


def run_chain(client: FakeClient, quote_id: str) -> ChainResult:
    """extract -> gate -> validate -> gate -> recommend.

    The important lines are the `if`s. A prompt saying 'always return all
    fields' is a request; a branch that refuses to continue is a control.
    """
    raw = f"{quote_id}: FRA->SIN, quoted per attached scan"
    missing: list[str] = []

    for attempt in range(2):                       # bounded attempts
        prompt = raw if attempt == 0 else f"{raw}\nMissing fields, re-read the scan: {missing}"
        extracted = json.loads(client.messages.create(
            model="claude-haiku-5-5",
            max_tokens=256,
            system="EXTRACT carrier, cost_usd, transit_days as JSON. Unknown -> null.",
            messages=[{"role": "user", "content": prompt}],
        ).text)
        missing = [f for f in REQUIRED if extracted.get(f) in (None, "", "???")]
        if not missing:
            break
    else:
        # Attempts exhausted: stop here. Never recommend on unvalidated data.
        return ChainResult(quote_id, "dead_letter", extracted, [f"missing={missing}"])

    violations = json.loads(client.messages.create(
        model="claude-haiku-5-5",
        max_tokens=256,
        system="VALIDATE record against procurement policy. Return JSON {violations:[...]}.",
        messages=[{"role": "user", "content": json.dumps(extracted)}],
    ).text)["violations"]

    if violations:
        return ChainResult(quote_id, "needs_human", extracted, violations)

    recommendation = client.messages.create(
        model="claude-sonnet-5-5",
        max_tokens=256,
        system="RECOMMEND a carrier from the validated record. One sentence.",
        messages=[{"role": "user", "content": json.dumps(extracted)}],
    ).text
    return ChainResult(quote_id, "ok", extracted, [recommendation])


def demo_chain() -> tuple[list[ChainResult], FakeClient]:
    rule("E1.1  Prompt chaining with a code-enforced gate")
    client = make_chain_client()
    results = [run_chain(client, qid) for qid in QUOTES]
    for r in results:
        print(f"  {r.quote_id}: {r.status:<12} {r.notes}")

    stages = [str(c.get("system", "")).split()[0] for c in client.calls]
    print(f"  call log: {' -> '.join(stages)}")

    ok("clean quote completes all three stages", results[0].status == "ok")
    ok("policy exception goes to a human, not to the recommendation",
       results[1].status == "needs_human")
    ok("selective retry recovers a partially-read scan", results[2].status == "ok")
    ok("unreadable scan dead-letters after exactly two attempts",
       results[3].status == "dead_letter")
    ok("dead-lettered quote never reaches VALIDATE or RECOMMEND",
       stages.count("RECOMMEND") == 2 and stages.count("VALIDATE") == 3)
    return results, client


# --------------------------------------------------------------------------- #
# E1.2  Routing: cheap classifier first, escalate on measured uncertainty
# --------------------------------------------------------------------------- #


def demo_routing() -> None:
    rule("E1.2  Routing with cheap-first escalation")

    messages = {
        "m1": ("general", 0.94),
        "m2": ("technical", 0.88),
        "m3": ("billing_dispute", 0.61),   # low confidence AND high-stakes class
        "m4": ("technical", 0.55),         # low confidence only
    }

    def policy(kw):
        user = kw["messages"][-1]["content"]
        if "CLASSIFY" in str(kw.get("system", "")):
            intent, conf = messages[user.split(":")[0].strip()]
            return Response([TextBlock(json.dumps({"intent": intent, "confidence": conf}))])
        return Response([TextBlock(f"[{kw['model']}] handled {user.split(':')[0]}")])

    client = FakeClient(policy)
    chosen: list[tuple[str, str, float]] = []

    for msg_id in messages:
        route = json.loads(client.messages.create(
            model="claude-haiku-5-5",
            max_tokens=32,
            system="CLASSIFY intent as general|technical|billing_dispute with confidence 0-1.",
            messages=[{"role": "user", "content": f"{msg_id}: my invoice is wrong again"}],
        ).text)

        # Two independent escalation triggers. Both are code, both are measured.
        escalate = route["confidence"] < 0.70 or route["intent"] == "billing_dispute"
        model = "claude-opus-5-5" if escalate else "claude-sonnet-5-5"

        client.messages.create(
            model=model,
            max_tokens=256,
            system="ANSWER using the specialist playbook.",
            messages=[{"role": "user", "content": f"{msg_id}: my invoice is wrong again"}],
        )
        chosen.append((msg_id, model, route["confidence"]))
        print(f"  {msg_id}: intent={route['intent']:<15} conf={route['confidence']:.2f} -> {model}")

    ok("low-confidence item escalated", chosen[3][1] == "claude-opus-5-5")
    ok("high-stakes class escalated even at 0.61 confidence", chosen[2][1] == "claude-opus-5-5")
    ok("confident routine items stayed on the mid tier", chosen[0][1] == "claude-sonnet-5-5")
    ok("routing is a workflow: code chose the branch, not the model",
       all(len(c["messages"]) == 1 for c in client.calls))


# --------------------------------------------------------------------------- #
# E1.3  Parallelisation: sectioning and voting
# --------------------------------------------------------------------------- #

SECTIONS = ["parties", "term", "termination", "liability", "data_processing"]


def demo_parallel() -> None:
    rule("E1.3a Parallel sectioning (independent subtasks)")

    def policy(kw):
        section = str(kw.get("system", "")).split(":")[-1].strip()
        return Response([TextBlock(json.dumps(
            {"section": section, "risk": section in ("liability", "termination")}))])

    client = FakeClient(policy)
    with ThreadPoolExecutor(max_workers=5) as pool:
        results = list(pool.map(
            lambda s: (s, json.loads(client.messages.create(
                model="claude-sonnet-5-5",
                max_tokens=256,
                system=f"EXTRACT risks from section: {s}",
                messages=[{"role": "user", "content": "contract text..."}],
            ).text)),
            SECTIONS,
        ))

    for section, payload in results:
        print(f"  {section:<16} risk={payload['risk']}")
    ok("every independent section reviewed", len(results) == len(SECTIONS))
    ok("failures are attributable to one section",
       {s for s, p in results if p["risk"]} == {"liability", "termination"})

    rule("E1.3b Voting (confidence on a risky classification)")

    ballots_script = ["APPROVE", "APPROVE", "REJECT", "APPROVE", "REJECT"]

    def voter(kw):
        return Response([TextBlock(ballots_script[len(client.calls) - 1])])

    client = FakeClient(voter)
    ballots = [
        client.messages.create(
            model="claude-sonnet-5-5",
            max_tokens=8,
            # Different reviewer framing decorrelates errors; identical prompts
            # give you five copies of the same mistake.
            system=f"REVIEWER PERSPECTIVE {i}: decide APPROVE or REJECT on policy grounds.",
            messages=[{"role": "user", "content": "expense claim..."}],
        ).text
        for i in range(5)
    ]
    approvals = ballots.count("APPROVE")
    print(f"  ballots={ballots} -> majority={'APPROVE' if approvals >= 3 else 'REJECT'}")
    ok("voting aggregates five independent passes", approvals == 3)


# --------------------------------------------------------------------------- #
# E1.4  Orchestrator-workers: the subtask list is data-dependent
# --------------------------------------------------------------------------- #

TICKET = "Migrate our auth module off the deprecated SDK and keep tests green."


def demo_orchestrator() -> None:
    rule("E1.4  Orchestrator-workers (subtasks unknown until the input is read)")

    def policy(kw):
        user = kw["messages"][-1]["content"]
        system = str(kw.get("system", ""))
        if "ORCHESTRATOR-PLAN" in system:
            # In reality the model reads a repo map; scripted here for determinism.
            return Response([TextBlock(json.dumps(
                ["src/auth/session.ts", "src/auth/oauth.ts", "tests/auth.spec.ts"]))])
        if "WORKER" in system:
            target = user.split("::")[0]
            return Response([TextBlock(json.dumps({"file": target, "patch": f"// migrated {target}"}))])
        if "ORCHESTRATOR-SYNTH" in system:
            return Response([TextBlock("3 files migrated; 1 conflict in session.ts resolved.")])
        raise AssertionError(system[:30])

    client = FakeClient(policy)

    plan = json.loads(client.messages.create(
        model="claude-sonnet-5-5", max_tokens=512,
        system="ORCHESTRATOR-PLAN: read the repo map and list the files to change.",
        messages=[{"role": "user", "content": TICKET}],
    ).text)
    print(f"  plan ({len(plan)} subtasks): {plan}")

    with ThreadPoolExecutor(max_workers=3) as pool:
        edits = list(pool.map(
            lambda f: json.loads(client.messages.create(
                model="claude-sonnet-5-5", max_tokens=512,
                system="WORKER: migrate exactly one file. Return JSON {file, patch}.",
                messages=[{"role": "user", "content": f"{f}::{TICKET}"}],
            ).text),
            plan,
        ))

    summary = client.messages.create(
        model="claude-sonnet-5-5", max_tokens=256,
        system="ORCHESTRATOR-SYNTH: merge worker patches, report conflicts.",
        messages=[{"role": "user", "content": json.dumps(edits)}],
    ).text

    print(f"  workers: {[e['file'] for e in edits]}")
    print(f"  synthesis: {summary}")
    ok("plan was generated, not hardcoded", len(plan) == 3)
    ok("each worker saw only its own subtask", len(edits) == 3)
    ok("synthesis runs once, after the workers", "conflict" in summary)
    ok("cost shape is 1 plan + N workers + 1 synth", len(client.calls) == 5)


# --------------------------------------------------------------------------- #
# E1.5  Evaluator-optimizer with a stop rule and a budget
# --------------------------------------------------------------------------- #


def demo_evaluator_optimizer() -> None:
    rule("E1.5  Evaluator-optimizer (bounded, with an explicit stop rule)")

    scores = [0.55, 0.72, 0.86]

    def policy(kw):
        system = str(kw.get("system", ""))
        if "GENERATE" in system:
            n = sum(1 for c in client.calls if "GENERATE" in str(c.get("system", "")))
            return Response([TextBlock(f"draft v{n}")])
        if "EVALUATE" in system:
            n = sum(1 for c in client.calls if "EVALUATE" in str(c.get("system", "")))
            return Response([TextBlock(json.dumps(
                {"score": scores[min(n - 1, 2)], "issues": ["vague", "no citation"]}))])
        raise AssertionError(system[:30])

    client = FakeClient(policy)
    budget_calls = 6
    best_score = 0.0

    for round_no in range(3):
        draft = client.messages.create(
            model="claude-sonnet-5-5", max_tokens=1024,
            system="GENERATE a policy answer with citations.",
            messages=[{"role": "user", "content": "parental leave after 5 years?"}],
        ).text
        review = json.loads(client.messages.create(
            model="claude-haiku-5-5", max_tokens=128,      # cheap critic
            system="EVALUATE the draft against the rubric. JSON {score, issues}.",
            messages=[{"role": "user", "content": draft}],
        ).text)
        best_score = review["score"]
        print(f"  round {round_no + 1}: score={review['score']} issues={review['issues']}")
        if review["score"] >= 0.85:                       # testable stop rule
            print("  stop: quality bar met")
            break
        if len(client.calls) >= budget_calls:             # cost guard
            print("  stop: call budget reached")
            break

    ok("loop terminated within the call budget", len(client.calls) <= budget_calls)
    ok("accepted draft met the stated bar", best_score >= 0.85)
    ok("critic runs on a cheaper tier than the generator",
       client.calls[1]["model"] == "claude-haiku-5-5")


# --------------------------------------------------------------------------- #
# E1.6  Cost/latency shape of each pattern (why the ladder exists)
# --------------------------------------------------------------------------- #


@dataclass
class Pattern:
    name: str
    calls: int
    hops: int            # depth of dependent calls
    note: str


PATTERNS = [
    Pattern("single augmented call", 1, 1, "cheapest, most testable"),
    Pattern("3-stage chain + gates", 3, 3, "auditable; latency = 3 hops"),
    Pattern("route -> specialist", 2, 2, "cheap classifier pays for itself"),
    Pattern("section x5 (parallel)", 6, 2, "wide, not deep"),
    Pattern("orchestrator + 3 workers", 5, 3, "flexible, cost grows with N"),
    Pattern("agent loop (avg 9 turns)", 9, 9, "unbounded tail latency"),
    Pattern("supervisor + 2 workers", 12, 6, "only for separable contexts"),
]


def demo_ladder() -> None:
    rule("E1.6  Cost and latency shape by pattern (assume 900 ms per call)")

    per_call_ms, per_call_usd = 900, 0.004
    print(f"  {'pattern':<26} {'calls':>5} {'hops':>5} {'p50':>8} {'$/task':>8}  note")
    for p in PATTERNS:
        print(f"  {p.name:<26} {p.calls:>5} {p.hops:>5} "
              f"{p.hops * per_call_ms / 1000:>7.1f}s {p.calls * per_call_usd:>8.3f}  {p.note}")

    ok("a 3-stage chain is latency-linear", PATTERNS[1].hops * per_call_ms == 2700)
    ok("parallel sectioning adds width, not depth", PATTERNS[3].hops == 2)
    ok("an unbounded agent loop has the worst tail", PATTERNS[5].hops == 9)


def main() -> None:
    results, chain_client = demo_chain()
    demo_routing()
    demo_parallel()
    demo_orchestrator()
    demo_evaluator_optimizer()
    demo_ladder()

    rule("Takeaways")
    print("  1. Gates are branches in code. A prompt cannot refuse to continue.")
    print("  2. Each rung up buys flexibility and costs latency + testability.")
    print("  3. Retry selectively; checkpoint; dead-letter; cap iterations.")
    print("  4. Verify with the environment, not with self-reported confidence.")
    print(f"\n  chain: {len(chain_client.calls)} calls, "
          f"${chain_client.spend:.5f} simulated, "
          f"{chain_client.messages.usage.input_tokens} input tokens")
    print(f"  did not complete cleanly: "
          f"{[(r.quote_id, r.status) for r in results if r.status != 'ok']}")


if __name__ == "__main__":
    main()
