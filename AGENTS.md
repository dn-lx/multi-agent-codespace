# Multi-agent Codespace rules

This repository provisions independent coding tools and a human-led, usage-aware routing workflow. It can recommend task/model assignments; it does not silently invoke providers, merge accounts, or integrate changes without review.

## Separate agent hosts
- Claude Code (`claude`), Codex (`codex`), Antigravity (`agy`) and GitHub Copilot CLI (`copilot`) run independently.
- OmniRoute (`omniroute`) is an optional API gateway, not an agent account or subscription.
- Never merge subscription credentials, impersonate another provider or silently call an agent from another agent.
- Check recent local quota snapshots with `agent-usage availability` and request a host/model-class suggestion with `agent-route recommend --task-class <class> --current <host>` from any Codespace worktree. Snapshots are manually entered from each provider's native usage view.
- Prefer the current host if its fresh quota is competitive. If quota is stale or unknown, check the native provider view; never guess or silently switch to API/credit billing.
- Paid/API/credit routing is opt-in. Keep OmniRoute disabled until a separate budget and provider policy have been reviewed.
- Use `scripts/project.sh add <repository>` to create separate Claude, Codex, Antigravity, and Copilot Git worktrees. Make code changes only in your assigned worktree.
- The environment repository itself should contain only setup, diagnostics, launchers and instructions.
- If two agents work on the same product, coordinate with Git commits and reviewed pull requests, **not** by editing the same dirty directory.

## Required safeguards
- Inspect a project's `AGENTS.md`, `CLAUDE.md` and equivalent instructions before touching its code.
- Never print, copy, commit, or transmit access tokens, cookies, keys or other secrets.
- Never change a protected `main`/`master`/`prod` branch directly or deploy production without explicit approval.
- Prefer the target project's integration branch (`dev` if present), create feature branches, run appropriate tests, review the diff and summarize remaining failures.
- Never bypass approvals, disable security checks, or auto-approve tool execution just to accelerate coding.
- Don't change another agent's branch/worktree or delete preserved historical work.
- A running terminal/tmux session can outlive a browser tab, but not a stopped or rebuilt Codespace.

## Handoffs
Record completed changes and test commands in the relevant project's commits/PRs. For cross-agent review, ask a different agent to inspect the diff in **its own clean worktree** before applying any suggested edits. The user chooses when to launch each agent.

Use one lead agent by default, then add a reviewer or parallel contributor only for a distinct bounded task. Follow [docs/WORKFLOW-AND-USAGE.md](docs/WORKFLOW-AND-USAGE.md) for usage-aware host/model recommendations, task packets, review handoffs, and private usage snapshots. Provider plans and API/credit billing remain separate; never report the local ledger as a combined quota.
