"""Domain 4 - Evaluation: stratified metrics, sample size, triage, unit economics.

The four habits this file drills:

  1. Report field-level AND document-level accuracy, per segment.
  2. Never call a delta a win without a confidence interval on the same items.
  3. Diagnose a failure by stage (retrieved? in-context? cited?) before blaming the model.
  4. Compare cost per *successful* task, not cost per call.

    python3 examples/d4_eval.py
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from statistics import mean

from fake_llm import ok, rule

random.seed(7)

FIELDS = ["vendor", "invoice_no", "po_number", "amount", "tax",
          "currency", "due_date", "terms", "line_items", "ship_to"]

# --------------------------------------------------------------------------- #
# A synthetic labelled eval set: two segments, deliberately imbalanced
# --------------------------------------------------------------------------- #


@dataclass
class Item:
    doc_id: str
    segment: str          # "printed" | "handwritten"
    truth: dict[str, str]
    pred: dict[str, str]


def make_dataset(n_printed: int = 180, n_hand: int = 20,
                 field_acc: dict[str, float] | None = None) -> list[Item]:
    acc = field_acc or {"printed": 0.995, "handwritten": 0.62}
    items: list[Item] = []
    for segment, count in (("printed", n_printed), ("handwritten", n_hand)):
        for i in range(count):
            truth = {f: f"{f}-{segment[:3]}-{i}" for f in FIELDS}
            pred = {
                f: (truth[f] if random.random() < acc[segment] else f"{f}-MISREAD")
                for f in FIELDS
            }
            items.append(Item(f"{segment[:3]}-{i}", segment, truth, pred))
    return items


def field_accuracy(items: list[Item]) -> float:
    correct = sum(
        1 for it in items for f in FIELDS if it.pred.get(f) == it.truth[f]
    )
    return correct / (len(items) * len(FIELDS)) if items else 0.0


def doc_accuracy(items: list[Item]) -> float:
    return mean(1.0 if all(it.pred.get(f) == it.truth[f] for f in FIELDS) else 0.0
                for it in items) if items else 0.0


# --------------------------------------------------------------------------- #
# E4.1  Field vs document accuracy, per segment
# --------------------------------------------------------------------------- #


def demo_stratified(items: list[Item]) -> None:
    rule("E4.1  Field-level vs document-level, stratified by segment")

    print(f"  {'segment':<14} {'n':>4} {'field acc':>10} {'doc acc':>9}")
    for segment in ("all", "printed", "handwritten"):
        subset = items if segment == "all" else [i for i in items if i.segment == segment]
        print(f"  {segment:<14} {len(subset):>4} {field_accuracy(subset):>10.3f} "
              f"{doc_accuracy(subset):>9.3f}")

    overall_field = field_accuracy(items)
    overall_doc = doc_accuracy(items)
    hand = [i for i in items if i.segment == "handwritten"]

    print(f"\n  independent-error prediction for doc acc: {overall_field ** len(FIELDS):.3f}"
          f" (actual {overall_doc:.3f})")

    ok("document accuracy is materially below field accuracy",
       overall_doc < overall_field - 0.05)
    ok("the aggregate hides a segment that fails badly",
       doc_accuracy(hand) < 0.05 < overall_doc)
    ok("field accuracy alone would pass a 95% requirement",
       overall_field > 0.95 > overall_doc)


# --------------------------------------------------------------------------- #
# E4.2  Confidence intervals and the sample-size trap
# --------------------------------------------------------------------------- #


def bootstrap_doc_ci(items: list[Item], iters: int = 1000) -> tuple[float, float]:
    """Resample documents, recompute document-level accuracy, take percentiles."""
    n = len(items)
    estimates = []
    for _ in range(iters):
        sample = [items[random.randrange(n)] for _ in range(n)]
        estimates.append(doc_accuracy(sample))
    estimates.sort()
    return estimates[int(0.025 * iters)], estimates[int(0.975 * iters)]


def demo_sample_size(items: list[Item]) -> None:
    rule("E4.2  Confidence intervals: why a 5-point win at n=40 is not a win")

    small = random.sample(items, 30)
    for label, subset in [
        ("n=30 (random sample)", small),
        (f"n={len(items)} (full set)", items),
    ]:
        lo, hi = bootstrap_doc_ci(subset)
        print(f"  {label:<26} doc acc {doc_accuracy(subset):.3f}  95% CI [{lo:.3f}, {hi:.3f}]  "
              f"width {hi - lo:.3f}")

    small_lo, small_hi = bootstrap_doc_ci(small)
    big_lo, big_hi = bootstrap_doc_ci(items)
    print(f"  the same estimator is {(small_hi - small_lo) / (big_hi - big_lo):.1f}x less precise "
          f"on 30 items than on {len(items)}")
    ok("the interval narrows substantially with sample size",
       (small_hi - small_lo) > 1.5 * (big_hi - big_lo))

    # A point-estimate delta inside an interval this wide is not a decision.
    print("  rule: if the CI of the DIFFERENCE straddles 0, run more items -- do not ship on the mean")


# --------------------------------------------------------------------------- #
# E4.3  Calibrating an LLM judge against humans
# --------------------------------------------------------------------------- #


def demo_judge_calibration() -> None:
    rule("E4.3  LLM judge: measure agreement, and the bias direction")

    human = [5, 4, 3, 5, 2, 4, 5, 3, 4, 2, 5, 4]
    judge = [5, 5, 4, 5, 3, 4, 5, 3, 5, 2, 5, 4]      # slightly generous on mid scores

    exact = sum(h == j for h, j in zip(human, judge)) / len(human)
    within_one = sum(abs(h - j) <= 1 for h, j in zip(human, judge)) / len(human)
    bias = mean(j - h for h, j in zip(human, judge))

    print(f"  exact agreement {exact:.2f} | within-1 {within_one:.2f} | mean bias {bias:+.2f}")
    print("  report: 'judge agrees with humans within 1 point on X% of items; "
          "known +0.1 verbosity bias'")

    ok("judge agreement is measured, not assumed", 0.5 <= exact <= 1.0)
    ok("the bias direction is quantified", bias > 0)
    ok("within-1 agreement is high enough to be useful", within_one >= 0.9)


# --------------------------------------------------------------------------- #
# E4.4  Failure triage by stage
# --------------------------------------------------------------------------- #


@dataclass
class Failure:
    doc_id: str
    retrieved: bool          # was the right chunk retrieved at all?
    in_context: bool         # did it survive assembly/truncation?
    cited: bool              # did the answer reference it?
    correct: bool            # was the final answer right?


def classify(failure: Failure) -> str:
    """The triage order matters more than the labels."""
    if not failure.retrieved:
        return "retrieval: chunking/filter/query/index"
    if not failure.in_context:
        return "assembly: truncation or context budget"
    if not failure.cited:
        return "generation: prompt/ordering/noise"
    if not failure.correct:
        return "source data: stale or contradictory"
    return "unknown"


def demo_triage() -> None:
    rule("E4.4  Triage a wrong answer by stage, not by model tier")

    failures = [
        Failure("d1", retrieved=True, in_context=True, cited=False, correct=False),
        Failure("d2", retrieved=False, in_context=False, cited=False, correct=False),
        Failure("d3", retrieved=True, in_context=False, cited=False, correct=False),
        Failure("d4", retrieved=True, in_context=True, cited=True, correct=False),
        Failure("d5", retrieved=True, in_context=True, cited=True, correct=False),
    ]
    causes = [classify(f) for f in failures]
    for f, cause in zip(failures, causes):
        print(f"  {f.doc_id}: {cause}")

    ok("retrieval misses are labelled as retrieval", causes[1].startswith("retrieval"))
    ok("truncation is not blamed on the model", causes[2].startswith("assembly"))
    ok("evidence present but ignored is a generation problem",
       causes[0].startswith("generation"))
    ok("no failure was blamed on the model tier", not any("model" in c for c in causes))

    counts: dict[str, int] = {}
    for c in causes:
        counts[c.split(":")[0]] = counts.get(c.split(":")[0], 0) + 1
    print(f"  distribution: {counts} -> fix in that order of volume, not by upgrading the model")


# --------------------------------------------------------------------------- #
# E4.5  Cost per successful task, including human escalation
# --------------------------------------------------------------------------- #


def demo_unit_economics() -> None:
    rule("E4.5  Cost per SUCCESSFUL task, not per call")

    human_cost = 4.50
    configs = {
        "A: Opus, 1.2 calls, 2% retry, 8% escalate": dict(
            cost_per_call=0.028, calls=1.2, retry=0.02, escalate=0.08),
        "B: Sonnet+router, 2.1 calls, 6% retry, 11% escalate": dict(
            cost_per_call=0.006, calls=2.1, retry=0.06, escalate=0.11),
    }

    print(f"  {'config':<46} {'$/call':>8} {'$/ticket':>9} {'$/resolved':>11}")
    results = {}
    for name, c in configs.items():
        per_ticket = c["cost_per_call"] * c["calls"] * (1 + c["retry"])
        per_resolved = per_ticket + c["escalate"] * human_cost
        results[name[0]] = per_resolved
        print(f"  {name:<46} {c['cost_per_call']:>8.3f} {per_ticket:>9.3f} {per_resolved:>11.3f}")

    ok("the config with cheaper calls is not the cheaper outcome", results["A"] < results["B"])
    print(f"  A wins by ${results['B'] - results['A']:.3f} per ticket because escalation dominates")


# --------------------------------------------------------------------------- #
# E4.6  A pre-registered gate
# --------------------------------------------------------------------------- #


@dataclass
class Gate:
    min_doc_accuracy: float = 0.90
    max_segment_drop: float = 0.03
    min_groundedness: float = 0.95
    max_p95_latency_s: float = 2.5
    max_cost_per_success: float = 0.05

    def evaluate(self, candidate: dict, baseline: dict) -> list[str]:
        failures = []
        if candidate["doc_accuracy"] < self.min_doc_accuracy:
            failures.append(f"doc_accuracy {candidate['doc_accuracy']:.3f} < {self.min_doc_accuracy}")
        for segment, acc in candidate["segments"].items():
            drop = baseline["segments"].get(segment, acc) - acc
            if drop > self.max_segment_drop:
                failures.append(f"segment {segment} dropped {drop:.3f}")
        if candidate["groundedness"] < self.min_groundedness:
            failures.append("groundedness below floor")
        if candidate["p95_s"] > self.max_p95_latency_s:
            failures.append("p95 latency over SLA")
        if candidate["cost_per_success"] > self.max_cost_per_success:
            failures.append("unit cost over budget")
        return failures


def demo_gate() -> None:
    rule("E4.6  A decision rule agreed BEFORE the run")

    gate = Gate()
    baseline = {"doc_accuracy": 0.88, "segments": {"printed": 0.96, "handwritten": 0.12},
                "groundedness": 0.94, "p95_s": 2.2, "cost_per_success": 0.041}

    good = {"doc_accuracy": 0.92, "segments": {"printed": 0.97, "handwritten": 0.16},
            "groundedness": 0.97, "p95_s": 2.3, "cost_per_success": 0.038}
    regressed = {"doc_accuracy": 0.93, "segments": {"printed": 0.99, "handwritten": 0.05},
                 "groundedness": 0.96, "p95_s": 2.1, "cost_per_success": 0.036}

    passed = gate.evaluate(good, baseline)
    failed = gate.evaluate(regressed, baseline)
    print(f"  candidate 1 -> {'PASS' if not passed else passed}")
    print(f"  candidate 2 -> {'PASS' if not failed else failed}")

    ok("the better candidate passes the gate", not passed)
    ok("an aggregate win with a segment regression is blocked",
       any("handwritten" in f for f in failed))
    ok("the rule was fixed in advance, so the decision is not post-hoc", gate.min_doc_accuracy == 0.90)


def main() -> None:
    items = make_dataset()
    demo_stratified(items)
    demo_sample_size(items)
    demo_judge_calibration()
    demo_triage()
    demo_unit_economics()
    demo_gate()

    rule("Takeaways")
    print("  1. Field accuracy flatters; document accuracy is what downstream sees.")
    print("  2. Stratify, always -- the aggregate hides the failing segment.")
    print("  3. Report CIs; a point estimate on a small set is not a decision.")
    print("  4. Calibrate the judge and publish its bias.")
    print("  5. Triage by stage; the model tier is the last suspect.")
    print("  6. Optimise cost per resolved task, including human time.")
    print("  7. Pre-register the gate, or you will rationalise the result.")


if __name__ == "__main__":
    main()
