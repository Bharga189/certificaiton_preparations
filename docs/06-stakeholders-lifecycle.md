# 06 · Stakeholder Communication & Lifecycle Management — 14%

> **What this domain really tests:** can you make a probabilistic system *ownable* — requirements agreed,
> expectations calibrated, decisions documented, and operations handed over?

This is 14% of the paper and it is where strong engineers lose points, because the "correct" answer is often
*renegotiate the requirement* rather than *engineer harder*.

---

## 1. Discovery: the questions that prevent rework

Run discovery with every stakeholder group, not just the sponsor.

| Stakeholder | What they own | Questions to ask |
|---|---|---|
| **Sponsor / business owner** | Outcome, budget | What decision improves if this works? What number moves? What would make you cancel it? |
| **End users** | Adoption | What do you do today? Where does it slow you down? What would you not trust it with? |
| **Security** | Data flow, access | What data classes are involved? Who may see what? What is the threat model? |
| **Legal / compliance** | Lawfulness, retention | What is the lawful basis? What retention? Any BAA/DPA? Deletion path? |
| **Operations / support** | Running it | Who is on call? What is the degraded mode? What does an incident look like? |
| **Data owners** | Corpus quality | Who curates the source? How fresh is it? Who approves reindexing? |

### Discovery outputs (write these down, get them signed)

1. **Problem statement** in one paragraph, in the sponsor's words.
2. **Success metric(s)** with unit, segment, baseline, target, and measurement method.
3. **Hard constraints** — regulatory, latency, budget, data residency, approval gates.
4. **Non-goals** — what this explicitly will not do (prevents scope creep and over-trust).
5. **Risk list** with owners.
6. **Draft SLA** by segment, not one global number.
7. **Acceptance criteria** for the pilot, agreed *before* building.

If you cannot fill in the metric's *unit*, you do not have a requirement yet.

---

## 2. Expectation management: the conversation that saves the project

### The SLA pattern (learn this shape — it recurs)

**Stem:** sponsor demands 99.9% accuracy; your measured result is 96.4%, errors concentrated in one segment.

**Bad answers:** accept and hope; refuse any SLA; promise after a model upgrade.

**Correct shape:**

1. **Bring evidence, segmented.** "Printed documents: 99.1% field accuracy. Handwritten (4% of volume): 61%."
2. **Propose a testable alternative, per segment.** "99% field accuracy on printed; handwritten routed to human
   review with a 4-hour turnaround."
3. **Define the measurement.** "Field-level, sampled weekly, n=200, adjudicated by your team's QA lead."
4. **Name the residual risk and who accepts it.** Signed, dated.
5. **Offer the path to a higher number** with cost/time, rather than implying it is free.

This answers the actual question ("can I trust this?") instead of arguing about a decimal.

### Language that calibrates expectations

| Instead of | Say |
|---|---|
| "It's 96% accurate" | "96.4% of fields on printed invoices; 61% on handwritten, which we route to review" |
| "The AI understands your documents" | "It extracts these 8 fields from these 3 document types; it does not interpret contract intent" |
| "It's ready" | "It meets the agreed pilot criteria on the eval set; production monitoring starts at go-live" |
| "We'll fix it with a better model" | "We'll test whether the gap is retrieval or generation before changing the model" |

---

## 3. Communicating architecture to different rooms

| Audience | They care about | Give them | Do not give them |
|---|---|---|---|
| **Executive** | Cost, risk, time, decision | One page: outcome, unit economics, top 3 risks with mitigations, go/no-go ask |
| **Security** | Data flow, identity, blast radius | Diagram with trust boundaries, authz model, tool scopes, logging, kill switch |
| **Legal** | Lawfulness, retention, deletion | Data inventory, processor list with contracts, retention schedule, DSAR runbook |
| **Engineering** | How it works, how it fails | ADRs, sequence diagrams, prompt registry, failure modes, runbook |
| **End users** | What it does, when to trust it | Capability boundaries, how to correct it, escalation path |

### The trade-off template (use it in every design review)

```
Decision:            Prompt caching on the shared policy prefix
Options considered:  No cache / cache 5m TTL / cache 1h TTL
Criteria:            cost per request, p95 latency, staleness risk
Evidence:            $13.90 -> $3.13 per 500 requests; p95 -400ms; policy changes ~monthly
Decision:            5m TTL, cache invalidated on policy publish
Residual risk:       first request after a policy change is slower and pricier
Reversal cost:       one config flag; no migration
Owner / review:      platform team; revisit if traffic becomes bursty
```

That paragraph is what "communicate trade-offs" means on the exam. It has a decision, alternatives, criteria,
numbers, a risk, and a reversal cost.

---

## 4. The documentation set (and who reads each piece)

| Artefact | Audience | Contents |
|---|---|---|
| **ADR** (Architecture Decision Record) | Engineering, future you | Context, options, decision, consequences |
| **System / model card** | Risk, legal, ops | Intended use, out-of-scope use, eval results by segment, known limitations |
| **Data-flow diagram** | Security, legal | Sources, processors, storage, retention, trust boundaries |
| **Prompt registry** | Engineering | Versioned prompts, owner, change log, eval attached |
| **Eval report** | Sponsor, engineering | Dataset, metrics, segments, CIs, decision |
| **Runbook** | On-call | Alerts, first actions, rollback, kill switch, escalation contacts |
| **Handoff pack** | Receiving team | Architecture, credentials process, deploy steps, failure playbook, dashboards |
| **Incident post-mortem** | Everyone | Timeline, impact, root cause, actions with owners/dates |

**Documentation rule:** the runbook must be executable by someone who did not build the system, at 3 a.m., with
no access to you.

---

## 5. Lifecycle: phases, gates, ownership

| Phase | Exit gate | Owner |
|---|---|---|
| **Discovery** | Signed problem statement, metric, constraints | Architect + sponsor |
| **Design** | ADRs, threat model, eval plan, cost model approved | Architect |
| **Build** | Eval set passing, guardrails tested, runbook drafted | Engineering |
| **Pilot** | Acceptance criteria met on held-out data; sponsor sign-off | Product + sponsor |
| **Rollout** | Canary metrics within guardrails; rollback rehearsed | Engineering + ops |
| **Operate** | Dashboards live; on-call named; drift alerts configured | Ops |
| **Iterate** | Monthly review of quality/cost/incidents; re-eval on model changes | Product + architect |
| **Retire** | Data deletion plan, user comms, credentials revoked | Owner |

**Ownership questions the exam asks in disguise:**

- Who approves a high-risk action? (named role, not "the team")
- Who is on call for a quality regression? (not just uptime)
- Who can flip the kill switch? (and what happens to in-flight work)
- Who pays when token spend triples? (budget owner, alert thresholds)
- Who decides to change the model? (change control, not an engineer at 5 p.m.)

### Change control for prompts and models

Treat them as production configuration:

1. Change in a branch, with the eval diff attached.
2. Review by someone who owns the metric.
3. Canary 5% with guardrails.
4. Rollback is one flag (prompt version pinned).
5. Change log entry with the reason and the measurement.

---

## 6. Feedback loops that keep the system honest

| Loop | Cadence | Signal |
|---|---|---|
| User feedback (thumbs, edits) | Continuous | Per-answer quality; edit distance |
| Sampled human review | Weekly | Ground truth on a stratified sample |
| Incident review | Per incident | Failure mode → new eval case |
| Cost/quality review | Monthly | Unit economics vs budget |
| Full re-eval | Per model/prompt change, and quarterly | Drift, regressions |
| Stakeholder review | Monthly/quarterly | Expectation recalibration; scope changes |

The **failure gallery** (production failure → eval case) is the highest-yield loop in the whole lifecycle. It
makes every incident permanently cheaper.

---

## 7. Worked examples

### E6.1 The SLA demand (the canonical item)

Covered in §2. The exam version: accept/refuse/promise-bigger-model are all wrong; **evidence + per-segment SLA
+ agreed measurement + human path for the weak segment** is right.

### E6.2 Scope creep at design review

Sponsor: "while you're at it, can it also recommend pricing?" Correct response: log as a new requirement,
estimate the added risk and eval burden, and return with a decision — not a silent yes inside the same sprint.
Domain 6 rewards protecting the agreed scope with evidence, not enthusiasm.

### E6.3 The go-live conversation

Three weeks out, accuracy on the pilot is 91% against an agreed 92% target, and the gap is one document type.
Options: delay, launch with that type routed to humans, or launch and monitor.

**Correct:** present the segmented result, propose launching with the weak segment in human review, define the
condition for removing that restriction, and get it signed. That satisfies the outcome, the risk, and the date —
and it is testable. "Launch and see" is not.

### E6.4 Handoff that actually works

Give the runbook to an engineer who has never seen the system and watch them: deploy to staging, trigger an
alert, find the dashboard, flip the kill switch, restore. Every hesitation is a documentation defect. This is
also objective 7.3's "check whether they can finish the task without your help".

### E6.5 The cost overrun conversation

Token spend is 3× forecast. Correct: bring unit economics (cost per resolved task), attribute the change
(context growth? retry rate? model tier?), propose the fix with its quality impact (trim context, cache, route),
and state the residual risk. Do not present only the total, and do not silently switch to a cheaper model.

### E6.6 Retiring the feature

Comms to users, deletion of indexed data and caches, revocation of credentials and MCP scopes, archival of
prompts/evals for audit, and a post-implementation note. "We turned it off" leaves credentials and data behind.

---

## 8. Traps

1. Accepting an unmeasurable requirement ("99.9% accurate") without defining the unit.
2. Refusing any SLA because "AI is probabilistic" — the sponsor needs a workable commitment.
3. Reporting one aggregate number to a sponsor who will make a segmented decision.
4. Promising a capability improvement to avoid a hard conversation.
5. Documenting architecture only for engineers, then being surprised security blocks go-live.
6. No named owner for the human review queue, rollback, or the kill switch.
7. Handoff by walkthrough only, with no written runbook.
8. Silent model/prompt changes with no change log.
9. Treating the pilot as the end of evaluation rather than the start of monitoring.
10. Forgetting the retirement path — data, credentials, and eval artefacts.

---

## 9. Practice questions

**Q1.** Three weeks before go-live, the operations head demands a 99.9% accuracy SLA on invoice extraction. Your
eval shows 96.4% field-level, with most errors on handwritten documents. What do you do first?

- A. Accept the SLA and close the gap with prompt tuning before launch
- B. Refuse any SLA because model output cannot be guaranteed
- C. Present accuracy by document type, propose a per-type SLA with human review for handwritten documents, and
  agree how accuracy will be measured in production
- D. Switch to the largest model and commit to 99.9% once deployed

**Answer: C.** The job is to align the expectation with the evidence. Segmentation shows where the risk is, a
review path covers the weak segment, and an agreed measurement makes the SLA testable. A commits to an unproven
number; B leaves the sponsor without a decision; D promises an outcome nobody has measured and inflates unit cost.

---

**Q2.** At a design review the sponsor asks to add a new capability two weeks before launch. The best response?

- A. Add it — the sponsor is the customer
- B. Decline and cite the change freeze
- C. Record it as a new requirement with its risk, evaluation burden and cost, and bring a decision back with a
  dated recommendation
- D. Add it behind a feature flag and skip the eval to protect the date

**Answer: C.** Scope changes are legitimate; unmeasured scope changes are not. C keeps the relationship and the
engineering discipline. A risks the launch, B is unhelpful, D ships an unevaluated capability — which is the
failure mode this domain exists to prevent.

---

**Q3.** Which document most directly lets an on-call engineer who did not build the system recover it at 3 a.m.?

- A. The architecture decision records
- B. A runbook with alerts, first actions, rollback and kill-switch steps, and escalation contacts
- C. The eval report
- D. The prompt registry

**Answer: B.** The runbook is the operational artefact. ADRs explain why, the eval report explains quality, the
registry explains versions — none tells you what to do when the p95 alert fires.

---

**Q4.** A sponsor asks "is it accurate?" in a steering committee. Which answer is best?

- A. "96.4% accurate"
- B. "96.4% of fields on printed invoices, 61% on handwritten which we route to human review; here is how we
  measure it weekly"
- C. "It depends on the document"
- D. "As accurate as the underlying model allows"

**Answer: B.** It gives the number, the unit, the segment that matters, the mitigation, and the measurement
method — everything needed to make a decision. A invites a false conclusion. C looks evasive. D transfers
responsibility without informing.

---

**Q5.** Which set best constitutes a complete handoff?

- A. A code walkthrough recording and repository access
- B. Runbook, architecture and data-flow diagrams, deploy/rollback steps, dashboards, failure playbook, named
  owners, and a verified dry run by the receiving team
- C. The README and the eval results
- D. A three-month shadowing period

**Answer: B.** Handoff is proven by the receiver operating it, which requires documentation *and* a dry run.
A and C lack operational detail; D may help but is not a handoff artefact and has no verification step.

---

**Q6.** Six months after launch, accuracy drifts down with no code change. What is the first lifecycle action?

- A. Roll back the most recent prompt version
- B. Check input distribution and retrieval logs (new document types, changed source data, stale index) before
  changing anything
- C. Re-run the original eval set and file the difference as model drift
- D. Schedule a model upgrade

**Answer: B.** Drift is usually data or population change, not the model. Retrieve the evidence first, then change
one thing. A presumes a cause; C measures the symptom without diagnosing; D is the expensive guess this exam keeps
punishing.

---

## 10. 60-second recall

- Discovery outputs: problem, metric with unit/segment/baseline/target, constraints, non-goals, risks, draft SLA,
  acceptance criteria — signed.
- SLA conversation: evidence → per-segment proposal → agreed measurement → residual risk accepted → path to a
  higher number.
- Trade-off template: decision, options, criteria, evidence, residual risk, reversal cost, owner.
- Documentation set: ADR, model card, data flow, prompt registry, eval report, runbook, handoff, post-mortem.
- Lifecycle gates: discovery → design → build → pilot → rollout → operate → iterate → retire, each with an owner.
- Prompts and models are production configuration: eval-gated, canaried, one-flag rollback.
- Handoff is proven by a dry run by someone else, not by a walkthrough.
- Failure gallery: every incident becomes an eval case.
