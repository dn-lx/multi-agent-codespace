#!/usr/bin/env python3
"""Usage-aware, provider-neutral model-class router. It recommends; it never launches agents."""
from __future__ import annotations

import argparse
import csv
import json
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROFILE_EXAMPLE = ROOT / ".agents" / "router-profile.example.json"
PRIVATE_DIR = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "multi-agent-codespace"
PRIVATE_PROFILE = PRIVATE_DIR / "router-profile.json"
SNAPSHOTS = Path(os.environ.get(
    "MULTI_AGENT_SNAPSHOTS_FILE",
    Path.home() / ".local" / "share" / "multi-agent-codespace" / "snapshots.jsonl",
))
CLASSES = {"reasoning-high", "coding-high", "fast-utility", "long-context", "multimodal"}
ALIASES = {"claude": "Claude Code", "codex": "Codex CLI", "antigravity": "Antigravity CLI",
           "copilot": "GitHub Copilot CLI", "omniroute": "OmniRoute gateway"}


def load_profile(path: Path | None) -> tuple[dict, Path]:
    defaults = json.loads(PROFILE_EXAMPLE.read_text(encoding="utf-8"))
    chosen = path or PRIVATE_PROFILE
    if chosen.exists():
        profile = json.loads(chosen.read_text(encoding="utf-8"))
        # Add new defaults while preserving any private enablement/model choices.
        profile.setdefault("providers", {})
        for agent, default in defaults.get("providers", {}).items():
            local = profile["providers"].get(agent, {})
            merged = {**default, **local}
            merged["models"] = {**default.get("models", {}), **local.get("models", {})}
            profile["providers"][agent] = merged
        profile.setdefault("freshness_hours", defaults.get("freshness_hours", 72))
        profile.setdefault("minimum_quality_samples", defaults.get("minimum_quality_samples", 5))
        profile.setdefault("allow_api_or_credit_routing_by_default",
                           defaults.get("allow_api_or_credit_routing_by_default", False))
        return profile, chosen
    if path is not None:
        raise ValueError(f"routing profile not found: {chosen}")
    return defaults, PROFILE_EXAMPLE


def snapshots() -> list[dict]:
    if not SNAPSHOTS.exists():
        return []
    rows = []
    with SNAPSHOTS.open(encoding="utf-8") as stream:
        for n, line in enumerate(stream, 1):
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid quota snapshot on line {n}") from exc
            if row.get("agent") in ALIASES:
                rows.append(row)
    return rows


def latest_quota(rows: list[dict], agent: str, freshness_hours: int,
                  billing: str = "subscription") -> dict | None:
    now = datetime.now(timezone.utc)
    by_window: dict[str, tuple[datetime, int, dict, float]] = {}
    for row in rows:
        if row.get("agent") != agent or row.get("billing") != billing:
            continue
        try:
            observed = datetime.fromisoformat(row["observed_at_utc"])
            if observed.tzinfo is None:
                observed = observed.replace(tzinfo=timezone.utc)
            age = (now - observed).total_seconds() / 3600
            remaining = int(row["remaining_percent"])
            window = str(row["window"])
        except (KeyError, TypeError, ValueError):
            continue
        if 0 <= age <= freshness_hours:
            previous = by_window.get(window)
            if previous is None or observed > previous[0]:
                by_window[window] = (observed, remaining, row, age)
    if not by_window:
        return None
    # Use the latest value per provider window, then the tightest window for that provider.
    tightest = min(by_window.values(), key=lambda entry: entry[1])
    return {"remaining": tightest[1], "row": tightest[2], "age": tightest[3],
            "windows": len(by_window)}


def quality_history(agent: str, model: str | None, task_class: str) -> dict:
    path = Path(os.environ.get("MULTI_AGENT_OUTCOMES_FILE", Path.home() / ".local" /
                              "share" / "multi-agent-codespace" / "outcomes.csv"))
    scores = []
    if not path.exists():
        return {"samples": 0, "score": None, "scope": "none"}
    with path.open(newline="", encoding="utf-8") as stream:
        for row in csv.DictReader(stream):
            if row.get("agent") != agent or row.get("task_class") != task_class:
                continue
            if model and row.get("model") != model:
                continue
            # Completed checks matter most; first-pass success and clean review are supporting signals.
            checks = 1.0 if row.get("checks_passed") == "yes" else 0.0
            first_pass = 1.0 if row.get("first_pass") == "yes" else 0.0
            no_repairs = 1.0 if int(row.get("repair_rounds", "0")) == 0 else 0.0
            clean_review = 1.0 if int(row.get("review_findings", "0")) == 0 else 0.0
            scores.append(0.50 * checks + 0.25 * first_pass + 0.15 * no_repairs + 0.10 * clean_review)
    return {
        "samples": len(scores),
        "score": sum(scores) / len(scores) if scores else None,
        "scope": "model" if model else "host",
    }


def recommend(args: argparse.Namespace) -> None:
    profile, profile_path = load_profile(args.profile)
    providers = profile.get("providers", {})
    freshness = int(profile.get("freshness_hours", 72))
    rows = snapshots()
    candidates = []
    paid_skipped = []
    for agent, config in providers.items():
        if not config.get("enabled", False):
            continue
        command = config.get("command") or ALIASES.get(agent)
        if not command or not shutil.which(command):
            continue
        model_map = config.get("models", {})
        model = model_map.get(args.task_class)
        # Empty explicit model map means the main interface picks from the native CLI's current catalog.
        if model_map and args.task_class not in model_map:
            continue
        if args.task_class not in config.get("supports", sorted(CLASSES)):
            continue

        if agent == "omniroute":
            if not args.allow_paid and not profile.get("allow_api_or_credit_routing_by_default", False):
                paid_skipped.append(agent)
                continue
            paid_billing = config.get("paid_billing", "api")
            quota = latest_quota(rows, agent, freshness, billing=paid_billing)
            billing = paid_billing
            if quota is None:
                continue
        else:
            quota = latest_quota(rows, agent, freshness, billing="subscription")
            billing = "subscription"
            if quota is None and args.allow_paid:
                paid_billing = config.get("paid_billing", "api")
                quota = latest_quota(rows, agent, freshness, billing=paid_billing)
                if quota:
                    billing = paid_billing
        candidates.append({
            "agent": agent, "command": command, "model": model, "billing": billing,
            "quota": quota, "quality": quality_history(agent, model, args.task_class),
            "is_current": agent == args.current,
        })

    print(f"Task class: {args.task_class} | risk: {args.risk}")
    print("Quality gate: keep the required class; do not downgrade a high-risk task to save quota.")
    print(f"Profile: {profile_path}")
    if not candidates:
        print("No installed, enabled host is eligible. Stay in the current interface or install/configure a host.")
        return

    known = [c for c in candidates if c["quota"] is not None]
    usable = [c for c in known if c["quota"]["remaining"] > 0]
    current = next((c for c in candidates if c["is_current"]), None)
    quality_threshold = int(profile.get("minimum_quality_samples", 5))
    quality_ready = len(usable) > 1 and all(c["quality"]["samples"] >= quality_threshold for c in usable)
    if current and current["quota"] is None:
        model_text = current["model"] or f"choose its best available {args.task_class} model in the CLI"
        print("The active provider has no fresh usage snapshot; do not switch based on stale or missing data.")
        print(f"Provisional choice: stay in {ALIASES[current['agent']]} / {model_text} (quota unknown).")
    elif usable:
        pool = usable
        if quality_ready:
            best_quality = max(c["quality"]["score"] for c in usable)
            # Quality wins unless observed scores are close; quota/context then break the tie.
            pool = [c for c in usable if c["quality"]["score"] >= best_quality - 0.05]
        best_remaining = max(c["quota"]["remaining"] for c in pool)
        preferred = [c for c in pool if c["is_current"] and
                     c["quota"]["remaining"] >= best_remaining - 15]
        picked = preferred[0] if preferred else max(pool, key=lambda c: c["quota"]["remaining"])
        q = picked["quota"]
        model_text = picked["model"] or f"choose its best available {args.task_class} model in the CLI"
        print(f"Recommendation: {ALIASES[picked['agent']]} / {model_text}")
        print(f"Usage basis: {q['remaining']}% in the tightest fresh {picked['billing']} window "
              f"({q['row'].get('window')}; observed {q['age']:.0f}h ago).")
        if quality_ready:
            print(f"Quality basis: {picked['quality']['score']:.0%} measured score across {picked['quality']['samples']} "
                  f"{args.task_class} tasks ({picked['quality']['scope']} history).")
        elif len(usable) > 1:
            print(f"Quality history is still sparse; quota/context break the tie until each candidate has "
                  f"{quality_threshold} recorded {args.task_class} outcomes.")
        if picked["is_current"]:
            print("Stay in the current interface; its quota and measured quality support continuity.")
        else:
            print("Use this host for the lead or a bounded independent worker; transfer only the task packet.")
    elif known:
        print("All fresh snapshots show 0% remaining. Check native usage or stop; no exhausted provider is recommended.")
    else:
        print("No fresh usage snapshot is available. Check native usage before switching providers.")
        if current:
            model_text = current["model"] or f"choose its best available {args.task_class} model in the CLI"
            print(f"Provisional choice: stay in {ALIASES[current['agent']]} / {model_text} (quota unknown).")
        else:
            print("No provider-brand default was selected. Compare current native quotas and choose a capable host.")
        print("Candidates:")
        for candidate in candidates:
            model_text = candidate["model"] or f"best available {args.task_class} model"
            print(f"- {ALIASES[candidate['agent']]} / {model_text} (quota unknown)")
    if args.risk in {"high", "critical"}:
        print("Require an independent review and deterministic checks before integration.")
    if paid_skipped:
        print("Paid API/credit routing is disabled; OmniRoute was skipped. Enable it only for a budget you knowingly set.")
    print("Subscription snapshots are separate provider values; percentages guide selection but are not pooled or billed totals.")





def init_profile(_args: argparse.Namespace) -> None:
    if PRIVATE_PROFILE.exists():
        raise ValueError(f"profile already exists; edit it directly: {PRIVATE_PROFILE}")
    PRIVATE_DIR.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(PRIVATE_DIR, 0o700)
    PRIVATE_PROFILE.write_text(PROFILE_EXAMPLE.read_text(encoding="utf-8"), encoding="utf-8")
    os.chmod(PRIVATE_PROFILE, 0o600)
    print(f"Created private routing profile: {PRIVATE_PROFILE}")
    print("Edit model names against each CLI's current model picker; OmniRoute stays disabled by default.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    init = commands.add_parser("init", help="copy the example profile to private user config")
    init.set_defaults(run=init_profile)
    route = commands.add_parser("recommend", help="recommend a host/model class from task and fresh usage")
    route.add_argument("--task-class", required=True, choices=sorted(CLASSES))
    route.add_argument("--risk", choices=["low", "standard", "high", "critical"], default="standard")
    route.add_argument("--current", choices=sorted(ALIASES), help="preserve the active host when usage is competitive")
    route.add_argument("--allow-paid", action="store_true", help="include configured API/credit routes")
    route.add_argument("--profile", type=Path, help="use an explicit routing profile")
    route.set_defaults(run=recommend)
    args = parser.parse_args()
    try:
        args.run(args)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"router: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
