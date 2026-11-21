# Tandem workflow and usage tracking

This Codespace provides three separate provider tools. It is a shared workspace with isolated Git worktrees, not an automatic agent orchestrator. You decide which CLI runs and when. Each account and subscription stays with its provider; quotas and credentials cannot be combined.

## A practical tandem loop

Use one agent as the task owner and bring the others in for distinct, bounded work. A reliable default is:

1. **You define the task.** Keep one canonical brief with the goal, repository and base branch, allowed paths, constraints, acceptance criteria, and relevant commands.
2. **One CLI implements.** Choose Claude Code, Codex, or Antigravity based on availability, fit, and remaining allowance. Work only in that agent's worktree and branch.
3. **A second CLI reviews independently.** Give it the brief, diff, and acceptance criteria. Ask for findings with file and line references, severity, and a concrete fix. Do not ask it to edit the implementer's worktree. It can review read-only or make a proposed fix in its own worktree.
4. **The owner triages.** The implementing agent or you decide which findings are valid, apply fixes in the implementation branch, and explain rejected findings.
5. **You verify and integrate.** Inspect the final diff, run the project's requested checks, then open and merge a PR when ready. Agents do not merge or deploy by default.
6. **Use the third CLI selectively.** Bring it in for a genuinely separate task (for example docs while implementation proceeds), a difficult disagreement, or a final independent review. Keep concurrent agents to work that can be separated cleanly.

A starting role rotation is Claude for implementation, Codex for adversarial review, and Antigravity for an alternate design or a parallel documentation task. This is only a starting heuristic. Rotate the lead and reviewer as you learn which tool works best for your repository, task, and available quota. Do not send the same full task to all three just to consume their allowances.

### Task brief template

Copy this into an issue, PR, or handoff note and fill it in:

```text
Goal:
Repository and base branch:
Implementation branch/worktree:
Allowed paths:
Constraints and relevant instructions:
Acceptance criteria:
Checks to run:
Out of scope:
```

### Review handoff template

```text
Review this diff against the task brief and acceptance criteria.
Do not edit files. Return only actionable findings, sorted by severity.
For each finding include: severity, file and line, impact, and a suggested fix.
If you find no issues, say so and note any checks you could not run.
```

Keep the task brief and review results in an issue/PR or a short handoff note. Avoid putting secrets, private prompts, or full agent transcripts in the repository.

## Separate worktrees, shared project

Create the project worktrees once with `scripts/project.sh add`. Run each CLI from its own worktree with `scripts/agent.sh`. Before switching tasks, inspect `scripts/project.sh status <name>` and Git status in each worktree. An agent must not edit another worktree's files. Pass changes through Git commits, cherry-picks, or PRs so each handoff is reviewable. Keep the integration branch clean and merge only after you approve the result.

An agent can see files and run commands in its Codespace, so give it the smallest useful scope. Review shell commands and generated changes as you would from a human contributor.

## Monitor usage without mixing accounts

The ledger in `scripts/usage.py` records only summaries you enter: agent, project, task label, model, billing source, minutes, and optional provider-reported USD. It stores a CSV under `~/.local/share/multi-agent-codespace/usage.csv` on the Codespace, outside Git. It does not call provider APIs or inspect accounts. Enter only usage you can verify; leave cost blank when the provider does not report a comparable amount.

Examples:

```bash
python3 scripts/usage.py add --agent claude --project my-project --task issue-42 \
  --model sonnet --billing subscription --minutes 35

python3 scripts/usage.py add --agent codex --project my-project --task issue-42 \
  --model gpt-5-codex --billing subscription --minutes 18

python3 scripts/usage.py add --agent antigravity --project my-project --task issue-42 \
  --model gemini --billing credits --minutes 12 --cost-usd 0.20

python3 scripts/usage.py summary --month 2026-11
python3 scripts/usage.py path
```

Log one row when a useful work session ends. Minutes measure your own active session time, not model runtime or provider quota consumption. Do not enter a guessed dollar value. The monthly report groups your entries by agent and billing source; it cannot compare unlike subscription quotas or compute a combined plan balance.

### Check each provider's own limit

Use the provider's own CLI or account page for authoritative remaining quota. Exact commands and account pages can change with CLI versions and plan types.

- **Claude Code:** run `/usage` in an interactive Claude Code session to see plan usage and activity. `/cost` reports API session cost when using API billing; it is not the same as subscription quota. [Claude cost and usage docs](https://code.claude.com/docs/en/costs)
- **Codex:** run `/status` in the Codex CLI to inspect the current session/account context. Check the Codex usage page in ChatGPT settings for plan limits where available. API-key use is billed separately from a ChatGPT plan. [Codex plans and pricing](https://developers.openai.com/codex/pricing)
- **Antigravity:** run `/usage` (or `/quota`, if available in your CLI version) to refresh and view model quotas. Models may share rolling quota windows. Check `/settings` or `/config` before enabling AI credits for overage. [Antigravity usage](https://antigravity.google/docs/cli/commands/usage/) · [plans](https://antigravity.google/docs/plans/) · [credits](https://antigravity.google/docs/cli/credits/)

For each tool, distinguish included plan usage from API billing or optional credits. Keep API keys private and do not copy credentials between CLIs.

## Keep the workflow sustainable

- Start with one lead agent. Add a reviewer when the risk or value justifies the extra context and quota.
- Give each agent the same short task brief and only the context needed for its role. Give the reviewer the actual diff.
- Ask for focused outputs: a patch, a review list, or a decision with evidence. Stop idle sessions and close work you are not using.
- Record a monthly checkpoint from provider usage pages and your local ledger. Compare trends by provider and billing source, not a blended “remaining quota.”
- Treat Codespaces compute and storage as a separate cost from provider plans. Stop the Codespace when it is not needed; tmux sessions do not survive a stop or rebuild.
- Antigravity may offer optional credit-based overage. Leave it disabled unless you deliberately want additional usage billed to those credits.

The goal is dependable review with the least parallel work that answers the task. More simultaneous sessions do not mean faster delivery when they compete over the same design or files.
