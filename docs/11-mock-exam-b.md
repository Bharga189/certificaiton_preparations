# 11 · Mock exam B — items 32–63

**How to use this.** Cover the answer key and take this one **timed: 60 minutes for 32 items**, no notes. This is
the second half of a 63-item paper; if you did Mock A, your combined score is the closest thing to a readiness
signal you will get without the real exam.

Domain mix: D1 ×5 · D2 ×4 · D3 ×6 · D4 ×5 · D5 ×5 · D6 ×5 · D7 ×2.

---

### 32 · D1
A team must review ten annual reports, extracting the same 12 metrics from each. The documents are independent
and the metrics are well defined. Latency budget is generous. Which pattern?

- A. Sequential chain across all ten documents
- B. Sectioning: one call per document in parallel, then a deterministic aggregation step
- C. An autonomous agent that decides which documents to read
- D. A multi-agent system with a specialist agent per metric

---

### 33 · D1
When is an autonomous tool-using agent the *most appropriate* choice?

- A. The required steps cannot be enumerated in advance and the environment provides ground truth
- B. The process has fixed stages defined in a policy document
- C. Every request must produce a byte-identical output
- D. The task must complete in a single model call

---

### 34 · D1
A regulator requires that the same claim always follows the same routing path, with an explanation. Which design
satisfies that?

- A. An autonomous agent with tool access, because it adapts to each claim
- B. A deterministic workflow: constrained classification, rule-based routing in code, and the decision logged
- C. A multi-agent system where agents negotiate the route
- D. A generative answer that explains the routing it chose

---

### 35 · D1
Which scenario genuinely justifies a multi-agent architecture?

- A. Two independent corpora with different tool surfaces, processed in parallel, each agent testable alone
- B. One corpus where every agent needs the full context
- C. A 600 ms p95 requirement for a two-step task
- D. A task with a fixed, short sequence of three calls

---

### 36 · D1
An agent sometimes calls the same search tool repeatedly with identical arguments until the turn limit. What is
the best fix?

- A. Raise the turn limit so it can finish
- B. Detect repeated identical calls, cap iterations per task, and hand off to a fallback path with the partial result
- C. Add "do not repeat tool calls" to the system prompt and ship
- D. Remove the search tool

---

### 37 · D2
A prompt produces valid JSON 92% of the time, and the remaining 8% breaks the downstream parser. Which addition
addresses the actual defect?

- A. A longer role description and warmer tone instructions
- B. An explicit output contract with a strict schema, plus a bounded repair path and a deterministic fallback
- C. A higher `max_tokens`
- D. A larger model with the same prompt

---

### 38 · D2
Why should few-shot examples include hard negatives rather than only clean, typical cases?

- A. They reduce token usage
- B. They teach the decision boundary — near-misses show what makes an item *not* qualify
- C. They make the prompt cacheable
- D. They eliminate the need for an output schema

---

### 39 · D2
A critical rule ("never quote prices without a validity date") is buried in the middle of a 90k-token context and
is sometimes ignored. Which change most reliably improves compliance?

- A. Repeat the rule in one line immediately before the question, and retest
- B. Increase the temperature
- C. Move the rule to the very beginning and remove all examples
- D. Add 20 more pages of policy text

---

### 40 · D2
For which task is extended thinking most clearly worth its cost?

- A. Formatting a date string into ISO 8601
- B. Applying a multi-clause refund policy to an ambiguous customer situation
- C. Classifying a message into one of four routing labels
- D. Rewriting a sentence in a different tone

---

### 41 · D3
A `search_documents` tool implementation accepts a `user_id` argument that the model fills in. What is the
problem, and the fix?

- A. No problem: the model is instructed to pass the correct ID
- B. Client/model-controlled identity allows access to other users' documents; derive the identity server-side
  from the authenticated session
- C. The tool needs a larger timeout
- D. The tool should accept an email address instead

---

### 42 · D3
An agent must issue refunds inside an existing transaction that enforces fraud checks and idempotency. Which
integration approach fits best?

- A. An MCP server exposing a generic refund tool
- B. A direct tool handler you own, calling the transactional service with server-side validation
- C. A CLI command the agent runs
- D. Agent-to-agent negotiation with the payments service

---

### 43 · D3
A 9,000-row price list is chunked into 512-token windows and answers badly ("which SKU is cheapest in category
B?"). Best fix?

- A. Re-embed with a bigger model
- B. Chunk by row/record with the header repeated, and store structured metadata for filtering
- C. Raise top-k to 20
- D. Convert the price list to images

---

### 44 · D3
An enterprise wants one agent to work across an internal catalogue of 400 tools. Which design is most
appropriate?

- A. Put all 400 definitions in the system prompt
- B. Progressive discovery: expose a search/load mechanism so relevant tools are loaded on demand
- C. Ask the model to memorise the catalogue
- D. Create 400 sub-agents, one per tool

---

### 45 · D3
Which TWO fields are most important to log for every RAG request?

- A. The retrieved chunk IDs and their scores
- B. The user's full raw input including any PII, for debugging
- C. The prompt version and model identifier
- D. The developer's local environment variables
- E. The model's internal chain of thought

---

### 46 · D3
An internal wiki page, authorised for the requesting user, contains text instructing the agent to export data.
Which statement is correct?

- A. Authorisation of the source means its content is trusted
- B. Authorisation is not integrity: the content must still be treated as data, and the agent's capabilities must
  bound the damage
- C. The user should be blocked from the wiki
- D. The model's safety training makes this impossible

---

### 47 · D4
You plan to use an LLM judge for answer quality. What must be done before trusting its scores?

- A. Nothing; modern judges correlate well with humans
- B. Calibrate it against human labels on a sample, measure agreement, and control for position/verbosity bias
- C. Use the same model that generated the answers
- D. Average the judge with the model's self-reported confidence

---

### 48 · D4
p50 latency is 900 ms and p95 is 4.2 s against a 3 s SLA. What does this indicate and what should you do?

- A. The average is fine; no action
- B. A long tail — profile per stage, parallelise independent calls, cap iterations, trim output, cache the prefix
- C. Move the entire workload to a faster tier
- D. Report p50 to the sponsor instead

---

### 49 · D4
In what order should you apply cost optimisations to an existing, measured system?

- A. Downgrade the model tier, then cache, then trim context
- B. Trim context, then cache, then route by complexity, and only then consider a tier change
- C. Enable caching first, then switch to batch
- D. Fine-tune a smaller model first

---

### 50 · D4
A provider releases a new model version and quality complaints start. What is the first step?

- A. Immediately roll back and stop investigating
- B. Re-run the pinned eval set on old and new versions and compare per segment
- C. Ask the model why its answers changed
- D. Add more few-shot examples for the failing cases

---

### 51 · D4
Why must the final test set be held out from prompt iteration?

- A. To reduce token costs
- B. Otherwise reported gains include fitting to the test items and no longer estimate production performance
- C. Because eval sets expire
- D. To satisfy auditors only

---

### 52 · D5
Clinicians approve 99.4% of AI drafts with a 4-second average review. What does this most likely indicate?

- A. Excellent model quality; reduce headcount
- B. Automation bias — the gate is not functioning; use seeded-error audits, show evidence in the UI, and measure
  the override rate
- C. Clinicians need training on the tool
- D. The model should be upgraded to preserve the approval rate

---

### 53 · D5
Which practice best supports data minimisation before prompting?

- A. Send the full record so the model has complete context
- B. Redact or tokenise direct identifiers, send only the fields needed for the task, and keep the mapping in your
  own vault
- C. Rely on the provider's retention policy
- D. Encrypt the prompt in transit only

---

### 54 · D5
Why must a kill switch define a degraded mode?

- A. To satisfy the audit requirement without changing behaviour
- B. So disabling the AI routes work to a defined human path rather than causing an outage
- C. Because the model may refuse requests
- D. To reduce token consumption during incidents

---

### 55 · D5
A team reports overall accuracy of 94%. Which additional measurement is required to assess fairness?

- A. A second overall accuracy from a different sample
- B. Accuracy, refusal and escalation rates broken down by user group and language
- C. Token cost per request
- D. The model's stated confidence distribution

---

### 56 · D5
Which TWO items belong in an audit record for an automated decision?

- A. The identity of any human approver and the timestamp
- B. The prompt version and model identifier
- C. The developer's personal notes
- D. Raw PHI for completeness
- E. The office Wi-Fi SSID

---

### 57 · D6
A sponsor says "we need it to be accurate". What is the most useful next question?

- A. "How accurate do you need it to be?"
- B. "Which decision improves, measured on which unit — field, document or ticket — for which segment, against
  what baseline?"
- C. "Which model do you prefer?"
- D. "What is your budget?"

---

### 58 · D6
How is a handoff best verified?

- A. The architecture is explained in a meeting
- B. Someone who did not build the system performs deploy, alert response and rollback using only the runbook
- C. The README is complete
- D. The original team remains on call

---

### 59 · D6
Token spend is 3× forecast. Which response is best?

- A. Switch to the cheapest model immediately
- B. Present cost per successful task, attribute the increase (context growth, retries, tier), and propose a fix
  with its quality impact
- C. Absorb it and report at quarter end
- D. Disable caching to simplify billing

---

### 60 · D6
Six months after launch, quality drifts down with no code change. What is the first lifecycle action?

- A. Roll back the last prompt version
- B. Check input distribution and retrieval logs — new document types, changed sources, stale index — before
  changing anything
- C. Re-run the original eval set and label the gap "model drift"
- D. Schedule a model upgrade

---

### 61 · D6
A system is being retired. Which set of actions is complete?

- A. Turn off the feature flag
- B. Disable the feature with user comms, delete indexed data and caches, revoke credentials and MCP scopes, and
  archive prompts/evals for audit
- C. Delete the repository
- D. Stop paying the model provider

---

### 62 · D7
Which content does **not** belong in a committed project memory file (`CLAUDE.md`)?

- A. Build, test and lint commands
- B. Architecture map and ownership links
- C. API keys and customer identifiers
- D. "Never edit a shipped migration" rules

---

### 63 · D7
A team wants secret paths blocked *before* a tool call executes. Which mechanism?

- A. A prompt instruction in `CLAUDE.md`
- B. A `PreToolUse` hook that blocks matching paths, plus deny permission rules
- C. A weekly transcript audit
- D. A warning logged on read

---

## Answer key and explanations

### 32 — B
Independent documents with identical, well-defined extraction is textbook sectioning: parallel calls, then
deterministic aggregation. **A** is latency-linear for no benefit. **C** adds planning for a known plan. **D**
multiplies cost by metrics and duplicates context.

### 33 — A
Agents earn their cost when the path cannot be enumerated and the environment returns ground truth to steer by.
**B** describes a workflow. **C** requires determinism that autonomy cannot guarantee. **D** contradicts the
multi-turn shape of an agent.

### 34 — B
Determinism plus explanation requires code-controlled routing and a logged decision. **A** and **C** make the path
model-dependent. **D** produces a narrative that may not match how the route was actually chosen.

### 35 — A
Separable corpora, different tool surfaces, parallel work and independent testability are the four conditions that
justify multi-agent. **B** duplicates context and loses coherence. **C** is latency-sensitive, where hand-offs
hurt. **D** is a workflow.

### 36 — B
Repeated identical calls signal a loop; detect it, cap iterations, and fail to a defined fallback with the partial
result. **A** increases cost and tail latency. **C** is a request inside a loop that already ignores instructions.
**D** removes a capability the task needs.

### 37 — B
The defect is an unenforced output contract. A strict schema plus bounded repair and a deterministic fallback
makes failure predictable. **A** is irrelevant. **C** does not change the probability of malformed output. **D**
is unmeasured and may change the failure shape without fixing it.

### 38 — B
Examples teach boundaries; near-misses show the discriminating feature. **A** is false (they add tokens). **C** is
false (cacheability depends on stability, not content type). **D** is false — schema and examples solve different
problems.

### 39 — A
Recall is strongest at the start and end; a one-line restatement immediately before the question is cheap and
directly targets the failure. **B** increases variance. **C** removes teaching material and does not fix the
middle-position problem. **D** worsens dilution.

### 40 — B
Ambiguity, multiple constraints and policy application benefit from explicit reasoning. **A**, **C** and **D** are
mechanical transformations where thinking adds latency and cost with no accuracy gain.

### 41 — B
Identity must come from the authenticated session, never from a model-supplied parameter — that is a
client-controlled authorisation bypass. **A** is exactly the failure (untrusted input choosing the scope). **C**
is unrelated. **D** is still model-supplied and adds ambiguity.

### 42 — B
App-specific transactional logic with validation and idempotency belongs in a handler you own and can test. **A**
generic MCP tool hides the transaction and its guarantees. **C** runs with ambient permissions and no transaction
boundary. **D** is over-engineered for a single-service action.

### 43 — B
Structured data wants record-level chunks with repeated headers and metadata for filtering — the query is a
filter-plus-lookup, not a semantic one. **A** does not fix structure loss. **C** adds noise. **D** destroys
machine readability.

### 44 — B
Progressive discovery keeps the context small and selection accurate; it exists for large tool catalogues. **A**
degrades selection and burns tokens on every call. **C** is not a mechanism. **D** creates 400 maintenance units
and routing overhead.

### 45 — A and C
Chunk IDs and scores let you evaluate retrieval and verify citations; prompt version and model identify what
produced the answer. **B** is a privacy risk. **D** is unrelated and sensitive. **E** is not exposed reliably and
is not the audit artefact.

### 46 — B
Authorisation says the user may see the page; it says nothing about the page being safe. Treat all retrieved
content as data and bound capability. **A** is the misconception the item tests. **C** penalises the victim. **D**
is not a control.

### 47 — B
A judge is a model with biases; calibrate against humans, report agreement, and swap positions in pairwise tests.
**A** is false. **C** invites self-preference bias. **D** combines two uncalibrated signals.

### 48 — B
A good median with a bad tail means retries, loops, large inputs or cold caches. Fix the tail specifically. **A**
ignores the SLA. **C** degrades quality broadly to fix a minority. **D** is misreporting.

### 49 — B
Fix waste before buying a cheaper engine: trim, cache, route, then tier. **A** may lose quality before you have
measured the cheaper alternatives. **C** skips the largest saving (context) and batch is a latency trade. **D**
needs data and a maintenance plan and is the highest-effort option.

### 50 — B
Attribute the change with the pinned eval, by segment, before acting. **A** discards the diagnosis. **C** is not
evidence. **D** patches symptoms before you know which segment moved or why.

### 51 — B
Iterating against the test set leaks information into the prompt; the reported number stops estimating unseen
performance. **A** is false. **C** is false. **D** is a side effect, not the reason.

### 52 — B
Near-zero override with seconds-long review is the signature of a non-functioning gate. Seed errors, show the
evidence, measure detection. **A** removes the control compliance depends on. **C** blames staff for process
design. **D** is unrelated.

### 53 — B
Minimisation means the model sees only what the task needs; identifiers are tokenised and the mapping stays with
you. **A** maximises exposure. **C** relies on someone else's configuration. **D** protects transit, not the prompt
or logs.

### 54 — B
A switch without a degraded mode turns an AI incident into a service outage, which is why teams hesitate to use
it. **A** is the opposite of the intent. **C** and **D** are not reasons to define a human path.

### 55 — B
Fairness is a distributional property; you need per-group quality and behaviour, not another aggregate. **A**
makes the same mistake twice. **C** is cost. **D** is uncalibrated self-report.

### 56 — A and B
Accountability and reproducibility. **C** is not evidence. **D** creates a retention liability. **E** is
irrelevant.

### 57 — B
It converts a vague expectation into a measurable requirement: unit, segment, baseline and decision. **A** yields
a number with no unit. **C** and **D** are premature implementation questions.

### 58 — B
Handoff is proven by the receiver operating the system from the documentation. **A** is a briefing. **C** may be
incomplete without a dry run. **D** is not a handoff.

### 59 — B
Attribution plus unit economics plus a proposed fix with its quality impact is the professional response. **A**
trades quality silently. **C** hides a budget problem. **D** removes a saving.

### 60 — B
Drift is usually population or data, not the model. Retrieve evidence, then change one thing. **A** presumes a
cause. **C** measures the symptom. **D** is the expensive guess.

### 61 — B
Retirement covers users, data, credentials and audit artefacts. **A** leaves data and access behind. **C**
destroys evidence. **D** does not remove anything.

### 62 — C
A committed memory file is public to everyone with repo access: commands, architecture and rules belong; secrets
and customer identifiers do not. **A**, **B** and **D** are exactly the useful content.

### 63 — B
Deterministic prevention before execution, at two layers. **A** is a request in the same context as the task. **C**
is detection after exposure. **D** is a warning — which is a log line nobody reads.

---

## Scoring

Target **≥23/32**. Combined with Mock A: **≥46/63** overall, no domain below 50%.

| Domain | Items | Your score |
|---|---|---|
| D1 | 32–36 | /5 |
| D2 | 37–40 | /4 |
| D3 | 41–46 | /6 |
| D4 | 47–51 | /5 |
| D5 | 52–56 | /5 |
| D6 | 57–61 | /5 |
| D7 | 62–63 | /2 |

### If you scored below target

| Weakest domain | Re-read | Then |
|---|---|---|
| D1 | `01-solution-design.md` §2 and §4 | Re-run `d1_patterns.py`; explain each gate aloud |
| D2 | `02-models-prompting-context.md` §4 | Re-derive the cache break-even by hand |
| D3 | `03-integration.md` §2–3 | Re-run `d3_rag_acl.py`; break the ACL test on purpose |
| D4 | `04-evaluation.md` §1, §6 | Recompute 0.97^10 and the escalation maths |
| D5 | `05-governance.md` §2–3 | Write your own risk register with owners |
| D6 | `06-stakeholders-lifecycle.md` §2 | Write the sponsor memo for a real system |
| D7 | `07-developer-productivity.md` §1–2 | Write the deny list and hook rules for your repo |
