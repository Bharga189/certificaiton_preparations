# 04 · Evaluation, Testing & Optimization — 16%

> **What this domain really tests:** can you prove a system got better, or only feel that it did?

Every item here resolves to one of four habits: **a metric that matches the business outcome**, **an eval set you
didn't tune on**, **a decision rule agreed before the test**, and **diagnosis before escalation**.

---

## 1. Metrics: choose the one the sponsor would sign

| Metric | Definition | Use when | Trap |
|---|---|---|---|
| **Task success / completion** | Did the workflow achieve its goal end-to-end? | Agents, multi-step flows | Graded too coarsely to compare variants |
| **Exact match** | Output == reference | Classification, extraction of closed fields | Brittle to formatting; often unfair |
| **Precision / recall / F1** | Per-class quality | Imbalanced labels, safety filters | Averaging hides the class that matters |
| **Field-level accuracy** | % of individual fields correct | Forms, invoices, records | Optimistic vs document-level |
| **Document-level accuracy** | % of documents with *all* fields correct | Anything downstream of the whole record | Drops fast with field count — use *both* |
| **Groundedness / citation validity** | Every claim traceable to retrieved evidence | RAG, regulated answers | Rewards refusing to answer |
| **Refusal correctness** | Right things refused, right things answered | Safety-critical, policy Q&A | Only measured with hard negatives |
| **Latency p50 / p95** | Response time distribution | Anything with an SLA | Averages hide the tail users feel |
| **Cost per successful task** | Total spend ÷ tasks succeeded | Business case, routing decisions | Per-call cost hides retries and failures |
| **Escalation / containment rate** | % routed to humans | Support, triage | Optimising it alone encourages silent failure |

**Two metric rules the exam rewards:**

1. **Per-successful-task, not per-call.** A cheap model with 30% retries can cost more than a mid-tier model
   that lands first time.
2. **Stratify, always.** Report by document type, language, intent, tenant. An aggregate that improves while
   handwritten invoices collapse is a regression dressed as a win.

### The field-vs-document maths (memorise this shape)

10 fields per document, each 97% accurate and independent:

```
P(all correct) = 0.97^10 ≈ 0.74
```

So "97% field accuracy" is a **74% document accuracy** — the number the downstream system actually experiences.
And errors are correlated (handwriting affects all fields on a page), so reality is usually *worse* than the
independent model predicts. This is why an SLA must name the metric *and* the unit.

---

## 2. Building an eval set that survives scrutiny

### Rules

| Rule | Why |
|---|---|
| Sample **by segment**, not at random | Random sampling under-represents the rare, expensive cases |
| Keep a **held-out test set** you touch only at the end | Otherwise you are fitting the test set by proxy |
| Version the set alongside prompts; never edit an item to make a run pass | Preserves comparability |
| Include **hard negatives** and adversarial cases | Measures refusal and boundaries, not just the happy path |
| ≥ 30 items per segment you intend to report on; 100–300 total for iteration | Below that, differences are noise |
| Two human labellers on a sample; measure agreement | Reveals whether the rubric is even well-defined |
| Store the **input, expected output, and rationale** | Rationale is what makes relabelling possible |

### Composition of a useful set (rough shape)

| Slice | Share | Purpose |
|---|---|---|
| Typical cases | 50% | Real distribution; catches broad regressions |
| Known-hard cases | 25% | Handwriting, long docs, ambiguity, code-switching |
| Edge/boundary cases | 15% | Exactly-at-threshold, empty, malformed |
| Adversarial / injection | 10% | Safety and robustness |

A set of 100 typical cases tells you almost nothing about the failure you will actually have in production.

---

## 3. Grading methods

| Method | Good for | Costs | Guardrails |
|---|---|---|---|
| **Deterministic checks** (schema, regex, unit tests, numeric tolerance) | Format, structure, calculations | Free, instant | Only checks what you encoded |
| **Exact / fuzzy match** against reference | Closed fields, short answers | Cheap | Formatting brittleness; normalise first |
| **LLM-as-judge** with a rubric | Open-ended quality, tone, groundedness | Cheap-ish, needs its own eval | Judge bias: position, verbosity, self-preference |
| **Pairwise comparison** | "Is A better than B?" | Two calls per pair | Swap positions to cancel order bias |
| **Human review** (sampled) | Ground truth, calibration, high-stakes | Expensive | Inter-rater agreement; rubric drift |

### Making an LLM judge trustworthy

1. **Rubric with explicit criteria and anchors** ("5 = every claim cited and no invented clause; 3 = one
   uncited claim…").
2. **Calibrate against humans** on ≥ 50 items; report agreement. An uncalibrated judge is an opinion with an
   API bill.
3. **Randomise order** in pairwise tests and average both directions.
4. **Blind the judge** to which variant produced the output.
5. **Re-run the judge when you change the judge prompt** — it is a model too, and it drifts.

---

## 4. Statistics without overclaiming

- **A 2-point difference on 40 items is noise.** Rough standard error for p≈0.8, n=40 is ~6 points. Report
  confidence intervals or at least the sample size next to the number.
- **Bootstrap the CI** (resample the eval set 1,000×, take the 2.5–97.5 percentiles). It is five lines of code
  and it prevents most bad decisions.
- **Pre-register the decision rule**: "ship if document-level accuracy ≥ 92% and p95 latency ≤ 2.5 s and no
  segment drops > 3 points." Decide before you look; otherwise you will rationalise.
- **Multiple comparisons**: testing 12 segments and celebrating the one that improved is how noise gets shipped.
- **Paired comparisons**: run A and B on the *same* items. Unpaired runs on different samples are not
  comparable.

---

## 5. A/B testing in production

| Element | Practice |
|---|---|
| Unit of randomisation | User or request, consistently (same user same variant) |
| Traffic split | Start 5% canary, not 50/50 |
| Guardrail metrics | Safety blocks, escalation rate, p95 latency, cost/task — auto-rollback thresholds |
| Duration | Pre-compute the sample size; don't peek daily and stop on a good day |
| Measurement | Log variant + outcome; use the same outcome definition as the offline eval |
| Segment analysis | Pre-declared segments only |
| Exit criteria | Ship / iterate / roll back, written down |

Offline eval decides *whether to test*; online test decides *whether to ship*. Both, in that order.

---

## 6. Diagnosing bad answers (the triage tree)

Work top-down; do not skip to "use a bigger model".

```
1. Was the correct evidence retrieved?           ── no → retrieval problem (chunking, filters, query, index)
2. Was it in the context sent to the model?      ── no → assembly/truncation bug
3. Did the model cite it?                        ── no → prompt/ordering/dilution (put question last, trim noise)
4. Did it cite it but answer wrongly?            ── source data stale or contradictory → data problem
5. Right answer, wrong format?                   ── output contract / schema / validation
6. Fluent and unsupported (no evidence)?          ── hallucination: add grounding rule + refusal path
7. Correct on eval, wrong in production?          ── distribution shift or prompt-version mismatch
```

### Hallucination taxonomy

| Type | Cause | Fix |
|---|---|---|
| **Retrieval miss** | Query/document mismatch, ACL over-filtering | Hybrid retrieval, query rewriting, rerank |
| **Stale source** | Old version indexed | Freshness metadata, incremental reindex |
| **Over-generalisation** | Model answering from priors | "Use only the excerpts"; INSUFFICIENT_CONTEXT path |
| **Prompt ambiguity** | Under-specified task | Output contract, few-shot with hard negatives |
| **Confident fabrication of IDs/dates** | No grounding check | Citation validation, numeric cross-check |
| **Model mismatch** | Task needs reasoning the tier lacks | Upgrade *after* 1–5 are ruled out |

**"Model mismatch" is the last diagnosis, never the first.** That ordering is worth points on its own.

---

## 7. Optimisation: cost and latency without losing quality

| Lever | Saves | Cost | When it's right |
|---|---|---|---|
| **Prompt caching** | 50–90% of input on stable prefixes | Write premium, TTL management | High-volume, shared prefix |
| **Model routing** | 40–70% | Classifier + complexity | Volume with a clear easy/hard split |
| **Context trimming** | 30–60% tokens | Engineering + eval | Always, once measured |
| **Batch API** | ~50% on eligible workloads | Latency up to 24h | Offline extraction, backfills |
| **Parallelisation** | Latency, not cost | More concurrent calls | Independent subtasks |
| **Streaming** | Perceived latency | — | Interactive UX |
| **Output length caps** | 20–40% of cost | Might truncate | Any structured output |
| **Distillation to a small model** | Large | Data + evals | Very high volume, stable task |

**Order of operations:** measure → trim context → cache → route → then consider a tier change. Reversing that
order is how teams pay more for the same quality.

**Unit economics:** report **cost per successful task** and **cost per resolved ticket**, not cost per token.
Include retries, failed calls and human review time.

---

## 8. Regression discipline

- Prompts and model versions are **pinned configuration**, not code comments.
- A model upgrade is a **change**: re-run the full eval, compare per segment, and shadow it on production
  traffic before switching.
- The eval runs in **CI** on every prompt change, with a pass gate (e.g. no segment down > 3 points).
- Keep a **failure gallery**: each production failure becomes a test case with a rationale. This is the single
  highest-yield eval practice.
- Watch for **silent drift**: input distribution changes (new product, new language, new document type) without
  any code change.

---

## 9. Worked examples

### E4.1 Reporting accuracy honestly

A vendor says "97% accurate". You ask: field or document? which segment? measured on what set?

| Report | Value |
|---|---|
| Field-level, all documents | 97.0% |
| Document-level (all 10 fields) | 73.7% |
| Field-level, printed | 99.1% |
| Field-level, handwritten (4% of volume) | 61.2% |
| Document-level, handwritten | 8.9% |

Now the SLA conversation is possible: printed documents can carry a 99% field SLA; handwritten needs human
review. Note that the aggregate **hides** a segment that fails 91% of the time.

### E4.2 Choosing sample size before claiming a win

Variant A: 82/100 document-level correct. Variant B: 87/100. Is B better?

Standard error ≈ √(p(1-p)/n) ≈ √(0.85×0.15/100) ≈ 3.6 points; the difference of 5 points is ~1.4 SE — suggestive,
not decisive. Correct action: run the paired bootstrap on the same 100 items, or extend to 300 items, *then*
decide. Declaring victory on 5 points at n=100 is how a regression ships with a celebration.

### E4.3 Calibrating an LLM judge

Run the judge and a human on 60 items. Agreement 78%, and the judge is systematically 1 point more generous on
verbosity. Fixes: anchor the rubric with examples at each score, cap length in the rubric, and report the
judge's agreement next to any judged result. An uncalibrated judge is a vibe with a JSON schema.

### E4.4 Cost per resolved ticket

| | Model | Calls/ticket | Retry rate | Cost/call | Human escalate |
|---|---|---|---|---|---|
| A | Opus | 1.2 | 2% | $0.028 | 8% |
| B | Sonnet + Haiku router | 2.1 | 6% | $0.006 | 11% |

Per call B is 4.7× cheaper. Per **resolved** ticket: A ≈ $0.033 + 0.08×$4.50 human ≈ $0.39; B ≈ $0.013 + 0.11×$4.50
≈ $0.51. A wins on unit economics because the escalation rate dominates. **This is the calculation the exam
wants you to be willing to do** — cheap tokens are not cheap outcomes.

### E4.5 Diagnosing "it got worse after we upgraded the model"

1. Re-run the pinned eval on the old and new model — is it actually worse, or only worse on the complaints you
   heard?
2. Compare per segment.
3. Check whether the prompt relied on behaviour that changed (formatting, tool-call style, verbosity).
4. Check retrieval logs for that period (data change?).
5. Only then: adjust prompt, pin the old version, or fix the segment.

### E4.6 What "eval in CI" looks like

```
on pull_request:
  run eval (150 items, 4 segments)
  fail if: doc_accuracy < 0.90
        or any segment drops > 0.03 vs main
        or groundedness < 0.95
        or p95 latency > 2.5s
        or cost/success > $0.05
  post a table of per-segment deltas to the PR
```

Boring, visible, and it prevents the "who changed the prompt?" archaeology.

---

## 10. Traps

1. Tuning on the test set, then reporting test-set numbers.
2. A single aggregate accuracy with no stratification.
3. Judging on 20–40 items and calling a 2-point delta a win.
4. Optimising cost per call instead of per successful task.
5. Using an uncalibrated LLM judge as ground truth.
6. Skipping retrieval evaluation and only grading final answers.
7. "Switch to the biggest model" before checking whether evidence was retrieved.
8. No failure gallery, so the same bug returns quarterly.
9. Model version not pinned — a silent provider update becomes an unexplained regression.
10. Measuring only what is easy to measure (latency) and declaring quality unmeasurable.

---

## 11. Practice questions

**Q1.** An invoice system reports 96.4% field-level accuracy across 10 fields. The sponsor expects "over 95%
accuracy". What should you tell them?

- A. The system meets the requirement; field accuracy is above 95%
- B. Document-level accuracy is roughly 69% (0.964^10), and it varies by document type — agree which metric the
  requirement means
- C. Accuracy cannot be measured for generative systems
- D. Report 96.4% but add a caveat in the appendix

**Answer: B.** The sponsor's number is meaningless until the unit is fixed, and the honest translation of 96.4%
per field is a document that is fully correct about 69% of the time (worse with correlated errors). Naming the
metric, the unit and the segmentation is the stakeholder work this exam rewards. A and D are technically true and
practically misleading.

---

**Q2.** A prompt change improves overall accuracy from 88% to 91% on your 120-item set, but the support-tickets
segment (n=18) drops from 84% to 76%. What is the correct action?

- A. Ship it: overall accuracy improved by 3 points
- B. Investigate the ticket segment first; small n means the drop may be noise, but a plausible regression in one
  segment should not ship unexamined
- C. Revert immediately and stop iterating
- D. Remove the ticket segment from the eval set and re-run

**Answer: B.** Both truths matter: n=18 makes the drop uncertain, and a systematic segment failure is exactly
what aggregates hide. Investigate (read the failures, extend the sample), then decide. A ignores a possible
regression. C over-reacts to noise. D is corrupting the eval, which is disqualifying.

---

**Q3.** RAG answers are wrong 15% of the time. Logs show the correct chunk appears in the context for 12 of
those 15 cases. Where is the defect?

- A. Retrieval: the index is missing content
- B. Generation/assembly: the evidence is present but not used correctly — check ordering, dilution and grounding
  instructions
- C. Embedding model is too small
- D. The model tier is too low

**Answer: B.** The evidence was retrieved, so the retrieval stage did its job for those cases. The remaining
question is why it was ignored: too much noise, question placed before the documents, no "answer only from
context" rule, or a conflicting chunk. For the 3 miss cases, retrieval is the issue — which is why you evaluate
the stages separately. A, C and D all assume a capability fix for an assembly defect.

---

**Q4.** You need to decide whether a cheaper model can replace the current one for a 40k/month extraction task.
What is the minimum defensible test?

- A. Try 20 examples and eyeball the output
- B. Run both models on a held-out, segmented eval set of ≥ 100 documents; compare field- and document-level
  accuracy with confidence intervals, plus p95 latency and cost per successful extraction
- C. Compare published benchmark scores for both models
- D. Ask each model to rate its own confidence and pick the higher one

**Answer: B.** Quality, tail latency and unit cost are the three decision axes, and the set must be held out and
segmented to be representative. A is anecdote. C measures a different task than yours. D trusts uncalibrated
self-assessment — the same error as gating on self-reported confidence.

---

**Q5.** Which single practice best prevents repeat production failures?

- A. Increasing the eval set size to 1,000 random examples
- B. Turning every production failure into a versioned eval case with a rationale, and gating CI on it
- C. Weekly manual spot checks by the team
- D. Logging every prompt and response

**Answer: B.** A failure gallery converts incidents into regression tests — targeted, cheap, and it grows exactly
where your system is weak. A adds volume but not coverage of the failures you actually have. C is unfocused and
unrepeatable. D is necessary for diagnosis but prevents nothing by itself.

---

**Q6.** p95 latency is 4.2 s against a 3 s SLA; p50 is 900 ms. Which action addresses the actual problem?

- A. Move the whole workload to a faster model tier
- B. Profile per-stage latency and fix the tail: parallelise independent retrieval calls, cap agent iterations,
  shorten outputs, cache the prefix
- C. Reduce the eval set so fewer test calls run
- D. Report p50 to the sponsor, since that is the typical experience

**Answer: B.** p50 fine and p95 bad means a long tail — retries, agent loops, large documents, cold caches. Fix the
tail specifically. A degrades quality everywhere to fix a minority of calls. C is unrelated. D is misreporting.

---

## 12. 60-second recall

- Metric must name the unit: field vs document, per call vs per successful task.
- 0.97^10 ≈ 0.74 — compounding field errors is the number that matters downstream.
- Stratify by segment; aggregates hide the failures that sink you.
- Held-out set, versioned with the prompt, hard negatives included, ≥30 per reported segment.
- Deterministic checks first; LLM judge only when calibrated against humans; swap positions for pairwise.
- CI on point estimates is not significant; bootstrap on the same items.
- Pre-register the decision rule and guardrails before the test.
- Diagnose in order: retrieved? in context? cited? correct? formatted? — model tier is last.
- Optimise in order: trim → cache → route → then tier. Report cost per success.
- Every production failure becomes an eval case.
