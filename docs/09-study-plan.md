# 09 · Study plan, drills, and tracking

Use this with `docs/00-exam-blueprint.md` §7 (self-diagnostic). The plan assumes ~1.5 focused hours per weekday
and one longer session at the weekend.

---

## A. 6-week plan (default if governance/stakeholder work is new to you)

### Week 1 — Blueprint + D1 + D2

| Day | Work | Output |
|---|---|---|
| 1 | Read blueprint, score the 18-statement diagnostic | Study queue ranked |
| 2 | D1 read; run `d1_patterns.py` | Explain the gate example aloud in 60 s |
| 3 | D1 questions, answers covered | ≥5/6 correct |
| 4 | D2 read; run `d2_context_cost.py` | State the break-even for caching |
| 5 | D2 questions | ≥5/6 |
| 6 | Apply to your own project: one requirement, two candidate patterns, written comparison | 1-page decision note |
| 7 | Rest / re-read D1+D2 recall sections | — |

### Week 2 — D3 (the 19% domain)

| Day | Work | Output |
|---|---|---|
| 1 | D3 §1–2 (tool surface, identity) | List 3 capability leaks in a system you know |
| 2 | D3 §3 (RAG) | Chunking decision for 3 document types |
| 3 | Run `d3_rag_acl.py`; break the ACL test deliberately and fix it | Working ACL filter |
| 4 | D3 §4–5 (protocols, observability) | One-page monitoring plan |
| 5 | D3 questions | ≥5/6 |
| 6 | Build: retrieval over your own docs with per-user filtering | Demo + injection test |
| 7 | Write down what could leak and how you know it cannot | Threat note |

### Week 3 — D4

| Day | Work | Output |
|---|---|---|
| 1 | D4 §1–2 (metrics, eval sets) | Metric definition with unit + segments |
| 2 | D4 §3–4 (grading, statistics) | Judge calibration plan |
| 3 | Run `d4_eval.py` | Explain why 0.97^10 ≈ 0.74 |
| 4 | D4 §6–8 (diagnosis, optimisation, regression) | Triage tree for your system |
| 5 | D4 questions | ≥5/6 |
| 6 | Build: 100-item eval set, stratified, versioned, CI gate | Eval report with CIs |
| 7 | Add the failure gallery (5 real failures → cases) | 5 new eval items |

### Week 4 — D5

| Day | Work | Output |
|---|---|---|
| 1 | D5 §1–2 (risk register, guardrails) | Risk register with owners |
| 2 | D5 §3 (HITL) | Gate design with evidence shown + override metric |
| 3 | Run `d5_guardrails.py` | Fail-closed and kill-switch behaviour |
| 4 | D5 §4 (regulation) | Data-flow one-pager with processors |
| 5 | D5 questions | ≥5/6 |
| 6 | Build: erasure runbook across index/cache/logs/evals | Tested deletion |
| 7 | Red-team your own system: 10 injection payloads | Results table |

### Week 5 — D6 + D7

| Day | Work | Output |
|---|---|---|
| 1 | D6 §1–2 (discovery, expectation management) | Discovery question set |
| 2 | Run `d6_sla.py` | Proposed SLA table for a real system |
| 3 | D6 §3–5 (communication, docs, lifecycle) | One ADR + one runbook |
| 4 | D6 questions | ≥5/6 |
| 5 | D7 read + `d7_team_setup.py` | Settings policy + deny list |
| 6 | D7 questions | ≥5/6 |
| 7 | Write the sponsor memo (limits, acceptance, risks, ask) | 1 page |

### Week 6 — Mocks and consolidation

| Day | Work |
|---|---|
| 1 | Mock A, study mode: untimed, read every explanation |
| 2 | Re-drill weakest domain's guide + questions |
| 3 | Re-drill second weakest |
| 4 | Mock B, timed 120 min, no notes |
| 5 | Review every wrong answer; write the *principle* you missed |
| 6 | Cheat sheet from memory; fix gaps; logistics check |
| 7 | Light recall only. Sleep. |

---

## B. 10-day sprint (you already own production systems)

| Day | Focus | Deliverable |
|---|---|---|
| 1 | Blueprint + diagnostic + cheat sheet | Ranked weak list |
| 2 | D1 + D2 guides, both examples | 6/6 on each question set |
| 3 | D3 §1–3 | ACL-filtered retrieval running |
| 4 | D3 §4–5 + questions | Monitoring plan |
| 5 | D4 + `d4_eval.py` | 50-item eval set with CI |
| 6 | D5 + `d5_guardrails.py` | Risk register + gate |
| 7 | D6 + `d6_sla.py` | Sponsor memo |
| 8 | D7 + Mock A | Weak-domain map |
| 9 | Mock B timed | ≥46/63 |
| 10 | Targeted revision of two weakest domains | Cheat sheet from memory |

---

## C. Daily drill (20 minutes, highest yield)

**Retrieval practice, not re-reading.** From memory, write:

1. The domain's **decision table** (3–5 rows).
2. **Three traps** and the phrase that signals each.
3. **One worked example with numbers** (cache saving, doc accuracy, SLA maths, review FTE).

Then check against the guide and mark what you missed. Repeat tomorrow for the missed items only.

### Spaced schedule

| When | What |
|---|---|
| Same day | Drill the domain you just read |
| Day +3 | Same drill, from memory |
| Day +7 | Cheat-sheet section only |
| Day +14 | One mock question set |

---

## D. The one project that covers D3–D5 at once

Anthropic's own advice, and the most efficient use of your time. Build:

1. **Corpus** of 20–50 documents you are allowed to use.
2. **Ingestion** with structure-aware chunking + metadata (tenant, ACL group, version, date).
3. **Retrieval** with per-user filtering *inside* the query, hybrid scoring, rerank.
4. **Generation** with an output contract and `INSUFFICIENT_CONTEXT`.
5. **Citations** validated against retrieved IDs.
6. **Eval set** of 50–100 items, stratified, held out, versioned.
7. **Logging** of request, version, tokens, latency, chunk IDs, outcome — redacted.
8. **Guardrails**: input screen, tool gating, output DLP, kill switch.
9. **One HITL gate** with an approval record and override metric.
10. **Runbook** + ADR.

You can then answer, with evidence: "what did you measure?", "how do you know a user can't see another tenant's
document?", "what happens when it's wrong?", "what does it cost per successful task?", "who turns it off?"

---

## E. Mock scoring sheet

| | Mock A | Mock B |
|---|---|---|
| Score /63 | | |
| % | | |
| D1 /11 | | |
| D2 /8 | | |
| D3 /12 | | |
| D4 /10 | | |
| D5 /9 | | |
| D6 /9 | | |
| D7 /4 | | |
| Ran out of time? | | |
| Multiple-response errors | | |
| Topics to re-drill | | |

Target ≥46/63 (≈73%) with every domain ≥60%. A domain below 50% is a retake risk regardless of the total.

---

## F. Two days before

1. Re-read `docs/08-cheatsheet.md` and reproduce the two decision tables (pattern ladder, guardrail layers).
2. Re-read your own wrong-answer notes from both mocks.
3. Confirm logistics: Partner org access, Pearson VUE slot, ID, quiet room, no browser translation.
4. Stop studying by 18:00 the day before. Sleep is worth more than one more mock.
