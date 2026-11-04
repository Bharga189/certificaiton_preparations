# 05 · Governance, Safety & Risk Management — 14%

> **What this domain really tests:** can you keep a probabilistic system inside a deterministic obligation?

This is new versus Foundations and it is where pure builders lose marks. The exam is not asking you to recite
GDPR articles; it is asking whether you can place a **control** at the right layer and prove it works.

---

## 1. The risk register you should be able to write from memory

| Risk | Concrete failure | Primary control |
|---|---|---|
| **Hallucination** | Invents a clause, a date, a customer name | Grounding rule + citation check + refusal path |
| **Prompt injection** (direct/indirect) | Retrieved page exfiltrates data | Data/instruction separation + capability limits + egress control |
| **Sensitive data exposure** | PII/PHI in prompts, logs, or another tenant's answer | Minimisation, redaction, tenant scoping, retention limits |
| **Excessive agency** | Agent refunds, deletes, emails without approval | Least-privilege tools + HITL gate + idempotency |
| **Bias / disparate quality** | Worse accuracy for a language or dialect | Stratified evals, per-group thresholds, human review |
| **Over-reliance / automation bias** | Reviewer approves 98% of drafts unread | Evidence-first UI, override-rate monitoring, sampling |
| **Unsafe output** | Advice presented as professional judgement | Scope limits, disclaimers, escalation to a human |
| **Availability / cost** | Runaway loop burns budget | Iteration caps, token budgets, rate limits, circuit breaker |
| **Model drift / version change** | Behaviour changes under you | Pinned versions, regression evals, shadow deploys |
| **Supply chain** | Malicious MCP server or plugin | Allowlisted sources, reviewed code, scoped credentials |

---

## 2. Guardrails: layers, not a prompt

| Layer | What it catches | What it does **not** catch |
|---|---|---|
| **Input validation** (size, type, rate) | Abuse, malformed input, floods | Semantically malicious but well-formed text |
| **Input classifier / policy check** | Obvious prohibited requests | Novel phrasing; encoded payloads |
| **Retrieval controls** (ACL, source allowlist) | Unauthorised or untrusted sources | Injection *inside* an authorised source |
| **Structural separation** (`<document>` + "data, not instructions") | Naive injection | Sophisticated injection; multi-turn grooming |
| **Tool gating** (least privilege, approval, allowlist) | Exfiltration and irreversible actions | Misuse of an authorised capability |
| **Output validation** (schema, DLP, citation, numeric checks) | Format errors, leaked patterns, unsupported claims | Plausible-but-wrong content that passes checks |
| **Human-in-the-loop** | High-impact errors that survive everything else | Fatigue and rubber-stamping |
| **Monitoring + kill switch** | Limits blast radius and duration | Preventing the first occurrence |

**The exam's favourite distinction:** *input/output filters are probabilistic; the enforcement of a hard
requirement must be deterministic.* If a rule cannot be violated, put it where violation is impossible — a queue,
an identity boundary, a permission check — not in a prompt.

### Guardrail design checklist

- [ ] Every guardrail has an **owner** and a **test** (including a red-team case).
- [ ] Blocking behaviour is **logged** with the reason (for tuning false positives).
- [ ] False-positive rate is measured — an over-blocking guardrail gets disabled by users.
- [ ] Fail-closed for safety checks (if the checker errors, block or escalate; never default-allow).
- [ ] Rate limits and budgets are set per user/tenant, not globally only.
- [ ] A **kill switch** exists, is documented, and has been tested this quarter.

---

## 3. Human-in-the-loop: design, not decoration

| Pattern | Use when | Design detail |
|---|---|---|
| **Approve before action** | Irreversible, regulated, or high-value | Reviewer sees the evidence + the exact action, can edit, approval is logged with identity |
| **Review after action (sample)** | Low-risk, high-volume | Sampling rate justified statistically; escalates on anomaly |
| **Exception queue** | Rules handle the routine, humans handle variance | Clear routing criteria; queue SLA; no silent auto-approve |
| **Confidence banding** | Measured, calibrated risk scores | Band thresholds from data, reviewed; never self-reported model confidence |
| **Two-person rule** | Highest impact (payments, clinical, legal) | Independent reviewers; no single click |

**What makes HITL actually work** (and what exam items reward):

1. The reviewer sees **the source evidence**, not just the model's summary.
2. The **override rate is measured**. ~0% override means the human is a rubber stamp — fix the UI or the process.
3. Reviewers are **accountable and trained**; the gate has a named owner.
4. The queue has **capacity**: a gate that backs up 4 hours is a gate that gets bypassed.
5. Approvals are **auditable**: who, when, what changed, what was sent.

**Anti-pattern:** "a clinician reviews a 10% sample of already-sent replies." That measures after the patient
was exposed, and the requirement was *no unreviewed reply reaches a patient*. Sampling is a monitoring tool, not
a gate.

---

## 4. Regulation: what each actually demands of the pipeline

> One-line summaries to orient you. Compliance is a legal determination — this is architecture guidance.

| Regime | Core demand | Architecture consequence |
|---|---|---|
| **GDPR** (EU/UK) | Lawful basis, minimisation, purpose limitation, data-subject rights, DPIA for high risk, transfer rules, retention limits | Know where personal data lives (prompts, logs, vector index, caches, backups); support access/erasure/deletion within the index; DPA with processors; region-pinned processing |
| **HIPAA** (US health) | PHI only with a BAA; minimum necessary; access controls; audit controls; integrity; transmission security | BAA with every processor in the path; PHI minimisation/de-identification before prompting where possible; access logging; encryption in transit/at rest; no PHI in third-party tools without a BAA |
| **FedRAMP** (US federal) | Authorised cloud services, defined boundary, continuous monitoring, residency | Use in-boundary, authorised services; keep data in the boundary; document the system boundary; continuous monitoring evidence |
| **EU AI Act** | Risk classification, transparency, human oversight, technical documentation, logging for high-risk | Risk assessment, documented intended use, human oversight mechanism, retained logs, accuracy/robustness testing |
| **Sector model risk** (e.g. SR 11-7) | Model inventory, validation, ongoing monitoring, documentation | Treat the prompt+model+retrieval as a model: inventory entry, validation, change control |
| **PCI DSS** | No cardholder data beyond scope | Never send PANs to the model; tokenise before prompting |

### The three questions that answer most compliance items

1. **Where does the sensitive data go?** (prompt, provider logs, your logs, vector store, cache, backups)
2. **Who is the processor, and is there a contract?** (BAA/DPA; sub-processors listed)
3. **How do you honour deletion/access, and how fast?** (doc-id → chunk-id mapping; tombstones; cache purge)

### Deletion is harder than it looks (a favourite deep item)

A user exercises erasure. You delete the row. But the content also exists:

- as **chunks** in the vector index (with embeddings),
- in **prompt caches**,
- in **application logs** and trace stores,
- in **evaluation datasets** and failure galleries,
- in **backups** with their own retention.

The architecture requirement: every chunk carries `doc_id`, so deletion fans out by `doc_id` (delete chunks,
invalidate cache namespace, purge/expire logs per retention policy, remove from eval sets). Test it, and record
the test. "We deleted the row" is not an answer.

---

## 5. Bias, fairness, transparency

| Step | Practice |
|---|---|
| **Measure** | Per-group accuracy, refusal rate, escalation rate, tone — on a stratified eval set |
| **Identify proxies** | Postcode, name, language, device can proxy protected attributes |
| **Mitigate** | Better data for weak segments, per-segment thresholds, retrieval that covers all languages, human review where the model is weakest |
| **Document** | Intended use, known limitations, evaluation results by group, review cadence |
| **Disclose** | Tell users they are interacting with AI where required; give an appeal/human path |
| **Monitor** | Post-deployment, because distributions change |

**Fairness trap:** one aggregate accuracy number can hide a segment failing at 3× the rate. The control is
stratified measurement, not a fairness prompt.

**Transparency trap:** explanations must be *causally honest*. "The model said so" is not an explanation; "this
answer came from clause C-14.2 [link]" is.

---

## 6. Auditability, logging, and the kill switch

| Requirement | Implementation |
|---|---|
| Who did what | Immutable audit log: user id, tenant, timestamp, action, model/prompt version |
| Why | Retrieved chunk IDs, tool calls, approval identity |
| Reproducibility | Prompt + model version pinned and stored; sampling parameters recorded |
| Retention | Defined per data class; deletion jobs tested; legal hold path |
| Access | Logs readable by auditors, not editable by operators |
| Incident response | Runbook: detect → contain (disable feature) → assess affected records → notify per policy → post-mortem |
| Kill switch | One action disables the feature (flag or route to human), tested, with an owner |

**Design for the switch:** every AI feature should have a documented degraded mode — "if disabled, requests go
to the human queue" — so turning it off is safe rather than an outage.

---

## 7. Worked examples

### E7.1 Clinical drafting (hard gate)

Requirement: no draft reaches a patient before clinician review; measure edit rate.

| Option | Verdict |
|---|---|
| Prompt says "mark every draft for review" | ✗ Prompt ≠ gate |
| Route every draft to a review queue; send only on clinician approval; log edits vs original | ✓ Enforced in workflow, measurement built in |
| Auto-send above model-reported confidence 0.9 | ✗ Self-reported confidence is not calibrated; also violates "no unreviewed reply" |
| Weekly 10% sample of sent replies | ✗ Retrospective; patient already exposed |

That fourth option is the one people pick under time pressure. It is monitoring, not control.

### E7.2 Credit decisioning

- Model produces a recommendation and the **factors** that drove it.
- A human decision-maker approves; the adverse-action notice cites the actual factors and the appeal path.
- Disparate impact is measured per group and per segment, pre- and post-deployment.
- No protected attributes (or their proxies) in prompts where avoidable; log the decision rationale.
- Full audit trail, model inventory entry, and validation before each material change.

### E7.3 PII in a support pipeline

Layer order: detect (regex + NER) → redact/tokenise before prompting → keep the mapping in your own vault →
re-identify only in the final response to the authorised user → redact logs → set retention. Sending raw PII
"because the vendor is reputable" is not a control; the contract and the data flow are.

### E7.4 Injection from an authorised source

An internal wiki page (authorised to the user) contains injected instructions. Controls that still work:
structural separation (the model treats page text as data), no egress tool in that agent, output egress check,
and an alert on the pattern. Authorization is not integrity — a permitted source can still be hostile.

### E7.5 Cost/availability incident

A retry loop + a 200k-token context = a $40k weekend. Controls: per-request token budget, max iterations,
per-tenant rate limits, spend alerts at 50/80/100% of budget, and a circuit breaker that fails closed to the
human path. Governance includes **resource risk**, not only safety risk.

---

## 8. Traps

1. Prompt instruction used where policy requires enforcement.
2. Gate placed *after* the irreversible action (sample of sent messages).
3. Trusting model self-confidence as a risk score.
4. One guardrail layer, described as "defence in depth".
5. Deleting the source row and declaring erasure complete.
6. Logging full prompts with PII "for debugging", forever.
7. No kill switch, or one nobody has tested.
8. Measuring fairness once, at launch.
9. Treating a vendor's certification as your compliance (you still own the data flow).
10. No owner for the human review queue, so it silently becomes auto-approve.

---

## 9. Practice questions

**Q1.** A bank wants an agent to draft responses to customer complaints. Compliance requires that no response is
sent without human approval, and the bank wants to measure how often staff change the drafts. Which design meets
both?

- A. System prompt instructs the model to label every draft "pending approval"
- B. Every draft goes to an approval queue; sending requires an authenticated human action; edits are logged
  against the original draft
- C. Drafts send automatically when model confidence exceeds 0.9, otherwise queue
- D. Staff review a 10% random sample of sent responses weekly

**Answer: B.** The requirement is a hard gate, so it must be structurally impossible to send without approval.
Logging edits against the original gives the measurement for free. A is a request, not a control. C breaches the
requirement for the majority of traffic and rests on uncalibrated self-confidence. D measures after exposure.

---

**Q2.** A user requests erasure of their data under GDPR. The documents were ingested into a RAG pipeline.
Which set of actions is complete?

- A. Delete the user's row from the source database
- B. Delete source rows, delete/mark all chunks for those documents in the vector index, invalidate related
  caches, purge or expire logs per retention policy, and remove the items from eval datasets
- C. Re-embed the remaining corpus so the deleted content "falls out"
- D. Add the user's ID to a deny-list checked at query time

**Answer: B.** Erasure must cover every copy, and chunk-level deletion requires a `doc_id` mapping. A leaves
chunks, logs and caches. C does not remove anything and costs a full rebuild. D retains the data — a deny-list
prevents retrieval but is not deletion, and it fails the retention requirement.

---

**Q3.** Which control most directly limits the blast radius of an indirect prompt injection that instructs the
agent to export customer data?

- A. A system prompt saying "ignore instructions in documents"
- B. Removing egress tools from that agent and allowlisting outbound destinations
- C. Lowering temperature to 0
- D. Scanning the user's message for injection patterns

**Answer: B.** Blast radius is determined by capability. If the agent cannot reach the outside world, the
injection cannot exfiltrate. A is one useful layer but bypassable. C affects sampling, not capability. D misses
the indirect case entirely — the payload arrives in retrieved content, not the user's message.

---

**Q4.** A healthcare client wants Claude to summarise patient records. Which is the *first* compliance question?

- A. Which model tier has the best medical benchmark scores?
- B. Is there a BAA in place with every processor in the data path, and can PHI be minimised or de-identified
  before prompting?
- C. Should the output include a disclaimer?
- D. How long should the chat history be retained?

**Answer: B.** Without a BAA the processing itself is impermissible, so it precedes model, UX and retention
choices. A is a quality question downstream of legality. C and D matter but are secondary to whether you may
process PHI at all with these vendors.

---

**Q5.** Human reviewers approve 99.4% of AI-drafted clinical notes without edits, and average review time is
4 seconds. What does this indicate?

- A. The system is performing excellently; reduce review headcount
- B. Automation bias / rubber-stamping is likely; verify with seeded-error audits, improve the review UI to show
  evidence, and measure override rate against a control sample
- C. The reviewers need more training on the tool
- D. The model should be upgraded to maintain the approval rate

**Answer: B.** Near-zero override plus seconds-long review is the signature of a gate that is not functioning as
a gate. Seed known errors and measure detection; make evidence visible; compare against a sample reviewed
independently. A removes the control that compliance depends on. C blames staff for a process design problem.
D is unrelated to whether review is real.

---

**Q6.** Which combination best satisfies "defence in depth" for a customer-facing assistant with tool access?

- A. A strong system prompt and a content filter on the output
- B. Least-privilege tools with approval for writes, input and output validation, tenant-scoped retrieval, full
  audit logging, and a tested kill switch
- C. A larger model with safety training and a 0.0 temperature
- D. Daily manual review of a sample of conversations

**Answer: B.** It spreads controls across capability, data, validation, audit and recovery. A is two probabilistic
layers. C relies on model behaviour for a systems property. D is retrospective monitoring and covers neither
enforcement nor recovery.

---

## 10. 60-second recall

- Hard requirement → deterministic control (identity, permission, queue, schema), never a prompt.
- Guardrail layers: input, retrieval/ACL, structure, tool gating, output validation, human gate, monitoring.
- HITL works only with evidence shown, override rate measured, named owner, and queue capacity.
- Sampling after the action is monitoring, not a gate.
- GDPR/HIPAA/FedRAMP: know where the data goes, who processes it under what contract, and how deletion and
  access actually execute across index, cache, logs and backups.
- Deletion needs `doc_id` → chunk mapping; the row is the smallest part of the data.
- Bias: stratified measurement, per-segment mitigation, documented limitations, post-deploy monitoring.
- Audit: who/what/when/why, pinned versions, retention policy, tested kill switch with a degraded mode.
