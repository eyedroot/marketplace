---
description: Dual-agent workflow where Claude does the first pass and Codex cross-verifies
argument-hint: "<prompt to execute>"
allowed-tools: Read, Edit, Write, Glob, Grep, Bash, AskUserQuestion, Agent, Skill, TodoWrite
---

A dual-verification workflow where Claude (primary) and Codex (secondary) collaborate.

User prompt:
$ARGUMENTS

## Execution flow

Primary pass — Claude does the work directly
- Carry out the user prompt as usual.
- Apply whatever fits the task: writing code, editing, analysis, review, etc.

Branching — at the end of the primary pass (or mid-way), pick one:

A. Stuck or uncertain → `/codex:rescue`
- Trigger: a decision you can't justify, a bug you can't reproduce, a weakly grounded assumption, a design choice that needs an alternative opinion.
- Call: invoke `Skill(codex:rescue)` and hand off the context that matters (file paths, line numbers, the specific question).
- Fold Codex's findings into your work, then continue to step C if the answer conflicts with what you had.

B. Primary pass finished cleanly → `/codex:review`
- Trigger: the work is done — there's a concrete artifact (changed code, analysis, conclusion).
- Call: invoke `Skill(codex:review)` to have Codex independently review the same scope.
- Compare both agents' findings and report where they agree and disagree.

C. Reconciliation (always after `/codex:review`, or after `/codex:rescue` if it contradicts the primary pass)
- Put Claude's and Codex's conclusions side by side.
- Mark agreement points as high confidence.
- For disagreements, lay out each agent's reasoning and present which side looks stronger, with justification.
- Use `AskUserQuestion` for anything that needs the user to break the tie.

## Operating rules

- Never skip the primary Claude pass. This is not a "send it to Codex first" workflow.
- A and B are not exclusive: rescue mid-pass and review at the end is a valid sequence.
- Don't relay Codex's output verbatim — always state how it differs from the primary result.
- End every run with three labeled sections: (1) primary result, (2) Codex result, (3) agreements and disagreements.
- If the user explicitly passes `--rescue-only` or `--review-only`, run only that branch.
