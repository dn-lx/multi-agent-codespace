# Multi-agent Codespace

A lightweight GitHub Codespace for Claude Code, Codex CLI, Antigravity CLI, and GitHub Copilot CLI, with an optional OmniRoute API gateway. A shared, human-led coordinator workflow routes by task capability and fresh usage snapshots; provider accounts and quotas remain separate.

| Tool | Command | Provider |
|---|---|---|
| Claude Code | `claude` | Anthropic |
| Codex CLI | `codex` | OpenAI |
| Antigravity CLI | `agy` | Google |
| GitHub Copilot CLI | `copilot` | GitHub |
| Optional model gateway | `omniroute` | OmniRoute; API/credits only (off by default) |

## Open the existing Codespace

Open [GitHub Codespaces](https://github.com/codespaces) and select the Codespace with display name **multi-agent-codespace**.

- Repository: `dn-lx/multi-agent-codespace`
- Working folder: `/workspaces/multi-agent-codespace`
- Integration branch: `dev`
- Claude, Codex, Antigravity, Copilot, and OmniRoute's optional local API gateway are installed by `.devcontainer/install-agents.sh`
- Default environment: Node.js 22.22.2, Git, GitHub CLI, ripgrep, Python, tmux, and Linux keyring/D-Bus components

This repository contains the Codespace setup, isolated worktree launchers, usage-aware host/model recommender, and shared agent policy. `agent-route` and `agent-usage` are installed on PATH so every CLI worktree can query the same private usage data. The coordinator recommends and prepares handoffs; it does not silently call other accounts or auto-merge changes.

### Step 1 — Check installations and login status

```bash
cd /workspaces/multi-agent-codespace
bash scripts/doctor.sh
bash scripts/doctor.sh --auth
bash tests/smoke.sh  # local regression check, also run in GitHub Actions
```

Sign in interactively, **separately**, when required:

```bash
claude
codex login --device-auth
agy
copilot  # then use /login in the CLI

# GitHub CLI uses its own authorization
# (needed for GitHub PR commands inside this Codespace)
gh auth login -h github.com
```

Use the providers' own login flows. The installer does not accept or commit passwords, keys or tokens. Subscription access depends on provider eligibility. API-based usage may incur separate charges.

### Step 2 — Set up a real project with isolated Git branches

```bash
bash scripts/project.sh add https://github.com/OWNER/REPOSITORY.git my-project
bash scripts/project.sh status my-project
```

This creates:

```text
/workspaces/projects/my-project/
  source/     # clean reference clone; do not edit here
  claude/     # branch agents/claude/...
  codex/      # branch agents/codex/...
  agy/        # branch agents/agy/...
  copilot/    # branch agents/copilot/...
```

If the target repository contains a `dev` branch, that is the starting point. Otherwise the remote default branch is the start point. The script **never modifies or merges a protected branch**. It creates new agent branches and does not deploy.

The worktrees are created only when you request a project. You may use any app repository, including private ones when Git is appropriately authorized.

### Step 3 — Work in tandem

Start with one implementation session, then add a second CLI for an independent review or a separate bounded task. Use extra CLIs only when the work divides cleanly or another perspective is valuable; they do not share conversations, logins, or quotas.

```bash
bash scripts/agent.sh claude my-project
bash scripts/agent.sh status
# In another terminal, start a separate worktree when needed:
bash scripts/agent.sh codex my-project
```

Each launcher uses a separate Git worktree and **tmux** session. This includes `bash scripts/agent.sh copilot my-project` when Copilot is selected. Codex, Claude, Antigravity and Copilot share one assignment and handoff policy; OmniRoute can be enabled separately for a deliberate API/credit budget. To detach without stopping the agent, press **Ctrl-b**, then **d**. Re-run the launcher to reconnect. Use each extra CLI selectively; never let agents modify the same dirty worktree. For a ready-to-use brief, review prompt, and handoff routine, see [Tandem workflow and usage](docs/WORKFLOW-AND-USAGE.md).

### Step 4 — Track usage and integrate safely

Check each provider's native usage view, and optionally record active session minutes and any verified charges in the private local ledger:

```bash
agent-usage add --agent claude --project my-project --task issue-42 \
  --model sonnet --billing subscription --minutes 35
agent-usage summary --month 2026-11
```

The ledger stays outside the repository and does not collect prompts, outputs, or credentials. It cannot combine provider quotas. Review the final diff and checks yourself, then open a pull request from the agent branch when ready. Do not ask one agent to edit another agent's uncommitted working directory. Use project instructions (`AGENTS.md`, `CLAUDE.md`, `GEMINI.md`) if supplied by that repository.

## Shared coordinator and usage-aware routing

All four coding interfaces follow `AGENTS.md`; Claude includes it through `CLAUDE.md`, Antigravity uses `GEMINI.md`, and Copilot uses `.github/copilot-instructions.md`. The active interface plans and splits work, checks fresh local provider usage, recommends a host and model class, and owns integration.

```bash
agent-route init
agent-usage availability

# Record fresh native quota snapshots, then ask for a route:
agent-usage snapshot --agent codex --billing subscription \
  --window weekly --remaining-percent 60 --source codex-usage
agent-route recommend --task-class coding-high --risk standard --current codex
```

See [Tandem workflow and usage](docs/WORKFLOW-AND-USAGE.md) for task breakdown, assignment rules, snapshot commands, and model-class guidance. Snapshots are manual because provider plan usage is not exposed through a common safe API. The recommender ignores data older than 72 hours, keeps the active interface when competitive, and leaves paid API/credit routing off unless requested with `--allow-paid`. OmniRoute is installed but stopped and disabled until deliberately configured.

### Direct ChatGPT access

The paired Linux Desktop Commander remote device allows ChatGPT terminal and file access directly, without your Windows PC.

```bash
bash scripts/remote.sh status
bash scripts/remote.sh start
bash scripts/remote.sh attach
```

The `status` command checks whether the remote process is running, **not** whether the device has completed pairing. Pairing may need repeating after a container rebuild.

Codespaces `postStartCommand` requests that Desktop Commander reconnect in a detached tmux session when the Codespace starts. If its prior device pairing is unavailable, use `attach` and follow the official pairing instructions. Credentials remain in the user's private home folder, never this Git repository. No automatic permission bypass is enabled.

The `--disable-no-sleep` flag allows Codespaces to suspend normally. This means ChatGPT access disappears when the Codespace is stopped or suspended and returns only once it is running and the remote agent reconnects. **Codespaces compute/storage may be billable.**

### Historical data

The old Me+ checkout and its uncommitted files were saved at `/workspaces/_legacy-me-plus-preserved-20261121`. The old `prod` branch and archive branch also retain the tracked source. Do not delete the preservation folder until you've exported its unfinished files. The old `/workspaces/me-plus` link exists only for older editor sessions.

### Updating or rebuilding

The committed `.devcontainer` defines reproducible installations. Rebuilding may remove CLI login sessions and restart remote pairing. Do not rebuild during active agent sessions. After rebuilding, run `bash scripts/doctor.sh --auth` and recheck the remote agent.

## References

[Claude Code](https://code.claude.com/docs/en/setup) · [Codex CLI](https://github.com/openai/codex) · [Antigravity CLI](https://antigravity.google/docs/cli) · [GitHub Codespaces](https://docs.github.com/en/codespaces) · [Desktop Commander](https://desktopcommander.app/help/getting-started/what-is-desktop-commander)
