# 08 · Cheat sheet

Print this. Re-derive it from memory two days before the exam; whatever you cannot reproduce is your revision
list.

---

## Exam facts

| | |
|---|---|
| CCAR-P | 63 items · 120 min · 720/1000 · $175 · Pearson VUE · EN/JA |
| Format | Standalone items (no scenario bank), single + multiple response |
| Weights | D1 17 · D2 13 · D3 19 · D4 16 · D5 14 · D6 14 · D7 7 |
| No prerequisites | Foundations is not required; access via a Claude Partner Network org |

**Pace:** 63 items / 120 min ≈ 1.9 min each. Pass 1 (~75 min, ≤90 s/item), pass 2 (~35 min flagged + verify
selections), reserve 10 min. Never leave a blank.

---

## The seven domain one-liners

| Domain | The one thing |
|---|---|
| D1 Design | Workflow = code decides the path; agent = model does. Climb the ladder only as far as constraints force. |
| D2 Models/context | Pick the tier your eval passes; cache the stable prefix; treat context as a budget. |
| D3 Integration | Authorisation filters the candidate set; retrieved text is data, never instructions. |
| D4 Evaluation | Fix the unit (field vs document), stratify, interval, then decide. |
| D5 Governance | Hard requirement → deterministic control, never a prompt. |
| D6 Stakeholders | Bring evidence, renegotiate per segment, name the measurement and the human path. |
| D7 Productivity | Managed settings + managed marketplace; deny beats allow; hooks block. |

---

## Pattern ladder and when each is right

| Pattern | Use when | Failure mode |
|---|---|---|
| Single call | Task fits in one context | Context dilution |
| Augmented LLM (RAG/tools) | Answer exists in data | Retrieval miss |
| Prompt chaining + gates | Steps known and ordered | Latency linear in stages |
| Routing | Distinct input classes | Misclassification; wrong specialist |
| Parallel (section/vote) | Independent subtasks / need confidence | Cost; vote correlation |
| Orchestrator–workers | Subtasks depend on the input | Hand-off overhead; synthesis conflicts |
| Autonomous agent | Path unknowable, recoverable errors | Loops, cost, tail latency |
| Multi-agent | Separable contexts + distinct tool surfaces | Coordination cost, untestable |

**Multi-agent is justified only by:** separable context, different tool surfaces, parallel work, testable in
isolation.

---

## Reliability checklist (D1)

- Idempotency key per unit of work
- Selective retry naming the failure; bounded attempts
- Dead-letter queue + alert on DLQ rate
- Checkpoint/resume, never restart the batch
- `max_iterations` + token budget per task
- Per-item status, not one exception
- Persist intermediate outputs for audit

---

## Models and cost

| Tier | Use | Order of magnitude (in/out $/MTok) |
|---|---|---|
| Haiku | classify · extract · route · high volume | 0.10 / 0.50 |
| Sonnet | answer · draft · summarise (default) | 2 / 10 |
| Opus | multi-file code, long tool loops | 4 / 20 |
| Fable | hardest reasoning, long-horizon | 10 / 50 |

- Output ≈ 5× input price → cap output length.
- `0.97^10 ≈ 0.74` — field accuracy compounds down at document level.
- Cost per **successful task**, not per call.
- Routing up a tier is a *quality* lever; it often costs more than running the mid tier everywhere.

---

## Context engineering

Order: **role → rules → output contract → examples → retrieved evidence → question** (question last).

| Slice | Rule |
|---|---|
| Tools | Biggest silent win — drop unused ones; large catalogues want progressive discovery |
| Retrieved | Rerank, send 5–8, not 25 |
| History | Summarise old turns into state; keep last exchange verbatim |
| Output | Always reserve |
| Critical constraint | Repeat one line immediately before the question |

**Lost in the middle:** best recall at the start and end. Never bury a hard rule in a long dump.

---

## Prompt caching

```
system = [
  {"type": "text", "text": STABLE_RULES_AND_CORPUS, "cache_control": {"type": "ephemeral"}},
]
messages = [{"role": "user", "content": VOLATILE_QUESTION}]
```

- Prefix match: any earlier change invalidates everything after.
- **Tools are part of the prefix** — adding one tool = cache write.
- 5m default TTL; 1h costs ~2× to write; reads ~0.1×; writes ~1.25× (verify).
- Minimum cacheable length exists — short prompts can't cache.
- Caching loses on a single request (write premium, no read).
- Bursty traffic with gaps > TTL pays the write again.
- Caching reduces the price of a mistake; it does not fix a bad context.

---

## RAG

| Stage | Rule |
|---|---|
| Parse | Layout-aware; tables as records |
| Chunk | By structure (clause, ticket, row); 10–15% overlap; stable IDs |
| Enrich | tenant, ACL groups, version, date, section path |
| Retrieve | **ACL filter inside the query**, before top-k; hybrid dense + keyword; rerank |
| Assemble | Top 5–8 chunks, question last, source IDs preserved |
| Generate | Answer only from context; `INSUFFICIENT_CONTEXT` fallback |
| Verify | Citations must be a subset of retrieved IDs |

**Dense misses:** error codes, part numbers, clause IDs. **Keyword misses:** paraphrase. → hybrid + rerank.

**Diagnosis order:** retrieved? → in context? → cited? → correct? → format? → model tier last.

---

## Metrics that survive review

| Metric | Watch out |
|---|---|
| Field accuracy | Flatters; hides compounding |
| Document accuracy | What downstream sees |
| Task completion | Coarse |
| Groundedness | Rewards refusing |
| Escalation rate | Optimising alone encourages silent failure |
| p95 latency | p50 hides the tail |
| Cost/success | Includes retries and human time |

- ≥30 items per reported segment; 100–300 for iteration.
- Bootstrap the CI; paired comparisons on the same items.
- Pre-register the gate: accuracy floor, per-segment drop cap, groundedness floor, p95, unit cost.
- LLM judge: rubric with anchors, calibrated vs humans, positions swapped, blind.

---

## Governance

| Layer | Stops | Does not stop |
|---|---|---|
| Input validation | Size, rate, malformed | Well-formed malice |
| Injection screen | Known patterns | Novel/encoded payloads |
| Retrieval ACL | Unauthorised sources | Injection inside an authorised source |
| Structural separation | Naive injection | Sophisticated grooming |
| Tool gating | Exfiltration, irreversible acts | Misuse of allowed capability |
| Output validation | Schema, DLP, invented citations | Plausible wrong answers |
| Human gate | Surviving high-impact errors | Rubber-stamping |
| Monitoring + kill switch | Duration/blast radius | First occurrence |

**Hard requirement → queue, permission, identity or schema. Never a sentence in a prompt.**

**HITL health:** reviewer sees evidence · override rate measured · named owner · queue has capacity · approvals
audited.

**Erasure reaches:** source rows · chunks (needs `doc_id` mapping) · caches · logs (retention) · eval sets ·
backups.

**Regulation in one line each:** GDPR → basis, minimisation, rights, retention, transfers. HIPAA → BAA, minimum
necessary, audit control. FedRAMP → authorised service, boundary, continuous monitoring.

---

## Stakeholders

**Trade-off template:** decision · options · criteria · evidence (numbers) · residual risk · reversal cost ·
owner.

**SLA pattern:** evidence by segment → per-segment proposal → agreed measurement (unit, n, adjudicator) → accept
residual risk → path to a higher number.

**Lifecycle gates:** discovery → design → build → pilot → rollout → operate → iterate → retire, each with an
owner.

**Handoff proof:** someone else performs deploy, alert response and rollback from the runbook alone.

---

## Claude Code / team setup

Precedence: **managed > CLI > local project > shared project > user**. Managed cannot be overridden.

- Enforce policy: managed settings. Distribute capability: managed marketplace. Two separate concerns.
- Permissions: **deny > allow > ask**; default ask; deny `.env*`, `secrets/*`, `*.pem`, `*.key`, `id_rsa*`,
  `*credentials*`.
- Hooks **block**, don't warn; fail closed.
- `CLAUDE.md`: commands, architecture, rules, links. **Assume it is public.**
- Delivery loop: explore → plan (approved) → implement (branch) → verify (tests) → document.
- Measure cycle time + revert rate, not suggestion counts.

---

## Phrasebook: what exam writers are signalling

| Phrase | Means |
|---|---|
| "cannot be overridden" | Server/managed-side control |
| "must be auditable" | Discrete steps + persisted intermediates |
| "no X reaches Y before review" | Gate in the workflow |
| "categories rarely change" | Constrained output + deterministic routing |
| "most errors come from Z" | Segment the metric; don't upgrade the model |
| "minimise cost and latency" | Trim context → cache → route → then tier |
| "regulated / PHI / personal data" | BAA/DPA, minimisation, retention, regional processing |
| "third-party tools across teams" | MCP with server-owned auth |
| "the model reports confidence" | Do not use as a gate; not calibrated |
| "recommended settings in a repo" | Not enforcement |

---

## Ten sentences worth memorising

1. Enforce hard requirements in code, identity or a queue — not in a prompt.
2. A workflow is chosen by code; an agent chooses its own path.
3. Autonomy is for unpredictable step counts, not for fixed rules.
4. Measure before changing the model; segment before believing the aggregate.
5. Authorisation filters the candidate set, not the output.
6. Retrieved content is data, never instructions.
7. Field accuracy compounds down; report the unit the business experiences.
8. Cache the stable prefix; stable before volatile.
9. Renegotiate an SLA with evidence and a human path for the weak segment.
10. Prompts and models are production configuration: versioned, eval-gated, rollback in one flag.
