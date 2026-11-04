# 02 · Claude Models, Prompting & Context Engineering — 13%

> **What this domain really tests:** do you choose and steer models with *measurements*, and do you treat the
> context window as a budget rather than a bin?

Only 13%, but it leaks into every other domain — a wrong model choice or a bloated context shows up as an
integration, evaluation, or cost problem later.

---

## 1. Models: choose on evidence, not on the spec sheet

The current line-up (Nov 2026 — **verify before exam day**) is a four-tier ladder:

| Tier | Positioning | Relative cost (in/out per MTok) | Context |
|---|---|---|---|
| **Fable 5.1** | Hardest reasoning, long-horizon agentic work | $10 / $50 | 1M |
| **Opus 5.5** | Long-running agentic coding and knowledge work | $4 / $20 | 1M |
| **Sonnet 5.5** | Best speed/intelligence balance — the default workhorse | $2 / $10 | 1M |
| **Haiku 5.5** | High-volume, latency-sensitive: classification, extraction, routing | from $0.10 / $0.50 | 128K |

**The exam-relevant rules, in order:**

1. **Start at the tier your eval says is sufficient**, not the biggest. The pattern "Sonnet for the bulk,
   escalate the hard 10–20% to Opus, Haiku for classification" is the standard answer.
2. **A model change is not a diagnosis.** If quality drops, find out whether it is retrieval, prompt,
   distribution shift or model behaviour *before* upgrading the tier.
3. **Cheaper tiers win on constrained tasks.** Classification into 12 labels, field extraction with a schema,
   routing — Haiku-class models are usually indistinguishable and 20–40× cheaper.
4. **Context size is not a goal.** Filling 1M tokens costs money and *lowers* accuracy (relevant signal gets
   diluted). Retrieve well, then send 5–30k tokens of genuinely relevant material.
5. **Cost is per token in *and* out.** Output is 5× input on every tier — verbose answers are the expensive
   kind. Constrain output length explicitly.

### Model-selection decision table

| Task shape | Start here | Escalate when |
|---|---|---|
| Classify / route / extract a fixed schema | Haiku | Ambiguous inputs, low-confidence band |
| Summarise, draft, answer from retrieved docs | Sonnet | Multi-document synthesis, regulated output |
| Multi-file code change, long tool loops | Opus | Still failing evals at higher effort |
| Novel research, hard maths, long-horizon planning | Fable | — |
| Anything with a hard p95 latency target | Haiku/Sonnet + caching | Never silently: renegotiate the SLA |

---

## 2. Prompt architecture

Treat the prompt as five layers with different owners and lifetimes:

```
┌─ 1. Role & objective        ── stable, one paragraph
├─ 2. Rules & constraints     ── stable, testable, numbered
├─ 3. Output contract         ── stable, schema-shaped
├─ 4. Examples (few-shot)     ── stable-ish, versioned with the prompt
└─ 5. Task input + retrieved  ── volatile, per request
```

Layers 1–4 form the **cacheable prefix**; layer 5 must come last. That ordering is not cosmetic — it is the
prompt-caching design (see §4).

### Rules that survive review

| Rule | Because |
|---|---|
| One instruction per line, numbered | The model can follow a list; prose blurs priorities |
| State the **output contract** explicitly (JSON keys, allowed values, max length) | Removes a whole class of format failures |
| Give **positive** instructions ("answer only from the provided excerpts") plus a fallback ("if the excerpts do not contain the answer, say INSUFFICIENT_CONTEXT") | Models comply better with a defined behaviour than a prohibition alone |
| Few-shot examples must include **hard negatives** (near-miss cases) | Examples teach boundaries, not just the happy path |
| Put **long documents before** the question | Recall is better when the query follows the material |
| Never put policy in the prompt if it must be *guaranteed* | A prompt is a request; code is a control |

### Zero-shot vs few-shot vs reasoning

| Situation | Use | Note |
|---|---|---|
| Common task, clear instructions | Zero-shot | Cheapest; test it before adding examples |
| Idiosyncratic format, house style, edge-case boundaries | Few-shot (2–5 examples) | Diminishing returns past ~5; every example costs tokens |
| Multi-step logic, arithmetic, ambiguity | Extended thinking / explicit reasoning step | Pay for thinking only where it changes the answer |
| Mechanical transformation | No thinking | Thinking on formatting tasks is pure cost |

---

## 3. Context engineering

Context engineering is **deciding what enters the window, in what order, and what gets evicted** — as a
deliberate budget.

### Budget template (adapt numbers, keep the discipline)

| Slice | Budget | Eviction order |
|---|---|---|
| System prompt + rules | 3k | Never (but version it) |
| Tool definitions | 2–6k | Drop unused tools first — biggest silent win |
| Retrieved evidence | 20k | Drop lowest-score chunks, never the top 3 |
| Conversation history | 10k | Summarise oldest turns → keep last 2 verbatim |
| Task input | 5k | — |
| Output reserve | 4k | Must always be reserved |

### Four techniques the exam expects you to name

1. **Retrieve-then-trim.** Fetch 20 candidates, rerank, send top 5. Sending 20 "just in case" costs 4× and
   usually *reduces* accuracy.
2. **Compaction / summarisation.** When history exceeds budget, summarise old turns into a running state block
   and keep the last exchange verbatim.
3. **Progressive disclosure.** Don't paste the whole schema/tool catalogue; let the model fetch the part it
   needs (tool search, sub-agent, or a lookup tool).
4. **Context isolation.** A sub-agent that reads 200 pages returns a 500-token summary, keeping the parent
   context clean. This is the strongest legitimate argument *for* multi-agent designs.

### Ordering and the "lost in the middle" effect

Long contexts are recalled best at the **beginning and end**. Practical rules:

- Stable instructions first, then evidence, then the **question last**.
- If a critical clause must be respected, repeat it in one line immediately before the question — cheap and
  effective.
- Never bury a hard constraint in the middle of a 100k-token dump and expect compliance.

---

## 4. Prompt caching (the highest-ROI feature on the exam)

Caching reuses a processed **prefix** so you don't pay full price to re-read it every request.

**Mechanics to know:**

- You mark **cache breakpoints** with `cache_control: {"type": "ephemeral"}` on a content block; caching applies
  to everything up to and including that block.
- Cache is a **prefix match**: any change earlier in the prompt invalidates everything after it. Tool
  definitions are part of the prefix — changing one tool invalidates the whole cache.
- Default TTL is short (5 minutes), extended with a 1-hour TTL at a higher write cost. A gap in traffic larger
  than the TTL means you pay the write again.
- Writes cost **more** than base input; reads cost **much less** (roughly 1.25× write / 0.1× read for 5-minute;
  2× for 1-hour — **verify**).
- There is a **minimum cacheable length**; short prompts can't be cached at all.

**Placement rule:** *stable → volatile.* Order the prompt so that everything shared by many requests sits
before the breakpoint and only the per-request input sits after it.

```python
system = [
    {"type": "text", "text": TOOL_AND_POLICY_TEXT,
     "cache_control": {"type": "ephemeral"}},   # breakpoint: shared prefix
]
messages = [{"role": "user", "content": f"<question>{q}</question>"}]   # volatile tail
```

**Economics** (`examples/d2_context_cost.py` computes this): reuse a 12k-token prefix across 500 requests and
input cost falls by roughly 85–90%. With one-shot or rare traffic, caching adds overhead and buys nothing.

**What caching is *not*:** it is not memory, not a semantic cache, and it does not help if your prompt changes
per request. If every request carries a different 20k document, put the *stable* material before the breakpoint
and accept that the document is uncached.

---

## 5. Modular prompts and Skills

As a system grows, one giant prompt becomes unmaintainable and un-cacheable. Two mechanisms:

| Mechanism | What it is | Use when |
|---|---|---|
| **Modular prompts** | Compose a prompt from versioned blocks (role, policy, format, examples) assembled per task | Several tasks share blocks; you need to A/B one block |
| **Skills** | Reusable packaged instructions/resources Claude loads for a specialised recurring task | The same procedure is needed across sessions/teams and should not be pasted into every request |

Both exist to solve the same problem: **instruction reuse without prompt bloat**. The exam framing is
"standardise recurring instructions so they don't live in every request", plus versioning and review.

Practical hygiene either way: prompt files in version control, a change log, and an eval run attached to every
prompt change. A prompt is code.

---

## 6. Worked examples

### E2.1 Choosing a tier (the item that looks trivial and isn't)

*"Extract 8 fields from 400k receipts/month; 99.5% of receipts are printed; a 2% field-error rate is
acceptable; p95 < 400 ms."*

Correct: **Haiku-class with a strict schema, plus a measured escalation path** for low-confidence/odd receipts
(handwritten, non-Latin script). Why not Opus: cost at 400k/month is ~25× for likely marginal accuracy on
printed receipts, and latency. Why not fine-tuning: you'd need labelled data and a retraining loop for a task a
schema + few-shot examples already solves.

### E2.2 Rewriting a weak system prompt

**Weak:**
```
You are a helpful assistant. Answer questions about our refund policy.
Be accurate and don't make things up. Use the documents provided.
```
Failures this causes: no output contract, no behaviour when evidence is missing, no length control, "helpful
assistant" invites general knowledge.

**Better:**
```
You answer refund questions for Acme's EU customers.

RULES
1. Use only the <policy> excerpts provided. Do not use prior knowledge.
2. If the excerpts do not answer the question, reply exactly: INSUFFICIENT_CONTEXT
3. Quote the clause ID for every factual claim, in the form [C-123].
4. If the customer's situation is ambiguous, ask one clarifying question instead of guessing.
5. Maximum 120 words.

OUTPUT
{
  "answer": string,
  "clauses": [string],
  "confidence": "high" | "low",
  "needs_human": boolean
}
```
Every rule is now **testable**: you can assert clause IDs exist, assert the exact fallback string, count words,
validate the JSON.

### E2.3 Few-shot with a hard negative

Two examples that both look like refunds but differ on the 30-day window teach the boundary; two happy-path
examples teach nothing. Include the near-miss deliberately:

```
<example>
<input>Bought 12 days ago, item arrived damaged.</input>
<output>{"decision":"refund","clause":"C-14"}</output>
</example>
<example>   <!-- near miss: outside window -->
<input>Bought 45 days ago, changed my mind.</input>
<output>{"decision":"decline","clause":"C-09"}</output>
</example>
```

### E2.4 Caching breakpoint placement

400-page handbook + per-user question, 50k requests/month:

- **Wrong:** handbook and question in one user message. Nothing is reusable → no cache hits.
- **Right:** `system = [role+rules+handbook]` with a breakpoint; per-request question in `messages`. Now the
  handbook is written once per TTL window and read at ~10% price thereafter.
- **Also wrong here:** putting the whole 400-page handbook in the window at all. Retrieve the 6 relevant pages
  and *then* cache the stable policy + format block. Caching reduces the price of a mistake; it doesn't fix it.

### E2.5 Context budget for a long conversation

A support session has grown to 90k tokens of history, and quality is degrading. Correct sequence:
summarise turns older than the last 3 into a structured state block ("customer, order, issue, commitments,
open questions"), keep the last exchange verbatim, drop resolved sub-threads. Then measure. Cutting the system
prompt or upgrading the model are both wrong first moves.

### E2.6 Structured output, enforced

```python
tool = {
  "name": "record_decision",
  "description": "Record the refund decision. Call exactly once.",
  "input_schema": {
    "type": "object",
    "properties": {
      "decision": {"type": "string", "enum": ["refund", "decline", "escalate"]},
      "clause":   {"type": "string", "pattern": "^C-[0-9]{2,3}$"},
      "reason":   {"type": "string", "maxLength": 240},
    },
    "required": ["decision", "clause", "reason"],
    "additionalProperties": False,
  },
  "strict": True,          # schema conformance, not a polite request
}
```
Then **still validate server-side**: schema-valid is not policy-valid. Bounded repair (≤2 attempts) then
fallback to a human queue. Never an infinite "please fix the JSON" loop.

### E2.7 Thinking/effort: where it pays

Turn on extended thinking for: multi-constraint planning, ambiguous policy application, maths, and code
changes spanning files. Leave it off for: classification, extraction, formatting, rewriting. Measure
**accuracy gain per extra 1k thinking tokens**; if the curve is flat, you are buying latency.

---

## 7. Traps

1. **"Use the largest model"** as a first response to a quality complaint.
2. **Caching a prompt that changes every request** — writes with no reads.
3. **Changing one tool definition** while expecting cache hits (prefix invalidation).
4. **Stuffing 200k tokens "for safety"** — cost up, accuracy often down.
5. **Prompt instructions standing in for a hard control** ("never reveal PII").
6. **Few-shot examples with no hard negatives**, then wondering why edge cases fail.
7. **Fine-tuning to add facts** — that is retrieval's job and fine-tuning won't hold facts reliably.
8. **Ignoring output tokens** in cost models when output is 5× input price.

---

## 8. Practice questions

**Q1.** A support assistant answers from a 12k-token policy + brand guide, identical for every request. Traffic
is ~50k requests/month, spread evenly. Where does the cache breakpoint go, and why?

- A. On the user's question, so each question is cached
- B. After the policy + brand guide, with the user's question last
- C. On the tool definitions only
- D. Caching is inappropriate because questions differ

**Answer: B.** The cache is a prefix match, so the breakpoint must sit after the *shared* material and before the
per-request material. A caches the thing that never repeats. C caches only the small tool block and leaves 12k
tokens of policy uncached. D confuses caching with a semantic answer cache: the *prefix* is identical across all
50k requests even though the tail differs.

---

**Q2.** A document Q&A system's accuracy fell after the team raised top-k from 5 to 25 chunks "to be safe".
Latency and cost rose 40%. What is the most likely cause and the best first fix?

- A. The model is too small; move up a tier
- B. Irrelevant chunks dilute attention and push relevant evidence into the middle of a long context; rerank and
  send fewer, better chunks
- C. The context window is overflowing; increase max_tokens
- D. Prompt caching is misconfigured

**Answer: B.** More context is not more evidence: precision matters, and recall is weakest in the middle of long
inputs. Rerank then send the best 5–8, keep the question last. A is unmeasured escalation. C confuses input
window with output budget. D is a cost story, not an accuracy story.

---

**Q3.** 400k receipts/month, 8 fields, 2% field-error tolerance, p95 400 ms, 99.5% printed. Which approach?

- A. Opus-class model with thinking enabled, one call per receipt
- B. Haiku-class model with a strict schema + few-shot, escalating low-confidence receipts to a stronger tier
- C. Fine-tune a model on historical receipts
- D. Batch all receipts nightly through the largest model

**Answer: B.** Volume + latency + a modest accuracy bar point to the cheap tier with a constrained output
contract, and an evidence-based escalation path for the hard 0.5%. A is ~25× cost with thinking latency and no
stated benefit. C needs labelled data and retraining for a task a schema solves. D breaks the latency target
entirely and is the most expensive option.

---

**Q4.** Which change is most likely to *invalidate* an existing prompt cache?

- A. Editing the user's question
- B. Adding a new tool to the `tools` array
- C. Changing `max_tokens`
- D. Increasing the number of retrieved chunks appended after the cached block

**Answer: B.** Tools are part of the cached prefix; changing them changes everything after. A and D affect only
the volatile tail. C is an output parameter and does not touch the prefix at all.

---

**Q5.** A team's prompt is 4,000 tokens of accumulated instructions after two years of patches, and every change
breaks something else. Best structural fix?

- A. Move everything into one longer, more emphatic prompt
- B. Split into versioned modular blocks, attach eval cases to each block, and only send the blocks the task needs
- C. Fine-tune on the prompt's examples to remove the need for instructions
- D. Switch to the largest model so the instructions are followed more reliably

**Answer: B.** The problem is maintainability and coupling, not model capability. Modular, versioned blocks with
per-block evals let you change one thing and prove it. A increases coupling. C cannot guarantee policy
compliance. D treats a maintenance defect as a capability defect.

---

## 9. 60-second recall

- Tier ladder: Haiku → Sonnet → Opus → Fable. Start where your eval passes, escalate the hard slice.
- Output is ~5× input price; constrain length.
- Prompt layers: role → rules → output contract → examples → volatile input. Cacheable prefix first.
- Cache = prefix match + `cache_control` breakpoint; stable→volatile; TTL gaps cost a rewrite; tools are in the
  prefix.
- Context budget: reserve output, cap tools, rerank then trim, summarise history, disclose progressively, isolate
  with sub-agents.
- Question last. Critical constraints repeated near the question.
- Prompts are code: versioned, reviewed, eval-gated.
