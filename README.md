# Claude Certified Architect — Professional (CCAR-P) Study Pack

A complete, example-driven preparation pack for Anthropic's **Claude Certified Architect – Professional**
exam. Every concept is taught three ways: a short mental model, a worked example, and an exam-style question
whose wrong options are explained — because on this exam, knowing *why the tempting answer is wrong* is the
actual skill being measured.

> **Independence notice.** This is an independent study resource. It is not affiliated with, authorised by, or
> endorsed by Anthropic. Exam facts below reflect the public CCAR-P exam guide (v1.0, July 2026) and the
> certification FAQ as read in **November 2026**. Anthropic updates guides and model line-ups; always confirm
> against the official exam guide on Anthropic Partner Academy before you book.

---

## 1. The exam in one table

| Attribute | CCAR-P |
|---|---|
| Full name | Claude Certified Architect – Professional |
| Items | **63** (single-answer and multiple-response; each item states how many to pick) |
| Time | **120 minutes** (~1.9 min/item) |
| Pass mark | **720 / 1000** scaled |
| Fee | **$175** per attempt |
| Delivery | Pearson VUE — online proctored or test centre |
| Languages | English, Japanese (browser translation is **not** allowed) |
| Prerequisites | None formally. Recommended: 3+ yrs systems architecture/platform engineering, 6+ months Claude (or comparable LLM) in production, one end-to-end delivery |
| Structure | 7 weighted domains; no scenario bank (unlike Foundations) |
| Score report | Scaled total **plus** per-domain percentages, which do not decide the pass |

**Access:** registration runs through a **Claude Partner Network** organisation. If your employer is not one,
that is a logistics problem to solve *before* study, not after.

### Domain weights — memorise this shape

| # | Domain | Weight |
|---|---|---|
| 1 | Solution Design & Architecture | **17%** |
| 2 | Claude Models, Prompting & Context Engineering | **13%** |
| 3 | Integration | **19%** |
| 4 | Evaluation, Testing & Optimization | **16%** |
| 5 | Governance, Safety & Risk Management | **14%** |
| 6 | Stakeholder Communication & Lifecycle Management | **14%** |
| 7 | Developer Productivity & Operational Enablement | **7%** |

Three facts follow from that table, and they should drive your study allocation:

1. **Integration is the heaviest domain (19%)** and it is where production systems actually break: retrieval,
   access control, tool exposure, protocol choice, monitoring.
2. **Domains 5 + 6 = 28%** and are *not on the Foundations blueprint at all*. Architects who only study
   architecture routinely lose here.
3. **Domain 7 is only 7%.** Do not spend a weekend on Claude Code settings; spend an afternoon.

---

## 2. What this exam actually tests

Foundations asks *"can you design a working Claude system?"* Professional asks *"can you own one?"* — build it,
ship it, defend it to a security review and a steering committee, and keep it safe over its life.

The exam is therefore less about API trivia and more about **judgement under constraints**. Nearly every item is
one of five archetypes:

| Archetype | Looks like | What it rewards |
|---|---|---|
| **Design choice** | "Which architecture/pattern fits?" | Picking the *simplest* pattern that meets stated requirements |
| **Security review** | "Which two actions should you take?" | Least privilege, enforcement in code/identity, not in prompts |
| **Diagnosis** | "Quality dropped after X. What first?" | Measure before changing; find the *cause*, not a workaround |
| **Stakeholder** | "The sponsor asks for an SLA you cannot meet." | Evidence + renegotiation + a human path for the weak segment |
| **Lifecycle** | "Three weeks before go-live…" | Gates, rollback, ownership, handoff, iteration |

Two reflexes win a large share of items:

- **Enforce hard requirements outside the model.** If Legal says "no reply reaches a patient unreviewed", that
  is a queue in the workflow, not a sentence in the system prompt.
- **Measure before you change the model/prompt.** "Switch to the biggest model" is almost always the wrong
  first move; "build a stratified eval set and look at failures by segment" usually is the right one.

---

## 3. File map

### Foundations of the pack

| File | What it is |
|---|---|
| [docs/00-exam-blueprint.md](docs/00-exam-blueprint.md) | Full blueprint, every objective, scoring maths, question tactics, study plans, self-diagnostic |
| [docs/08-cheatsheet.md](docs/08-cheatsheet.md) | One-page recall: numbers, patterns, decision tables, phrases exam writers use |
| [docs/09-study-plan.md](docs/09-study-plan.md) | 6-week plan, 10-day sprint, daily drills, evidence log |

### Domain guides (read in blueprint order)

| File | Domain | Weight |
|---|---|---|
| [docs/01-solution-design.md](docs/01-solution-design.md) | Design & architecture: workflow vs agent vs augmented LLM, orchestration | 17% |
| [docs/02-models-prompting-context.md](docs/02-models-prompting-context.md) | Model choice, prompting, context engineering, caching, Skills | 13% |
| [docs/03-integration.md](docs/03-integration.md) | RAG, ACLs, MCP vs API vs CLI vs A2A, tool surface, monitoring | 19% |
| [docs/04-evaluation.md](docs/04-evaluation.md) | Metrics, eval sets, A/B, hallucination diagnosis, cost/latency | 16% |
| [docs/05-governance.md](docs/05-governance.md) | Guardrails, failure modes, HITL, GDPR/HIPAA/FedRAMP, bias | 14% |
| [docs/06-stakeholders-lifecycle.md](docs/06-stakeholders-lifecycle.md) | Discovery, trade-offs, SLAs, documentation, handoff | 14% |
| [docs/07-developer-productivity.md](docs/07-developer-productivity.md) | Claude Code for teams, AI-assisted delivery, ops debugging | 7% |

Each domain guide follows the same shape: **objectives → mental model → decision tables → worked examples →
traps → practice questions with full rationale → 60-second recall**.

### Practice

| File | What it is |
|---|---|
| [docs/10-mock-exam-a.md](docs/10-mock-exam-a.md) | Mock items 1–31, weighted like the real exam, answers + explanations |
| [docs/11-mock-exam-b.md](docs/11-mock-exam-b.md) | Mock items 32–63, answers + explanations |

Both mocks are written from the published blueprint. They are **not** real exam items and their score is a map
of weak domains, not a forecast.

### Runnable code (`examples/`)

Everything runs offline with **no API key** — a small fake client mirrors the real SDK response shapes, so you
can see the orchestration and measurement logic execute. Each file's docstring shows the real `client.messages
.create(...)` call it stands in for.

```bash
python3 examples/d1_patterns.py      # workflow vs agent, gates, routing, orchestrator, evaluator loop
python3 examples/d2_context_cost.py  # prompt caching + model routing economics, measured
python3 examples/d3_rag_acl.py       # chunking, hybrid retrieval, per-user ACL filtering, MCP surface
python3 examples/d4_eval.py          # eval harness, stratified metrics, bootstrap CI, LLM-as-judge
python3 examples/d5_guardrails.py    # layered guardrails + human-in-the-loop gate + audit log
python3 examples/d6_sla.py           # SLA you can actually sign: per-segment accuracy + fallback maths
python3 examples/d7_team_setup.py    # managed settings precedence + team rollout checklist
python3 examples/run_all.py          # run every example, assert it behaved
```

---

## 4. How to study this pack (the short version)

1. **Diagnose first.** Read `docs/00-exam-blueprint.md` §7 and rate yourself 0–2 on each statement. Anything
   scoring 0 is your study queue; ignore domain order until that is done.
2. **Read a domain guide, then run its example, then answer its questions with the answers covered.** The
   questions are where learning happens; reading explanations passively feels productive and isn't.
3. **Build one small system end to end** (the guide's own advice): retrieval + ACLs + eval set + logs +
   a human approval gate. That single artefact covers Domains 3, 4 and 5 at once and gives you real answers
   to "what did you measure?" questions.
4. **Rehearse the stakeholder conversation out loud.** Domain 6 rewards an architect who can justify a
   trade-off to a sponsor who does not read code.
5. **Two timed mocks, 63 items in 120 minutes.** First in study mode (read every explanation), then against
   the clock. Re-drill the two domains where you lost most.

### Progress tracker

- [ ] Blueprint read; self-diagnostic scored
- [ ] D1 read + `d1_patterns.py` run + questions done
- [ ] D2 read + `d2_context_cost.py` run + questions done
- [ ] D3 read + `d3_rag_acl.py` run + questions done
- [ ] D4 read + `d4_eval.py` run + questions done
- [ ] D5 read + `d5_guardrails.py` run + questions done
- [ ] D6 read + `d6_sla.py` run + questions done
- [ ] D7 read + `d7_team_setup.py` run + checklist done
- [ ] Mock A timed (score: ____ / 63, weakest domain: ______)
- [ ] Mock B timed (score: ____ / 63, weakest domain: ______)
- [ ] Cheat sheet recalled from memory in one pass
- [ ] Logistics: Partner org access, Pearson VUE slot booked

---

## 5. Sources used

- Anthropic Partner Academy — CCAR-P exam guide v1.0 (July 2026) and certifications FAQ
- Claude Platform Docs — models overview, pricing, prompt caching, tool use, MCP connector, Agent SDK
- Anthropic Engineering — *Building effective agents* (workflows vs agents, orchestration patterns)
- Claude Code docs — settings hierarchy, server-managed settings, plugin marketplaces

Where the pack states a number that Anthropic revises often (model prices, cache multipliers, token minimums),
it is marked **verify** so you re-check it rather than memorise a stale figure.
