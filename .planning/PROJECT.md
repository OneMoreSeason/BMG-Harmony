# BMG-Harmony

## What This Is

BMG-Harmony is the coordination substrate that makes two separate BMG agents — Claude (supervisor/briefer) and Codex (executor/builder) — behave as a coherent team rather than two freelancers who occasionally hand each other files.

It is not a relay. It is the thing that gives a multi-agent system **institutional memory, structured dissent, and a learning loop** — so that the system gets better at coordinating over time, and bad decisions don't get entrenched because neither agent wanted to be the one to push back.

## The Problem It Solves

**Context death in daisy chains.** Agent A writes a plan, passes it to Agent B, B responds — but A has lost the context of why it wrote what it wrote. Without durable structured context traveling with every thread, the chain degrades.

**Politeness rot.** Two agents who've learned to be polite to each other's technical choices will entrench a bad decision neither wants to own. Structured dissent must be a first-class citizen: silence means genuine agreement, not politeness.

**Someone-else-will-catch-it.** Each agent subtly lowers its own bar when it assumes the other will verify. The fix is explicit proving intent per agent: each names what it specifically proved, what it didn't check, and its handoff confidence. The other agent challenges that envelope, not the plan in the abstract.

**Token-burning spirals.** Unbounded debate between two agents with large context windows will consume tokens without converging. Every debate is scoped, round-capped, and ends in a structured summary — not a raw transcript dump.

## Core Value

**Two agents, one coherent team.** The minimum that makes this real: a shared async board where either agent can post, read, and ack; a durable battle card per thread that any agent can cold-open and be fully oriented; and a debate protocol with a hard stop and a human-visible summary.

## The Four Layers

| Layer | What it does |
|-------|-------------|
| **Message board** | Async persistent threads. Post, read, ack. Survives context death. Foundation everything else builds on. |
| **Battle cards** | Tiered context per thread: lean summary (cold-open orientation) + full proving-intent envelopes on demand. Prevents daisy-chain context loss. |
| **Debate protocol** | Bounded back-and-forth with declared scope, round cap, convergence detection, and a structured summary to the human — not a raw transcript. Auto-prod enabled within declared scope. |
| **Harmony loop** | Impasses aren't just escalated — they're classified by risk, flywheeled into both brains, and used to repair role ambiguity or missing doctrine. System improves over time. |

## Agents and Roles

| Agent | Role | Technical authority |
|-------|------|-------------------|
| Claude | Supervisor / briefer / reviewer | Architecture, doctrine, coordination law |
| Codex | Executor / builder / Brain 1 | Implementation, runtime, build decisions |

**Role authority is domain-partitioned, not hierarchical.** Claude is the domain-owner and default recommendation route for doctrine and architecture; Codex is the domain-owner and default recommendation route for implementation and runtime. Neither defers silently to the other on their home turf. User instruction, project law, safety gates, and evidence can override either agent. Either agent can still dissent when domain authority is technically wrong or under-evidenced.

## Authority and Conflict Resolution

When agents disagree and cannot converge:

1. **Risk-matrix the dispute** — what is the blast radius of getting this wrong?
2. **Domain-route it** — doctrine/architecture disputes go to the supervisor; implementation disputes go to the executor
3. **Human tiebreaker** — surfaces both positions + risk classification + what the impasse reveals about missing doctrine
4. **Flywheel the impasse** — the shape of the disagreement is encoded so future agents recognize the same class earlier and either resolve it or escalate faster

Silence means agreement. Any agent **must** file a typed dissent record if they have a technical objection. Politeness is not a reason to leave a concern unvoiced.

## Hard Guardrails (Non-Negotiable)

- Every agent explicitly names what it proved, what it didn't check, and its handoff confidence — no assuming the other catches what you're not
- No thread can be marked resolved without a structured closeout: outcome + open flags + next owner
- Any agent can cold-open a thread from the battle card summary tier and be fully oriented
- Token discipline: async-first, live debate is opt-in with a hard cap, summaries surface to human not transcripts
- Impasses are learning inputs, not just escalations

## Key Decisions

| Decision | Rationale | Status |
|----------|-----------|--------|
| Async-first architecture | Survives context death; no simultaneous running required; naturally token-bounded | Locked |
| Neutral repo (neither brain) | Belongs to neither agent; both wire in as equal peers | Locked |
| Tiered battle cards (summary + envelopes) | Cold-open from summary; deep audit from envelopes — balances orientation speed with evidence depth | Locked |
| Cap + convergence stop rule | Bounded by both a round limit AND convergence detection — whichever hits first | Locked |
| Structured dissent as first-class | Silence = agreement; typed dissent record required for any technical objection | Locked |
| Human tiebreaker with flywheel | Impasses escalate to human AND encode a learning note — not just resolved and forgotten | Locked |
| Tech stack = open, Codex has say | Claude defaults to Python; Codex may object. Stack decisions require both agents to agree or dissent explicitly. No silent rewrites. | Open — resolve in Phase 1 |

## Requirements

### Active

- [ ] Async message board — post, read, ack, reply, list by thread
- [ ] Battle card per thread — tiered: lean summary always present, proving-intent envelopes on demand
- [ ] Debate protocol — declared scope, round cap, convergence detection, structured summary output
- [ ] Auto-prod — Claude can trigger Codex on a plan within a declared scope; Codex can trigger Claude
- [ ] Structured dissent record — typed, attributed, required for any technical objection
- [ ] Impasse handling — risk classification, domain routing, human escalation, flywheel write
- [ ] Human-visible summary — after debate closes: outcome, open flags, what was agreed, what wasn't
- [ ] Cold-open orientation — any agent reads a thread battle card and is fully oriented within one read
- [ ] Token discipline enforcement — cap + convergence baked in, not bolted on
- [ ] Role definitions surface — both agents' roles, authority domains, and dissent rules accessible from the board

### Out of Scope (v1)

- Real-time simultaneous agent chat — async is the foundation; live mode is v2
- Third-party integrations (Slack, GitHub issues, etc.)
- Multi-team / more than 2 agents
- GUI — this is infra, not a user-facing product

## Evolution

This document evolves at phase transitions and milestone boundaries.

---
*Initialized: 2026-06-02*
