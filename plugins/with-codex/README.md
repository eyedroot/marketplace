# with-codex

- Workflow plugin that wraps Claude's primary pass and Codex's cross-verification under one slash command
- A single `/with-codex <prompt>` runs the primary work and auto-routes into Codex review or rescue as needed
- Designed for environments where the `openai-codex` marketplace plugin (`/codex:rescue`, `/codex:review`) is already installed

## Included command

- `/with-codex`
  - Primary — Claude executes the user prompt as usual
  - Branch A — when the primary pass gets stuck or uncertain, delegate to `/codex:rescue` for deeper investigation
  - Branch B — when the primary pass finishes cleanly, hand the result to `/codex:review` for an independent second opinion
  - Branch C — reconcile Claude and Codex conclusions, flag agreements and disagreements explicitly
  - Flags — `--rescue-only` or `--review-only` to run a single branch

## Prerequisites

- The [openai-codex plugin](https://github.com/openai/codex) installed in Claude Code
  - `/codex:rescue` and `/codex:review` must be available
- Codex CLI authenticated (run `/codex:setup` if needed)

## Install

```bash
/plugin marketplace add eyedroot/eyedroot-marketplace
/plugin install with-codex@eyedroot
```

## Usage examples

```
/with-codex Review this migration script for downtime risk
/with-codex --review-only Cross-check the PR I just pushed
/with-codex --rescue-only I can't track down the source of this NullPointerException
```

## License

- MIT
