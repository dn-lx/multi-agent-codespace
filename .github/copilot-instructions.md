# GitHub Copilot instructions

Follow the shared cross-agent rules in `AGENTS.md`. Before recommending another provider or model, inspect `agent-usage availability` and use `agent-route recommend --task-class <class> --current copilot`. Quota snapshots are manual and provider-specific. Keep one lead agent by default, isolate writers in separate worktrees, assign bounded task packets, and require deterministic checks plus independent review for high-risk changes. Never auto-select paid/API routes or merge/deploy without human review.
