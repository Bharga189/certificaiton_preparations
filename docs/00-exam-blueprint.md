# 00 · Blueprint, scoring, tactics

Everything in this file is about the *exam as an instrument*, not about Claude. Read it once now, once again
two days before you sit.

---

## 1. Position in the certification family

Anthropic runs four role-based exams. They are independent: no exam is a prerequisite for another, and a
Foundations certificate does not "upgrade" into Professional.

| | Associate CCAO-F | Developer CCDV-F | Architect CCA-F | **Architect Professional CCAR-P** |
|---|---|---|---|---|
| Audience | Non-coding / business | Hands-on builders | Solution designers | Owners of production systems |
| Items | ~53 | ~53 | 60 | **63** |
| Format | MCQ | MCQ | 4 scenarios from a bank of 6 | 7 domains, standalone items |
| Time | 120 min | 120 min | 120 min | **120 min** |
| Pass | 720/1000 | 720/1000 | 720/1000 | **720/1000** |
| Fee | $99 | $125 | $125 | **$175** |

Two consequences worth internalising:

- **Professional is not "Foundations with more questions."** The overlap is model choice, prompting, tool and
  context design. What is new is *integration depth, evaluation rigour, governance, stakeholder work and
  lifecycle ownership* — 35%+ of the paper that Foundations never touches.
- **Scenario structure is gone.** Foundations hands you a scenario and asks questions inside it; Professional
  items are self-contained. Each item must give you enough context on its own, which means the **constraints
  stated in the stem are the answer key**. Read the stem twice; the discriminator is usually one clause
  ("regulated", "cannot be overridden", "40,000 per month", "three weeks before go-live").

---

## 2. Domain map with objectives

Objective wording below is a faithful paraphrase of the published v1.0 guide. Use it as a checklist: tick an
objective only if you have *done* it, not if you have *read* it.

### Domain 1 — Solution Design & Architecture · 17%

| # | Objective | Self-check question |
|---|---|---|
| 1.1 | Translate a business problem into a Claude solution with measurable outcomes | Can you name the metric the sponsor will judge you on? |
| 1.2 | Design the end-to-end flow: inputs → processing → outputs → feedback | Where does a human or a test catch a bad output? |
| 1.3 | Choose between workflow, agent, augmented LLM, multi-agent | Can you justify *not* using an agent? |
| 1.4 | Decompose the problem and choose an orchestration/coordination strategy | Which steps have data dependencies, which are independent? |
| 1.5 | Handle failure, retries, idempotency, partial success | What happens when step 3 of 5 fails? |
| 1.6 | Balance accuracy, latency, cost, maintainability | Which of the four did you trade, and why? |

### Domain 2 — Claude Models, Prompting & Context Engineering · 13%

| # | Objective | Self-check question |
|---|---|---|
| 2.1 | Select a model on reasoning, quality, latency, context, cost | What did your eval show at the cheaper tier? |
| 2.2 | Design system prompts, templates, few-shot examples, guardrails | Is each instruction testable? |
| 2.3 | Apply zero-shot / few-shot / structured reasoning appropriately | Does the task need reasoning, or just formatting? |
| 2.4 | Manage the context window: prioritise, trim, order | What do you drop first when over budget? |
| 2.5 | Use prompt caching, modular prompts, Skills for reuse | Which block is the cache breakpoint, and why there? |
| 2.6 | Control behaviour: refusal, format, tone, tool-use discipline | How do you *verify* the behaviour, not just request it? |

### Domain 3 — Integration · 19%

| # | Objective | Self-check question |
|---|---|---|
| 3.1 | Design tool surfaces without capability bloat | Which tool could you delete and lose nothing? |
| 3.2 | Close authentication/authorisation gaps; apply least privilege | Can the model reach a record the *user* cannot? |
| 3.3 | Design RAG: ingestion, chunking, indexing, retrieval, assembly | Why that chunk size for *this* document type? |
| 3.4 | Choose MCP vs direct API vs CLI vs agent-to-agent | Who owns auth in each option? |
| 3.5 | Plan observability and monitoring at scale | What alert fires when quality drops, not just uptime? |
| 3.6 | Decide progressive discovery vs monolithic context | How many tools before the model starts choosing wrong? |

### Domain 4 — Evaluation, Testing & Optimization · 16%

| # | Objective | Self-check question |
|---|---|---|
| 4.1 | Define metrics: accuracy, task completion, latency, cost, safety | Is your metric field-level or document-level? |
| 4.2 | Build representative eval sets; mix automated + human grading | How did you stop tuning on the test set? |
| 4.3 | Run comparative/A-B tests with a decision rule | What difference would you call significant? |
| 4.4 | Diagnose hallucinations, prompt failures, model mismatch | Retrieval miss, or generation error? |
| 4.5 | Optimise tokens, latency, cost without losing quality | What did caching buy you, measured? |
| 4.6 | Regression-test prompts and models before rollout | What breaks when the model version changes? |

### Domain 5 — Governance, Safety & Risk Management · 14%

| # | Objective | Self-check question |
|---|---|---|
| 5.1 | Implement guardrails and identify failure modes / misuse | Which layer catches prompt injection? |
| 5.2 | Apply human-in-the-loop for sensitive or high-impact output | Who signs, and what do they see? |
| 5.3 | Meet regulatory obligations (GDPR, HIPAA, FedRAMP, sector rules) | Where does PHI/PII live, and how long? |
| 5.4 | Address bias, fairness, transparency, responsible data use | How would you detect disparate quality? |
| 5.5 | Define auditability, logging, retention, kill switch | Can you turn it off in one action? |

### Domain 6 — Stakeholder Communication & Lifecycle Management · 14%

| # | Objective | Self-check question |
|---|---|---|
| 6.1 | Run structured discovery: needs, constraints, outcomes, risks, SLAs | What did you write down that the sponsor signed? |
| 6.2 | Communicate architecture and trade-offs to technical and non-technical audiences | Can you explain caching in one sentence to a CFO? |
| 6.3 | Document decisions, assumptions, and implementation guidance | Where is the ADR? |
| 6.4 | Manage expectations through delivery, handoff, monitoring, iteration | Who owns it on day 2 after go-live? |

### Domain 7 — Developer Productivity & Operational Enablement · 7%

| # | Objective | Self-check question |
|---|---|---|
| 7.1 | Configure shared Claude tooling (Claude Code, settings, marketplaces) securely | Which layer wins when settings conflict? |
| 7.2 | Apply AI assistance to analysis, implementation, testing, docs | What do you *not* let it touch? |
| 7.3 | Use Claude-assisted tooling for operational debugging | How do you keep production data out of the transcript? |

---

## 3. Scoring, and what 720 means

- Reported on a **100–1000 scale**; you need **720**. It is *scaled*, not a raw percentage, so "I need 72%"
  is a rough planning heuristic, not a formula. Assume you need roughly **46 of 63** and aim higher.
- The score report lists **per-domain percentages**. They do not decide the pass — the total does — but they
  are the best retake plan you will ever get. Note which domain is lowest and re-drill that guide.
- **There is no penalty for guessing.** Never leave a blank; a blank is a guaranteed loss, an elimination-based
  guess is ~30–50%.
- Multiple-response items state the number to select. Selecting *three* when it says *two* is simply wrong,
  even if all three are true statements. This is the most common avoidable loss on the paper.

---

## 4. Question tactics that actually move the score

### Tactic 1 — Classify the stem before reading options

Spend 10 seconds labelling the item: *design / security / diagnosis / stakeholder / lifecycle*. Then recall the
reflex for that class:

| Class | Default correct shape |
|---|---|
| Design | Simplest pattern that meets the constraints; add autonomy only when steps can't be enumerated |
| Security | Enforce in identity + code; least privilege; scope data to the requesting user |
| Diagnosis | Measure, segment, isolate cause; change one variable |
| Stakeholder | Evidence + revised expectation + human path for the risky segment |
| Lifecycle | Named owner, gate, rollback, logging, agreed acceptance criteria |

### Tactic 2 — Hunt the constraint clause

The stem always contains the discriminator. Underline it mentally:

- "**cannot be overridden**" → managed/server-side settings, not a repo file.
- "**no reply reaches a patient before review**" → hard gate in workflow, not a prompt instruction.
- "**40,000 per month, categories rarely change**" → single constrained call + deterministic routing, not an agent.
- "**most errors come from handwritten documents**" → segment the metric; don't buy a bigger model.
- "**must be auditable**" → discrete steps with persisted intermediate outputs.

### Tactic 3 — Eliminate on principle, not on plausibility

Wrong options are written to be *plausible*. They fail for one of a small set of reasons. Learn to name them:

| Failure reason | Tell-tale wording |
|---|---|
| Enforcement in the prompt | "instruct the model to…", "ask Claude to always…" |
| Unjustified complexity | multi-agent, autonomous planning, fine-tuning for a fixed task |
| Retrospective control | "audit later", "sample weekly", "review monthly" |
| Unmeasured optimism | "switch to the largest model", "tune the prompt until it reaches 99.9%" |
| Trusting self-reported confidence | "when the model reports confidence > 0.9" |
| Client-supplied identity | "pass the user_id from the browser" |
| Optimising the wrong stage | prompt-tuning when retrieval is broken |

### Tactic 4 — Prefer the option that produces evidence

When two options are both defensible, the one that **measures, logs, or gates** usually wins over the one that
**assumes**. Professional-level judgement is evidence-first.

### Tactic 5 — Time discipline

63 items / 120 min. Do two passes:

1. **Pass 1 (~75 min):** answer everything you can in under 90 seconds. Flag anything longer. Never let a
   scenario-heavy item eat four minutes.
2. **Pass 2 (~35 min):** flagged items, then multiple-response verification (count your selections!), then a
   sweep for blanks.
3. **Reserve 10 min** as buffer. Rushing the last ten items is where passes are lost.

---

## 5. The six traps that recur

1. **"Put the rule in the system prompt."** Promotion to a hard requirement means code, identity, or a queue.
2. **"Just use the biggest model."** A capability change is not a diagnosis. Segment first.
3. **"Add an agent."** Autonomy is for unpredictable step counts; fixed rules want a workflow.
4. **"Switch embedding model / re-index everything."** First check chunking, query formulation, and filtering.
5. **"Fine-tune."** Fine-tuning teaches *form and style*, not fresh facts; and it needs data plus a maintenance
   plan. Retrieval answers "what does our policy say".
6. **"Let the model decide if it is confident."** Self-reported confidence is not calibrated; use measured
   thresholds and a review path.

---

## 6. Study plans

### 6-week plan (recommended if you are new to the governance side)

| Week | Focus | Deliverable |
|---|---|---|
| 1 | Blueprint + D1 + D2 | Written requirement + pattern comparison for one real problem |
| 2 | D3 (integration, RAG, ACL) | Working retrieval with per-user filtering and an injection test |
| 3 | D4 (evaluation) | 100-item eval set, stratified metrics, baseline numbers |
| 4 | D5 (governance) | Risk register, guardrail layers, HITL gate, kill switch |
| 5 | D6 (stakeholders) | Sponsor memo, SLA by segment, ADRs, handoff doc |
| 6 | D7 + mocks | Two timed mocks; re-drill two weakest domains |

### 10-day sprint (if you already own production systems)

| Day | Work |
|---|---|
| 1 | This file + cheat sheet. Self-diagnostic. |
| 2–3 | D1 + D2, run both examples, answer all questions |
| 4–5 | D3 (heaviest domain — do not compress it) |
| 6 | D4 |
| 7 | D5 |
| 8 | D6 + D7 |
| 9 | Mock A timed, review every explanation |
| 10 | Mock B timed, re-read cheat sheet, sleep |

### Daily drill (20 minutes, high yield)

Pick one domain. From memory, write: (a) the domain's decision table, (b) three traps, (c) one worked example
with numbers. Then check against the guide. Retrieval practice beats re-reading by a wide margin.

---

## 7. Self-diagnostic — rate yourself 0 / 1 / 2

0 = never done it · 1 = done it with help · 2 = can do it and defend it

| # | Statement | Score |
|---|---|---|
| 1 | I can justify choosing a fixed workflow over an agent using cost, latency and failure handling. | |
| 2 | I have implemented prompt chaining with a validation gate and selective retry. | |
| 3 | I can pick a model tier from measured eval data, not vibes. | |
| 4 | I have used prompt caching and can state the breakpoint placement rule and measured saving. | |
| 5 | I can explain why a long system prompt belongs at the front, and what invalidates a cache. | |
| 6 | I have built RAG with chunking tuned to document structure, and hybrid retrieval. | |
| 7 | I have tested that a user cannot retrieve a document they lack permission for. | |
| 8 | I can compare MCP, direct API, CLI and agent-to-agent on auth ownership and blast radius. | |
| 9 | I have a versioned eval set that is separate from my tuning examples. | |
| 10 | I can compute field-level vs document-level accuracy and explain the difference to a sponsor. | |
| 11 | I have diagnosed a hallucination to either retrieval miss or generation error. | |
| 12 | I can design a layered guardrail set and say which layer stops prompt injection. | |
| 13 | I have designed a human-in-the-loop gate with a named approver and an audit trail. | |
| 14 | I can state what GDPR/HIPAA/FedRAMP each demand of an LLM pipeline in one line each. | |
| 15 | I have written an ADR and a sponsor-facing memo with limits and acceptance criteria. | |
| 16 | I can negotiate an SLA down from an unachievable single number to a testable per-segment one. | |
| 17 | I know the Claude Code settings precedence order and how to enforce a policy developers can't override. | |
| 18 | I have a rollback plan and a kill switch for an AI feature. | |

**Scoring:** any 0 → study that domain's guide first. Total < 20 → use the 6-week plan. 20–30 → 10-day sprint.
> 30 → mocks, then book.

---

## 8. Resources

| Resource | Use |
|---|---|
| CCAR-P exam guide (Partner Academy) | The authoritative objective list. Grade yourself against it. |
| Certifications FAQ | Logistics, languages, retakes, access rules |
| Claude Platform Docs → Models overview & Pricing | Model tiers, IDs, context, prices (**verify**) |
| Claude Platform Docs → Prompt caching | Breakpoints, TTL, minimums, multipliers (**verify**) |
| Claude Platform Docs → Tool use, MCP connector | Tool schemas, `tool_choice`, strict mode, server tools |
| Anthropic Engineering → *Building effective agents* | The workflow/agent vocabulary the exam uses |
| Claude Code docs → settings, server-managed settings, marketplaces | Domain 7 |
| This pack's mocks | Timing and weak-domain mapping |

**Do not** rely on dumps. Beyond the ethics, they are stale within weeks (model names and prices change) and
they teach recognition of a specific sentence rather than the judgement the items reward.
