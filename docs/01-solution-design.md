# 01 · Solution Design & Architecture — 17%

> **What this domain really tests:** can you pick the *cheapest, simplest* structure that still meets the
> stated reliability, auditability and latency requirements — and defend not adding autonomy?

Almost every item here is a variation of one question: **"Is this a workflow or an agent?"** Get that
distinction crisp and you can reason your way to most answers.

---

## 1. The vocabulary the exam uses

Anthropic's split (from *Building effective agents*) is the one to memorise:

| Term | Definition | Who decides the path |
|---|---|---|
| **Augmented LLM** | One model call + retrieval, tools, memory | Nobody — there is one step |
| **Workflow** | LLM calls and tools orchestrated through **predefined code paths** | Your code |
| **Agent** | LLM **dynamically directs** its own process and tool use | The model |

That is the whole axis. "Agentic" is the umbrella term for both; the exam uses "agent" in the narrow sense.

### The pattern ladder — climb only as high as you must

```
1. Single call                     ─ cheapest, most predictable, most testable
2. Augmented LLM (RAG + tools)      ─ answers "what does our data say"
3. Prompt chaining (+ gates)        ─ fixed subtasks, each easier than the whole
4. Routing                          ─ distinct input classes need different handling
5. Parallelisation (section/vote)   ─ independent subtasks, or need for confidence
6. Orchestrator–workers             ─ subtasks unknown until you see the input
7. Autonomous agent (tool loop)     ─ open-ended task, unpredictable step count
8. Multi-agent                      ─ parallel specialisation with real separation
```

Each rung buys flexibility and costs **latency, tokens, testability and debuggability**. The exam consistently
rewards the lowest rung that satisfies the constraints, and penalises jumping to rung 7 for a task that is
already written down in a policy document.

### The four questions that choose the rung

Ask these in order; stop at the first "yes":

1. **Can one call with good context do it?** → rungs 1–2.
2. **Are the steps known and ordered?** → rung 3, with gates between steps.
3. **Are there distinct input classes?** → rung 4 (route), and route *cheap first*.
4. **Are subtasks indeterminate but the goal fixed?** → rung 6.
5. Only if the *path* itself is unknowable, and errors are recoverable, and a human can intervene →
   rung 7/8.

---

## 2. Decision tables you should be able to redraw from memory

### 2.1 Pattern selection

| Requirement in the stem | Pattern | Why |
|---|---|---|
| Fixed stages, each depends on the previous, must be auditable | **Prompt chaining + validation gates** | Intermediate outputs persisted; failures retry per stage |
| Distinct categories (refund / technical / general) | **Routing** | Separate prompts per class; cheap classifier + escalation |
| Subtasks independent (extract 5 sections of a contract) | **Sectioning (parallel)** | Latency ↓, each call focused |
| Need confidence on a risky classification | **Voting (parallel)** | Multiple passes, majority/threshold |
| "Number of steps depends on the ticket" | **Orchestrator–workers** | Subtask list is generated, not hardcoded |
| Clear quality criteria + iteration measurably helps | **Evaluator–optimizer** | Generator + critic loop with a stop rule |
| Open-ended, tools, environment feedback, human available | **Autonomous agent** | Path unknowable; ground truth from tool results |
| Two genuinely separate expertise domains, parallel, latency-tolerant | **Multi-agent (supervisor)** | Context isolation + specialisation |

### 2.2 When multi-agent is *wrong*

| Signal | Why multi-agent hurts |
|---|---|
| Sub-agents need the same full context | You pay to duplicate tokens and lose coherence |
| Tight coupling between steps | Hand-off contracts become the bug surface |
| Sub-100ms–1s latency budget | Sequential hand-offs multiply latency |
| Single small context would fit | Coordination overhead > specialisation benefit |
| You cannot evaluate each agent separately | Debugging becomes non-deterministic guessing |

Multi-agent earns its cost when: (a) contexts are genuinely separable, (b) each agent has a different tool
surface, (c) work is parallelisable, (d) you can test each agent in isolation. Otherwise a supervisor with one
big prompt is cheaper and easier to own.

### 2.3 Orchestration mechanics

| Concern | Pattern | Note |
|---|---|---|
| Step 3 fails | Retry step 3 only, from a checkpoint | Never restart the batch |
| Duplicate delivery risk | Idempotency key per unit of work | Retries must be safe |
| Poison input | Max retries → dead-letter queue + alert | Do not loop forever |
| Partial success | Return per-item status, not one exception | The UI needs "3 of 50 failed" |
| Long-running tasks | Persist state; resume by ID | Agents die mid-run |
| Cost blow-out | Per-task token budget + max iterations | Hard stop, not a suggestion |
| Audit trail | Persist every intermediate output | "Why did it say that?" |

---

## 3. Worked examples

### E1.1 Freight quotes — the canonical workflow item

**Stem shape:** extract costs and terms → validate against procurement policy → produce a recommendation.
Stages follow consistent rules; later stages depend on earlier output; must be predictable and auditable.

**Correct:** a fixed workflow of discrete, sequenced calls with validation gates.

**Why the others lose:**

| Option | Fails because |
|---|---|
| One monolithic prompt | No intermediate checkpoints; you cannot tell which stage produced a bad number; cannot retry selectively |
| Autonomous agent | Steps are already known, ordered, repeatable → autonomy buys nothing and costs consistency |
| Fully parallel calls | Ignores data dependencies: validation needs extraction, recommendation needs validation |

**Implementation sketch** (`examples/d1_patterns.py` runs this with a gate):

```python
extract  = call(model="claude-haiku-5-5", system=EXTRACT_SCHEMA, user=quote_text)
if not validate(extract):                 # code, not a prompt instruction
    extract = retry_once(extract, missing_fields)   # selective retry
    if not validate(extract):
        return dead_letter(quote_id, extract)      # stop; do not recommend
policy_ok = call(model="claude-sonnet-5-5", system=POLICY_RULES, user=extract)
if not policy_ok.passed:
    return needs_human(quote_id, policy_ok)        # HITL for exceptions
return call(model="claude-sonnet-5-5", system=RECOMMEND, user=policy_ok)
```

**The exam-worthy sentence:** *"A workflow makes each call independently evaluable, exposes intermediate
outputs for audit, and lets validation prevent bad data reaching the recommendation."*

### E1.2 Routing with cheap-first escalation

40k support messages/month, three intents, and a hard p95 latency target. Haiku-classify, then one specialist
prompt. Escalate to a stronger model only when the classifier is uncertain **or** the item is high-value.

```python
route = classify(message)                    # haiku-5-5, constrained to 3 labels
if route.confidence < 0.7 or route.intent == "billing_dispute":
    answer = specialist(message, model="claude-opus-5-5")
else:
    answer = specialist(message, model="claude-sonnet-5-5")
```

Two exam points: (1) routing is a **workflow** — your code decides; (2) a *measured* confidence threshold is
acceptable for **routing**, but never as a gate for a hard safety requirement (see D5).

### E1.3 40-file refactor — orchestrator–workers earns its place

You cannot know in advance which files need changing or how. The orchestrator reads the task, emits a subtask
list, workers execute per-file, the orchestrator synthesises and runs the test suite.

```python
plan   = orchestrator(task, repo_map)         # dynamic decomposition
edits  = [worker(t) for t in plan.subtasks]   # parallel; isolated context each
result = orchestrator.synthesise(edits)       # conflict resolution
accept = run_tests(result)                    # ground truth, not model opinion
```

This is the pattern's signature use case: **subtasks are data-dependent, but the goal and the success test are
fixed.** Note the last line — verification comes from the environment, not from the model's self-assessment.

### E1.4 Augmented LLM: the answer you should reach for more often

300 policy documents, questions like "what's our parental leave after 5 years?" No multi-step reasoning, no
external actions. Correct: **retrieve top-k, answer in one call, cite the chunk IDs**. No agent, no chain.

The tell in the stem: *the answer already exists in a document*. Retrieval is the capability; orchestration adds
nothing but failure modes.

### E1.5 Designing for failure (the objective candidates forget)

| Failure | Naive handling | Correct handling |
|---|---|---|
| Extraction returns null field | Pass `null` downstream | Gate → retry with the missing fields named → dead-letter |
| Timeout on step 3 | Retry whole job | Checkpoint at step 2; retry step 3 only |
| Duplicate webhook | Process twice | Idempotency key; upsert not insert |
| Model calls a tool in a loop | Let it run | `max_iterations`, token budget, loop detector on repeated identical calls |
| Output fails schema | Prompt "please fix" forever | Bounded repair attempts (≤2), then fall back to human/fallback model |

### E1.6 Latency budget maths worth doing on paper

A 5-stage chain at 900 ms per call = 4.5 s p50, plus overhead. If the requirement is 2 s, chaining is the wrong
shape — section the independent parts (parallel) and cache the shared prefix. The exam will describe the
requirement and expect you to reject sequential chaining. **Always check whether the stages are actually
dependent before accepting a chain.**

---

## 4. Traps

1. **"Autonomous agent" offered for a rules-based process.** Any stem that says *fixed*, *predictable*,
   *consistent rules*, *auditable sequence* is telling you: workflow.
2. **"Multi-agent" offered for a single-domain task.** Specialisation without separable context is cost.
3. **"Fine-tune a model per category."** Unjustified: needs data, drifts, and a classifier + prompt usually
   matches it for 12 fixed labels.
4. **Parallelising dependent stages.** If B needs A's output, concurrency is a bug, not an optimisation.
5. **Optimising the wrong metric.** A design that improves accuracy but blows the latency SLA is wrong *in the
   stem's terms*, even if it is technically superior.
6. **Forgetting the feedback loop.** Objective 1.2 explicitly includes feedback: where does a human or a test
   correct the system? A design with no correction path is incomplete.

---

## 5. Practice questions

**Q1.** A bank classifies 40,000 monthly complaints into 12 fixed categories and routes each by a fixed rule
per category. Categories and rules rarely change. Best architecture?

- A. Multi-agent system where a coordinator hands each complaint to a category-specialist agent
- B. One model call per complaint with structured output restricted to the 12 categories, then deterministic routing in code
- C. Autonomous agent with tools to read the complaint, look up policy and choose the route itself
- D. A separately fine-tuned model for each category

**Answer: B.** The label set is closed and the routing rule is deterministic, so constrain the model's output and
let code route. A and C add autonomy the task cannot use — and with 40k/month you pay for it 40k times. D needs
40k×12 of labelled data, plus retraining whenever policy changes, versus editing one enum. Note the answer still
says *measure* cost/latency/accuracy; the architecture is a baseline, not a guarantee.

---

**Q2.** A due-diligence team must review 200 contracts per deal, extracting 30 fields per contract, cross-checking
against a checklist, and flagging contradictions. The number of review passes needed varies by contract. Latency
budget is 20 minutes per deal. Which pattern?

- A. Single call per deal with all 200 contracts in context
- B. Prompt chaining with a fixed 3-step pipeline for every contract
- C. Orchestrator–workers: a planner assigns per-contract extraction and cross-check subtasks, then synthesises
- D. One autonomous agent with full filesystem access

**Answer: C.** The work decomposes cleanly by contract (parallelisable), but the number of cross-checks depends on
what extraction finds, so the subtask list is data-dependent — exactly orchestrator–workers. A fails on context
(200 contracts ≫ a sane working set) and on per-contract auditability. B is tempting but a *fixed* 3-step pipeline
can't adapt passes per contract. D would technically work but gives an unbounded agent authority over sensitive
deal files with no per-contract checkpoint — least privilege and auditability both fail.

---

**Q3.** An invoice pipeline processes 50,000 documents nightly. On a bad night, 3% fail extraction and the job
currently restarts the whole batch. What should change first?

- A. Switch to a larger model so fewer documents fail
- B. Add per-document retry with a bounded attempt count, a dead-letter queue, checkpointed resume, and an alert on
  dead-letter rate
- C. Increase the batch timeout
- D. Lower the extraction schema requirements so more documents pass

**Answer: B.** This is a *reliability* defect, not a quality defect: 97% already succeed, and restarting discards
work. Bounded retries + DLQ + resume + an alert on the failure rate is the textbook fix and gives you the
measurement you need. A is a capability change with no diagnosis — and if failures are handwritten documents,
a bigger model is expensive and unproven. C treats a symptom. D silently degrades the product.

---

**Q4.** An HR team asks 300 policy PDFs questions in natural language; answers must cite the source clause. No
actions, no multi-step reasoning, sub-3-second responses. What design?

- A. An agent with file-system and search tools that decides when to open documents
- B. Retrieval of top-k chunks + one call that answers and cites chunk IDs
- C. Prompt chaining: summarise each document, then summarise the summaries, then answer
- D. Fine-tune on the policy corpus

**Answer: B.** The answer exists in a document; the capability needed is retrieval, not orchestration. B is one
call, meets latency, and citations are grounded in retrieved IDs (checkable). A adds planning latency for a
single-hop lookup. C loses clause-level citation through summarisation and costs 300 calls. D is the classic
distractor: fine-tuning teaches style/format, not reliable recall of facts, and policies change.

---

**Q5.** A claims triage system must return in under 1.5 s. It needs: parse the claim, check coverage rules, and
check fraud signals. Parsing must finish before the other two, which are independent of each other. Pattern?

- A. Sequential chain: parse → coverage → fraud
- B. Parallel: parse, coverage and fraud concurrently
- C. Parse, then run coverage and fraud concurrently; aggregate
- D. Orchestrator–workers with dynamic subtasks

**Answer: C.** Respect the dependency, parallelise the rest. A wastes the independence of coverage and fraud and
likely misses the latency budget. B violates the dependency. D is over-engineering for a three-step known plan.
This item exists to test whether you read "which are independent of each other" — that clause is the answer.

---

**Q6.** An agent in production has 38 tools, and tool-selection accuracy has fallen; it increasingly calls the
wrong tool or calls two that overlap. Cheapest effective first step?

- A. Add a system-prompt paragraph describing when to use each tool
- B. Consolidate overlapping tools, tighten descriptions, and expose only the tools needed for the current task
  (or load them progressively)
- C. Replace the agent with the largest available model
- D. Add a second agent to review tool choices

**Answer: B.** Tool-selection quality degrades with tool count and overlap; the fix is a smaller, clearer tool
surface (least privilege helps accuracy *and* security). A does not scale to 38 descriptions and competes with
them for attention. C is unmeasured. D adds a full extra hop to catch a problem you can design away — and the
reviewer sees the same bloated surface.

---

## 6. 60-second recall

- Workflow = code decides the path. Agent = model decides. "Agentic" covers both.
- Climb the ladder only as far as constraints force: single → augmented → chain → route → parallel → orchestrator
  → agent → multi-agent.
- Known steps + auditability → **chaining with gates**. Distinct classes → **routing**. Independent subtasks →
  **parallel**. Data-dependent subtasks → **orchestrator–workers**. Unknown path → **agent**.
- Multi-agent only for separable contexts, distinct tool surfaces, parallel work, individually testable agents.
- Hard requirements live in code: gates, idempotency keys, bounded retries, DLQ, checkpoints, iteration caps.
- Latency budget × stage count is a design constraint, not an implementation detail.
- Verify with the environment (tests, policy engine), not with the model's opinion of itself.
