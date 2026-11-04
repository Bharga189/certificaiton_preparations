# 07 · Developer Productivity & Operational Enablement — 7%

> **What this domain really tests:** can you roll Claude tooling out to a team so that it is *safe by
> configuration* rather than safe by good intentions?

Smallest domain (7%) — do not over-invest. One afternoon on settings precedence, permission rules, marketplaces
and a sane delivery loop is enough, plus the operational-debugging habits.

---

## 1. Configuration layers and precedence

Claude Code reads settings from several places. The exam cares about one property: **some layers cannot be
overridden.**

```
1. Server-managed settings (admin console)   ← highest authority, cannot be overridden
2. Command-line arguments
3. Local project settings   (.claude/settings.local.json)   ← git-ignored, personal
4. Shared project settings  (.claude/settings.json)         ← committed, team-wide
5. User settings            (~/.claude/settings.json)       ← personal, all projects
```

| Goal | Correct mechanism |
|---|---|
| Enforce a policy developers cannot bypass | **Server-managed settings** |
| Share conventions across a repo | Shared project settings (committed) |
| Personal preferences | User settings |
| Temporary per-machine override | Local project settings |
| Distribute approved skills/agents/hooks/MCP servers | **Managed plugin marketplace** |
| Prevent secrets from entering context | Permission deny rules + a PreToolUse hook |

**The canonical item:** "enforce security settings developers cannot override while distributing approved
tools" → **managed settings + managed marketplace**. Not "a shared repo of recommended settings", not "audit
local configs periodically", not "project-level config teams can edit". Those are recommendations, not controls.

`examples/d7_team_setup.py` implements the precedence and asserts that a lower layer changes nothing.

---

## 2. Permissions and hooks

### Permission rules

- `allow` / `ask` / `deny`, evaluated with **deny taking precedence over allow**.
- Default for anything unmatched should be **ask**, not allow.
- Deny by pattern, and include the ones people forget: `.env*`, `secrets/*`, `*.pem`, `*.key`, `id_rsa*`,
  `*credentials*`.
- Scope Bash narrowly (`Bash(git:*)`, `Bash(npm test)`), never a blanket shell.
- Treat MCP tool permissions the same way as local tools; a remote tool is still a capability.

```jsonc
{
  "permissions": {
    "deny":  ["Read(./.env*)", "Read(./secrets/*)", "Bash(curl:*)", "Bash(rm -rf:*)"],
    "allow": ["Read(./src/**)", "Bash(git:*)", "Bash(npm test)"]
  }
}
```

### Hooks

A `PreToolUse` hook is the deterministic layer: it can **block** a tool call before it happens (e.g. any read of
a secret path, any write outside the repo). Rules that matter:

- **Block, don't warn.** A warning is a log line nobody reads.
- Keep hooks small and testable; a broken hook must fail closed.
- Log the block for tuning, and review false positives.
- Hooks are configuration, so they belong in managed settings or the reviewed project file — not in someone's
  dotfiles.

### Secrets hygiene for teams

| Do | Don't |
|---|---|
| Keep keys in `.env`, denied by permission rules | Paste keys into `CLAUDE.md` or a prompt |
| Use a hook that blocks secret-path reads | Rely on the model "knowing" not to print them |
| Rotate anything that entered a transcript | Assume a deleted message is gone |
| Scope MCP server credentials per user | Share one service token across the team |

---

## 3. Project memory without leaking

A committed project memory file (`CLAUDE.md`) is the cheap, high-leverage convention: build/test commands,
architecture map, style rules, "never do this" list, and where the docs live.

Good content: commands, conventions, gotchas, owners, links.
Bad content: credentials, customer data, internal hostnames with embedded tokens, anything that would embarrass
you in a public repo. **Assume every committed file is public.**

Keep it short. A 2,000-line memory file competes with the actual task for context and rots quietly; review it
quarterly like code.

---

## 4. A defensible AI-assisted delivery loop

| Phase | Assistant does | Control |
|---|---|---|
| **Explore** | Reads code, maps dependencies, summarises | Read-only tools |
| **Plan** | Proposes a change plan / diff outline | Human approves the plan |
| **Implement** | Edits in a branch, writes tests | Tests + review; never straight to main |
| **Verify** | Runs tests, lint, typecheck | Environment decides; not the model's opinion |
| **Document** | Updates docs/changelog | Reviewed like code |

**Out of scope for the assistant** (say this in the policy): rotating production credentials, applying
migrations to production, pushing to main unreviewed, pasting customer data into a prompt.

### Measuring whether it helped

| Metric | Why |
|---|---|
| Lead time / cycle time | The outcome that matters |
| PR review comments per PR | Quality of first draft |
| Test coverage delta | Did it add tests or just code? |
| Revert rate | Did it ship breakage? |
| Escaped defects | The honest quality signal |
| Developer-reported friction | Adoption |

An adoption number without a quality number is a vanity metric.

---

## 5. Operational debugging with Claude

A discipline that transfers to any incident:

1. **State the symptom precisely** — what, since when, for whom, what changed.
2. **Give evidence, not conclusions** — logs, error text, metrics, recent diffs.
3. **Ask for hypotheses ranked by likelihood, each with a discriminating test.** This is the highest-value
   prompt shape in operations.
4. **Change one thing at a time** and record the result.
5. **Redact** before pasting: no PII, no credentials, no customer identifiers. Use synthetic reproductions.
6. **Verify in the environment** — a plausible explanation is not a fix.

Prompt shape that works:

```
Symptom: p95 latency 4.2s (was 1.1s) since 14:20 UTC, all tenants.
Evidence: <redacted APM histogram>, <error counts by endpoint>, <deploy diff 14:05>
Constraints: cannot roll back (migration applied); read-only access to prod.
Ask: 5 ranked hypotheses, and for each, the cheapest observation that would
     confirm or eliminate it. Do not propose a fix until a hypothesis is confirmed.
```

---

## 6. Worked examples

### E7.1 The rollout item (answered in full)

*"Standardise Claude Code across teams; enforce security settings developers cannot override; distribute
approved tools and reusable workflows. Select TWO."*

**Correct:** (1) server-managed settings for organisation-wide controls that cannot be overridden; (2) a managed
plugin marketplace for approved skills/agents/hooks/MCP servers.

**Why the others fail:**

| Option | Failure |
|---|---|
| Let developers install tools, audit later | Detect-after-the-fact; drift is already in place |
| Publish recommended settings in a repo | Recommended ≠ enforced; project files are editable |
| Store approved tools in project config | Teams can disable them; not organisation-wide |

The design principle: **separate policy enforcement (managed settings) from capability distribution (managed
marketplace).** Both are server-side, both are reviewable.

### E7.2 A good `CLAUDE.md` skeleton

```markdown
# Project: billing-service

## Commands
- test: `npm test -- --runInBand`
- lint: `npm run lint -- --max-warnings 0`
- typecheck: `npx tsc --noEmit`

## Architecture
- `src/api` HTTP handlers only; no business logic
- `src/domain` pure functions, fully unit-tested
- `src/db` migrations are append-only; never edit a shipped migration

## Rules
- Never read `.env*` or `secrets/` (denied by policy).
- Do not add dependencies without an ADR.
- Every bug fix includes a regression test.

## Where things live
- Runbook: `docs/runbook.md`   ADRs: `docs/adr/`
```

### E7.3 Blocking secrets deterministically

A `PreToolUse` hook matching `.env*`, `*.pem`, `*.key`, `id_rsa*`, `*credentials*` returns **block**. This is the
control; the prompt telling the model to be careful is the backup. `examples/d7_team_setup.py` asserts block/allow
for each path.

### E7.4 Onboarding a new engineer

Deliver: managed settings already in place, marketplace configured, `CLAUDE.md` committed, hooks installed, a
10-minute walkthrough, and a first task that exercises explore → plan → implement → verify. Success criterion:
they complete a small change without asking where anything is.

### E7.5 The incident that must not use production data

Customer reports wrong invoice totals. Correct: reproduce with synthetic data, share the code path and the
redacted inputs, and let the assistant propose hypotheses. Pasting the customer's real invoice into a chat is a
data incident, not a debugging step.

---

## 8. Traps

1. Thinking a committed settings file is a control (it is a suggestion developers can edit).
2. Project-level config used for organisation-wide enforcement.
3. Audit-after-the-fact instead of enforce-up-front.
4. `allow`-by-default permission policies.
5. Secrets in `CLAUDE.md`, prompts, or MCP config files.
6. Warning hooks that nobody reads.
7. One shared MCP credential for the whole team.
8. Measuring adoption (sessions, suggestions accepted) without quality or cycle-time outcomes.
9. Pasting production PII into a debugging session.
10. Unreviewed agent commits to main.

---

## 9. Practice questions

**Q1.** An organisation must enforce Claude Code security settings that developers cannot override and centrally
distribute approved skills, agents, hooks and MCP servers. Select TWO.

- A. Establish a managed plugin marketplace for approved extensions
- B. Let developers install tools and audit local configs quarterly
- C. Use server-managed settings to enforce organisation-wide controls that lower layers cannot override
- D. Publish recommended settings in a shared repo for teams to apply
- E. Put approved tools in project-level config so teams can update them

**Answer: A and C.** Managed settings are the highest-precedence layer, so policy cannot be overridden; a managed
marketplace is the controlled distribution channel for capabilities. B and D are retrospective/recommended, not
enforced. E is editable per team, which is precisely the drift the requirement forbids.

---

**Q2.** A developer's user settings allow `Read(./*)`, and managed settings deny `Read(./.env)`. What happens?

- A. The read is allowed, because the developer explicitly allowed it
- B. The read is denied, because managed settings outrank user settings and deny beats allow
- C. The read is allowed with a warning
- D. Behaviour depends on which file was loaded last

**Answer: B.** Precedence puts managed settings above user settings, and within a permission set deny wins. The
requirement "developers cannot override" is exactly this property.

---

**Q3.** Which is the most effective control against secrets appearing in an AI coding session?

- A. Instructing the model in `CLAUDE.md` not to read `.env`
- B. Deny permission rules on secret paths plus a PreToolUse hook that blocks them
- C. Reviewing transcripts weekly
- D. Rotating keys monthly

**Answer: B.** Deterministic prevention at two layers. A is a request in the same context as the task. C is
detection after exposure. D limits the damage but not the exposure.

---

**Q4.** Which assistant workflow is appropriate for a production incident?

- A. Give the assistant read access to prod DB and let it query freely
- B. Provide redacted logs, metrics and the recent diff; ask for ranked hypotheses with discriminating tests;
  verify in the environment
- C. Paste the customer's record so it has full context
- D. Have it apply the most likely fix immediately to shorten MTTR

**Answer: B.** Evidence plus ranked hypotheses plus verification is the disciplined loop, and redaction keeps the
data boundary. A grants unnecessary capability; C is a data incident; D changes production on an unconfirmed
hypothesis.

---

**Q5.** Which metric best shows whether AI-assisted development actually helped?

- A. Number of suggestions accepted
- B. Session count per developer
- C. Cycle time and revert rate, with test coverage delta
- D. Tokens consumed per week

**Answer: C.** Those measure delivery outcome and quality together. A and B measure activity and are easy to
inflate. D measures cost without value.

---

**Q6.** A team wants each developer to be able to tweak model choice locally, while the organisation pins the
model for compliance. Which configuration achieves both?

- A. Delete user settings files
- B. Set the model in managed settings; developers may vary anything not defined there
- C. Put the model in project settings only
- D. Ask developers to follow a wiki page

**Answer: B.** Managed settings define the enforced values; everything undefined remains overridable by lower
layers. A is heavy-handed and unnecessary; C is editable; D is not enforcement.

---

## 10. 60-second recall

- Precedence: managed > CLI > local project > shared project > user. Managed cannot be overridden.
- Enforce policy in managed settings; distribute capability via a managed marketplace. Two separate concerns.
- Permissions: deny > allow > ask. Scope Bash narrowly; deny secret paths.
- Hooks block (not warn) and fail closed.
- `CLAUDE.md`: commands, architecture, rules, links — never secrets. Assume it is public.
- Delivery loop: explore → plan → implement → verify → document; environment verifies; never main unreviewed.
- Ops: symptom + evidence + ranked hypotheses + one change at a time, with redaction.
- Measure cycle time and revert rate, not suggestion counts.
