#!/usr/bin/env bash
# Independent provider CLIs plus optional local API router. Authenticate each account separately.
set -Eeuo pipefail

workspace_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
mkdir -p "$HOME/.local/bin"
chmod +x "$workspace_root/scripts/usage.py" "$workspace_root/scripts/route.py"
ln -sf "$workspace_root/scripts/usage.py" "$HOME/.local/bin/agent-usage"
ln -sf "$workspace_root/scripts/route.py" "$HOME/.local/bin/agent-route"
export PATH="$HOME/.local/bin:$PATH"
line='export PATH="$HOME/.local/bin:$PATH"'
if ! grep -Fqx "$line" "$HOME/.bashrc" 2>/dev/null; then
  printf '\n%s\n' "$line" >> "$HOME/.bashrc"
fi

failed=()
printf '\n[1/6] Node.js 22 runtime (OmniRoute requires Node >=22.22.2)\n'
if ! npm install --global --prefix "$HOME/.local" node@22.22.2; then
  failed+=("node 22.22.2")
fi
export PATH="$HOME/.local/bin:$PATH"

printf '\n[2/6] OpenAI Codex CLI\n'
if ! npm install --global --prefix "$HOME/.local" @openai/codex; then
  failed+=("codex")
fi

printf '\n[3/6] Claude Code CLI\n'
if ! (curl -fsSL https://claude.ai/install.sh | bash); then
  failed+=("claude")
fi

printf '\n[4/6] Antigravity CLI\n'
if ! (curl -fsSL https://antigravity.google/cli/install.sh | bash); then
  failed+=("agy")
fi

printf '\n[5/6] GitHub Copilot CLI\n'
if ! npm_config_ignore_scripts=false npm install --global --prefix "$HOME/.local" @github/copilot; then
  failed+=("copilot")
fi

printf '\n[6/6] OmniRoute CLI (optional; server will not start automatically)\n'
if ! npm install --global --prefix "$HOME/.local" omniroute; then
  failed+=("omniroute")
fi

printf '\nInstalled versions:\n'
for bin in node npm claude codex agy copilot omniroute; do
  if command -v "$bin" >/dev/null 2>&1; then
    if [[ "$bin" == omniroute ]]; then
      "$bin" --version 2>&1 | tail -n 1 || failed+=("$bin version")
    else
      "$bin" --version || failed+=("$bin version")
    fi
  else
    printf 'NOT FOUND: %s\n' "$bin" >&2
    failed+=("$bin missing")
  fi
done

if (( ${#failed[@]} )); then
  printf 'Attention required: %s\n' "${failed[*]}" >&2
  exit 1
fi

printf '\nReady to sign in separately with: claude, codex, agy, copilot\n'
printf 'Usage-aware commands work from any Codespace worktree: agent-usage, agent-route\n'
printf 'OmniRoute is installed but remains stopped until you start it.\n'
printf 'No accounts have been authenticated by this installer.\n'
