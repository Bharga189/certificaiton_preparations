"""Domain 6 - Stakeholders: turning one impossible SLA into a signable set.

The scenario is the canonical exam item. The sponsor wants "99.9% accuracy".
The modelling below shows why that number is meaningless until you fix the unit
and the segment, what it costs to actually achieve, and where the capacity
constraint hides.

    python3 examples/d6_sla.py
"""

from __future__ import annotations

from dataclasses import dataclass

from fake_llm import ok, rule

FIELDS_PER_DOC = 8
WORK_HOURS_PER_MONTH = 160


@dataclass
class Segment:
    name: str
    volume: int                # documents per month
    field_acc: float           # measured, held-out eval
    review_share: float        # fraction routed to human review
    review_minutes: float      # minutes of reviewer time per reviewed doc
    p95_auto_s: float

    @property
    def doc_acc(self) -> float:
        return self.field_acc ** FIELDS_PER_DOC

    @property
    def review_docs(self) -> float:
        return self.volume * self.review_share

    @property
    def review_hours(self) -> float:
        return self.review_docs * self.review_minutes / 60

    @property
    def fte(self) -> float:
        return self.review_hours / WORK_HOURS_PER_MONTH


SEGMENTS = [
    Segment("printed",  volume=38_400, field_acc=0.991, review_share=0.00, review_minutes=0.0, p95_auto_s=2.1),
    Segment("scanned",  volume=1_400,  field_acc=0.958, review_share=0.05, review_minutes=2.0, p95_auto_s=2.8),
    Segment("handwritten", volume=1_600, field_acc=0.612, review_share=1.00, review_minutes=3.2, p95_auto_s=3.4),
]


def global_field_accuracy(segments: list[Segment]) -> float:
    total_fields = sum(s.volume for s in segments) * FIELDS_PER_DOC
    correct = sum(s.volume * FIELDS_PER_DOC * s.field_acc for s in segments)
    return correct / total_fields


def global_doc_accuracy(segments: list[Segment]) -> float:
    total_docs = sum(s.volume for s in segments)
    return sum(s.volume * s.doc_acc for s in segments) / total_docs


# --------------------------------------------------------------------------- #
# E6.1  Why the single number is meaningless
# --------------------------------------------------------------------------- #


def demo_single_number() -> None:
    rule("E6.1  One number hides the whole decision")

    print(f"  {'segment':<13} {'vol/mo':>8} {'field':>7} {'doc':>7} {'review':>8} {'p95':>6}")
    for s in SEGMENTS:
        print(f"  {s.name:<13} {s.volume:>8,} {s.field_acc:>7.3f} {s.doc_acc:>7.3f} "
              f"{s.review_share:>7.0%} {s.p95_auto_s:>5.1f}s")

    gf, gd = global_field_accuracy(SEGMENTS), global_doc_accuracy(SEGMENTS)
    print(f"\n  aggregate field accuracy: {gf:.3f}")
    print(f"  aggregate document accuracy: {gd:.3f}")
    print(f"  handwritten document accuracy: {SEGMENTS[2].doc_acc:.3f}")

    ok("the aggregate field number passes a 95% requirement", gf > 0.95)
    ok("the aggregate document number does not", gd < 0.90)
    ok("one segment is effectively unusable without review", SEGMENTS[2].doc_acc < 0.10)


# --------------------------------------------------------------------------- #
# E6.2  Cost and capacity of the review path
# --------------------------------------------------------------------------- #


def demo_capacity(segments: list[Segment]) -> None:
    rule("E6.2  A human path is only a control if it has capacity")

    hours = sum(s.review_hours for s in segments)
    fte = sum(s.fte for s in segments)
    print(f"  review load: {hours:.0f} h/month across {sum(s.review_docs for s in segments):,.0f} docs"
          f" = {fte:.2f} FTE")

    ok("current volumes fit inside one reviewer", fte < 1.0)

    # The assumption that breaks the SLA: handwritten share rises.
    inflated = segments[:2] + [Segment("handwritten", 16_000, 0.612, 1.00, 3.2, 3.4)]
    hours2, fte2 = sum(s.review_hours for s in inflated), sum(s.fte for s in inflated)
    print(f"  if handwritten volume 10x's: {hours2:,.0f} h/month = {fte2:.2f} FTE")
    print(f"  -> capacity assumption must be written INTO the SLA")

    ok("a volume shift breaks the review capacity", fte2 > 5.0)
    ok("this is why the SLA states volume assumptions", fte2 > 5 * fte)


# --------------------------------------------------------------------------- #
# E6.3  The proposed SLA table
# --------------------------------------------------------------------------- #

@dataclass
class SlaRow:
    segment: str
    metric: str
    target: str
    method: str
    path: str


def proposed_sla(segments: list[Segment]) -> list[SlaRow]:
    rows = []
    for s in segments:
        if s.review_share >= 1.0:
            rows.append(SlaRow(
                s.name, "review turnaround",
                "95% within 4 business hours",
                "queue timestamps, weekly report",
                "human review before release",
            ))
        elif s.review_share > 0:
            rows.append(SlaRow(
                s.name, f"field accuracy (auto path, {1 - s.review_share:.0%} of volume)",
                ">= 98.5%",
                "n=200 weekly sample, adjudicated by client QA",
                "auto; 5% sampled + low-confidence band to review",
            ))
        else:
            rows.append(SlaRow(
                s.name, "field accuracy",
                ">= 99.0%",
                "n=200 weekly sample, adjudicated by client QA",
                "auto",
            ))
    rows.append(SlaRow("all", "p95 automated latency", "<= 2.5 s",
                       "APM histogram, per segment", "auto"))
    return rows


def demo_sla_table() -> None:
    rule("E6.3  What the sponsor can actually sign")

    rows = proposed_sla(SEGMENTS)
    for r in rows:
        print(f"  {r.segment:<13} {r.metric:<44} {r.target:<26} {r.path}")

    ok("every segment has a testable commitment", len(rows) == len(SEGMENTS) + 1)
    ok("the weak segment gets a human path, not an accuracy promise",
       any(r.segment == "handwritten" and "review" in r.path for r in rows))
    ok("every row names a measurement method", all(r.method for r in rows))
    ok("latency is committed at p95, not average",
       any("p95" in r.metric for r in rows))


# --------------------------------------------------------------------------- #
# E6.4  The go/no-go memo, generated from the numbers
# --------------------------------------------------------------------------- #


def demo_memo() -> None:
    rule("E6.4  The one-page memo (what the sponsor reads)")

    gf = global_field_accuracy(SEGMENTS)
    fte = sum(s.fte for s in SEGMENTS)
    memo = f"""\
  TO:      Head of Operations
  FROM:    Solution Architect
  RE:      Invoice extraction - pilot result and proposed acceptance

  RESULT    {gf:.1%} field accuracy overall on the held-out set (n=840 documents).
            Printed documents: 99.1% field / 93.0% document.
            Handwritten: 61.2% field, concentrated on 4% of volume -> human review.

  PROPOSAL  Per-segment SLA (attached). Handwritten routed to review,
            95% within 4 business hours; requires {fte:.1f} FTE at current volume.

  MEASURE   200-document weekly sample, adjudicated by your QA lead; dashboard shared.

  RISKS     1. Handwritten volume growth breaks review capacity (assumption: <= 2,000/mo).
            2. Scanned documents depend on source scan quality.
            3. Model change requires re-validation (5 working days).

  ASK       Approve per-segment SLA and the review headcount; go-live 14 Nov.
"""
    print(memo)

    ok("memo states the unit of the metric", "field accuracy" in memo)
    ok("memo states the measurement method", "adjudicated" in memo)
    ok("memo names the capacity assumption explicitly", "assumption" in memo.lower())
    ok("memo has a specific ask with a date", "Approve" in memo and "14 Nov" in memo)


def main() -> None:
    demo_single_number()
    demo_capacity(SEGMENTS)
    demo_sla_table()
    demo_memo()

    rule("Takeaways")
    print("  1. Fix the unit before agreeing the number: field vs document, per segment.")
    print("  2. A human path is only a control if you staff it; write volume assumptions in.")
    print("  3. Commit at p95 and name the measurement method and adjudicator.")
    print("  4. Bring the decision, not the decimal: evidence, proposal, risks, ask.")


if __name__ == "__main__":
    main()
