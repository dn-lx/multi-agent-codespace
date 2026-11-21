# Tandem workflow and usage tracking

This Codespace provides three separate provider tools. It is a shared workspace with isolated Git worktrees, not an automatic agent orchestrator. You decide which CLI runs and when. Each account and subscription stays with its provider; quotas and credentials cannot be combined.

## A practical tandem loop

Use one agent as the task owner and bring the others in for distinct, bounded work. A reliable default is:

1. **You define the task.** Keep one canonical brief with the goal, repository and base branch, allowed paths, constraints, acceptance criteria, and relevant commands.
2. **One CLI implements.** Choose Claude Code, Codex, or Antigravity based on availability, fit, and remaining allowance. Work only in that agent's worktree and branch.
3. **A second CLI reviews independently.** Give it the brief, diff, and acceptance criteria. Ask for findings with file and line references, severity, and a concrete fix. Do not ask it to edit the implementer's worktree. It can review read-only or make a proposed fix in its own worktree.
4. **The owner triages.** The implementing agent or you decide which findings are valid, apply fixes in the implementation branch, and explain rejected findings.
5. **You verify and integrate.** Inspect the final diff, run the project's requested checks, then open and merge a PR when ready. Agents do not merge or deploy by default.
6. **Use another CLI selectively.** Bring it in for a genuinely separate task (for example docs while implementation proceeds), a difficult disagreement, or a final independent review. Keep concurrent agents to work that can be separated cleanly.

Do not bind lead, reviewer, or specialist roles to a provider brand. Pick from installed hosts by repository/tool locality, current model capability, fresh usage, and context-transfer cost. Rotate providers as the task and measured outcomes justify. Do not send the same full task to every host just to consume allowances.

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
agent-usage add --agent claude --project my-project --task issue-42 \
  --model sonnet --billing subscription --minutes 35

agent-usage add --agent codex --project my-project --task issue-42 \
  --model gpt-5-codex --billing subscription --minutes 18

agent-usage add --agent antigravity --project my-project --task issue-42 \
  --model gemini --billing credits --minutes 12 --cost-usd 0.20

agent-usage summary --month 2026-11
agent-usage path
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



## Usage-aware routing from any interface

Codex, Claude Code, Antigravity, and Copilot all read the same repository policy: Codex reads `AGENTS.md`, Claude loads it through `CLAUDE.md`, Antigravity loads `GEMINI.md`, and Copilot uses `.github/copilot-instructions.md`. The active interface remains the coordinator. It classifies the task, breaks it into bounded packets, proposes host/model-class assignments, and owns integration. It does not silently invoke another account or provider.

### Seed and review your private routing profile

```bash
agent-route init
```

This copies the example to `~/.config/multi-agent-codespace/router-profile.json` with private permissions. Review the model names against the model picker in each account and update this local file when offerings change. The committed example gives Claude starter aliases and leaves other model IDs to the active CLI's catalog. Provider model names are deliberately not baked in for Codex, Antigravity, or Copilot because their catalog and account availability can change. Each host also lists task classes it can support; maintain this capability list as the installed CLI features change.

### Record fresh provider usage

Open each provider's own usage view first; then enter the remaining allowance for the relevant window. Snapshots are local and private.

```bash
# From Claude Code's /usage view
agent-usage snapshot --agent claude --billing subscription \
  --window session --remaining-percent 42 --source /usage

# From Codex /status and its account usage page
agent-usage snapshot --agent codex --billing subscription \
  --window weekly --remaining-percent 65 --source codex-usage

# From Antigravity /usage or /quota
agent-usage snapshot --agent antigravity --billing subscription \
  --window session --remaining-percent 30 --source /usage

# Copilot: check the included monthly usage in GitHub billing/IDE usage
agent-usage snapshot --agent copilot --billing subscription \
  --window monthly --remaining-percent 72 --source github-billing

agent-usage availability
```

Enter the percentage shown by the provider or calculate remaining allowance from that provider's usage page. Include model group or reset data when useful. If the provider only reports dollar credits, use `--billing credits` and treat that number as local guidance for the same billing window; the router never adds it to subscriptions. Record new snapshots after a provider window resets or changes materially. Snapshots older than 72 hours are ignored by default.

### Ask for a route

Pick a task class, then use this from any CLI or terminal:

```bash
agent-route recommend --task-class coding-high --risk standard --current codex
agent-route recommend --task-class reasoning-high --risk high --current claude
agent-route recommend --task-class fast-utility --current antigravity
```

Classes describe the required model capability, not a vendor ranking:

- `reasoning-high`: architecture, hard debugging, security, or ambiguous cross-system work.
- `coding-high`: substantial implementation and refactoring.
- `fast-utility`: mechanical edits, routine documentation, or deterministic follow-up.
- `long-context`: broad document/repository synthesis when targeted reads are insufficient.
- `multimodal`: screenshots, visual inspection, diagrams, or image-heavy input.

The recommender uses the tightest fresh window for that provider, keeps the active interface when its allowance is within 15 percentage points of the best known option, and never treats unknown quota as zero. If the active provider's quota is unknown, it tells you to check the native view rather than switching on stale evidence. Percentages are a selection aid, not comparable token balances or pooled subscriptions.

To include a separately budgeted API or credit route, opt in explicitly:

```bash
agent-route recommend --task-class coding-high --allow-paid --current codex
```

`--allow-paid` only considers fresh snapshots for the billing type configured in your private profile. It does not start OmniRoute, spend credits, or sign in. OmniRoute is installed as an optional local gateway and disabled in the profile by default. Its credentials, costs, quotas, and provider terms are separate from native CLI subscriptions; never copy provider subscription credentials into the gateway without first verifying the provider permits that use.

### Break down and assign work

The active coordinator should produce a compact plan before parallelizing:

1. State the outcome and acceptance criteria.
2. Mark risk and select the required model class.
3. Run `scripts/usage.py availability` and `scripts/route.py recommend`; use the native provider view if data is missing or stale.
4. Split only independent work: one lead owns integration; bounded contributors get separate branches/worktrees; reviewers get a read-only final diff and evidence.
5. Assign each packet to a capable installed host based on current tools/data access, model fit, quota and continuity cost. Choose the concrete model from that provider's available model picker or private profile.
6. Keep the task packet self-contained: goal, allowed files, constraints, acceptance criteria, checks, owner/worktree, and expected output.
7. Run deterministic checks on the final integrated candidate, request an independent review when risk warrants it, and let the human approve PR merge/release.

A suggested output is:

| Work item | Role | Host/model class | Worktree | Depends on |
| --- | --- | --- | --- | --- |
| Core change | Lead implementer | Recommended capable host / coding-high | one writer branch | none |
| Security or correctness check | Independent reviewer | Different capable host / reasoning-high | read-only diff | core change |
| Separate docs or test fixture | Utility worker (only if separable) | Available host / fast-utility | separate branch | interface stable |

The active interface may draft and assign this plan, but worker execution remains explicit. Launch workers with `bash scripts/agent.sh <claude|codex|agy|copilot> <project>`; their worktrees are isolated. The coordinator integrates via Git and owns conflict resolution.

## Provider usage views

- Claude Code: `/usage` for plan use; `/cost` is API-session cost, not subscription quota.
- Codex: `/status` in the CLI and the account's Codex usage page. API-key billing remains separate.
- Antigravity: `/usage` or `/quota`; note shared model groups and optional AI credits.
- Copilot: check the VS Code Copilot status/usage view and GitHub billing settings. GitHub's billing model and included credits vary by plan; the terminal CLI may not expose a full account balance.
- OmniRoute: use its local dashboard/API statistics only after you deliberately configure and start the gateway. It is not a provider account or quota source.


### Learn from completed work

After the checks and any independent review, log an outcome without storing prompts or transcripts:

```bash
agent-usage outcome --task issue-42 --agent claude --model sonnet \
  --task-class coding-high --first-pass no --checks-passed yes \
  --repair-rounds 1 --review-findings 2
```

This records task class, first-pass success, final deterministic-check result, repair rounds, and actionable review findings. A class/model route is quality-adjusted only after at least five comparable outcomes for each active candidate; quality leads when scores differ, then quota and current-session continuity break close ties. Before that threshold, the router labels the evidence sparse and uses quota/context without claiming a provider is better. Keep the same model label in the private profile and outcome entries to measure a specific model; when the profile uses `null`, the router aggregates that host's models for the class.

The score weights final checks (50%), first-pass success (25%), zero repair rounds (15%), and a clean review (10%). It is a routing aid, not a substitute for code review or test evidence. Do not record user data or private task descriptions; use short issue IDs.


## Patterns adapted from agent-project-starter

This workspace adopts its capability-based roles, separate host/model routing, one lead by default, scoped task packets, isolated writers, independent review for risky work, and measured first-pass/check outcomes. See [Agent Orchestration](https://github.com/dn-lx/agent-project-starter/blob/prod/docs/AGENT-ORCHESTRATION.md) and [Execution Routing Policy](https://github.com/dn-lx/agent-project-starter/blob/prod/docs/EXECUTION-ROUTING-POLICY.md) in the starter.
