#!/usr/bin/env python3
"""Private manual session and quota ledger for the agent workspace.

Provider sessions are never queried automatically. Enter only verified summaries.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import shutil
import sys
from collections import defaultdict
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

FIELDS = ["date_utc", "agent", "project", "task", "model", "billing", "minutes", "cost_usd"]
AGENTS = {"claude", "codex", "antigravity", "copilot", "omniroute"}
BILLING = {"subscription", "api", "credits", "unknown"}
WINDOWS = {"session", "weekly", "monthly", "api"}
COMMANDS = {"claude": "claude", "codex": "codex", "antigravity": "agy",
            "copilot": "copilot", "omniroute": "omniroute"}
BASE = Path.home() / ".local" / "share" / "multi-agent-codespace"


def private_file(path: Path, *, append: bool = False):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(path.parent, 0o700)
    flags = os.O_WRONLY | os.O_CREAT | (os.O_APPEND if append else os.O_TRUNC)
    fd = os.open(path, flags, 0o600)
    os.chmod(path, 0o600)
    return os.fdopen(fd, "a" if append else "w", newline="", encoding="utf-8")


def ledger_path() -> Path:
    return Path(os.environ.get("MULTI_AGENT_USAGE_FILE", BASE / "usage.csv"))


def snapshots_path() -> Path:
    return Path(os.environ.get("MULTI_AGENT_SNAPSHOTS_FILE", BASE / "snapshots.jsonl"))


def outcomes_path() -> Path:
    return Path(os.environ.get("MULTI_AGENT_OUTCOMES_FILE", BASE / "outcomes.csv"))


def add(args: argparse.Namespace) -> None:
    if args.minutes <= 0:
        raise ValueError("minutes must be a positive integer")
    if args.cost_usd is not None:
        try:
            cost = Decimal(args.cost_usd)
        except InvalidOperation as exc:
            raise ValueError("cost-usd must be a non-negative number") from exc
        if not cost.is_finite() or cost < 0:
            raise ValueError("cost-usd must be a non-negative number")
        cost_text = format(cost.quantize(Decimal("0.01")), "f")
    else:
        cost_text = ""

    path = ledger_path()
    is_new = not path.exists()
    with private_file(path, append=True) as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        if is_new:
            writer.writeheader()
        writer.writerow({
            "date_utc": datetime.now(timezone.utc).date().isoformat(),
            "agent": args.agent,
            "project": args.project,
            "task": args.task,
            "model": args.model,
            "billing": args.billing,
            "minutes": args.minutes,
            "cost_usd": cost_text,
        })
    print(f"Recorded {args.minutes} minutes for {args.agent} in {path}")


def snapshot(args: argparse.Namespace) -> None:
    value = {
        "observed_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "agent": args.agent,
        "billing": args.billing,
        "window": args.window,
        "remaining_percent": args.remaining_percent,
        "reset_at": args.reset_at or "",
        "model_group": args.model_group or "",
        "source": args.source,
    }
    with private_file(snapshots_path(), append=True) as stream:
        stream.write(json.dumps(value, separators=(",", ":")) + "\n")
    print(f"Saved {args.agent} {args.window} usage snapshot locally.")


def read_snapshots() -> list[dict]:
    path = snapshots_path()
    if not path.exists():
        return []
    records = []
    with path.open(encoding="utf-8") as stream:
        for number, line in enumerate(stream, 1):
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid snapshot entry on line {number}") from exc
            if record.get("agent") in AGENTS:
                records.append(record)
    return records


def availability(args: argparse.Namespace) -> None:
    now = datetime.now(timezone.utc)
    latest: dict[tuple[str, str, str], dict] = {}
    for row in read_snapshots():
        key = (row["agent"], row["billing"], row["window"])
        try:
            observed = datetime.fromisoformat(row["observed_at_utc"])
        except (KeyError, ValueError):
            continue
        if observed.tzinfo is None:
            observed = observed.replace(tzinfo=timezone.utc)
        if key not in latest or observed > datetime.fromisoformat(latest[key]["observed_at_utc"]):
            latest[key] = row

    print("Provider usage is separate. Values below are manual snapshots, not live quota reads.")
    for agent in sorted(AGENTS):
        command = COMMANDS[agent]
        installed = shutil.which(command) is not None
        rows = [r for (a, _, _), r in latest.items() if a == agent]
        if not installed:
            state = "CLI not installed"
        elif not rows:
            state = "installed; quota unknown (check the provider's native usage view)"
        else:
            parts = []
            for row in sorted(rows, key=lambda x: (x["billing"], x["window"])):
                observed = datetime.fromisoformat(row["observed_at_utc"])
                if observed.tzinfo is None:
                    observed = observed.replace(tzinfo=timezone.utc)
                age = (now - observed).total_seconds() / 3600
                fresh = age <= args.max_age_hours
                label = "fresh" if fresh else f"stale {age:.0f}h"
                reset = f", resets {row['reset_at']}" if row.get("reset_at") else ""
                group = f", group {row['model_group']}" if row.get("model_group") else ""
                parts.append(f"{row['billing']}/{row['window']} {row['remaining_percent']}% ({label}{reset}{group})")
            state = "; ".join(parts)
        print(f"- {agent:<12} {state}")
    print(f"Ledger: {ledger_path()}")
    print(f"Snapshots: {snapshots_path()}")
    print(f"Task outcomes: {outcomes_path()}")


def record_outcome(args: argparse.Namespace) -> None:
    if args.repair_rounds < 0 or args.review_findings < 0:
        raise ValueError("repair-rounds and review-findings must be non-negative")
    fields = ["date_utc", "task", "agent", "model", "task_class", "first_pass",
              "checks_passed", "repair_rounds", "review_findings"]
    path = outcomes_path()
    is_new = not path.exists()
    with private_file(path, append=True) as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        if is_new:
            writer.writeheader()
        writer.writerow({
            "date_utc": datetime.now(timezone.utc).date().isoformat(),
            "task": args.task,
            "agent": args.agent,
            "model": args.model,
            "task_class": args.task_class,
            "first_pass": args.first_pass,
            "checks_passed": args.checks_passed,
            "repair_rounds": args.repair_rounds,
            "review_findings": args.review_findings,
        })
    print(f"Recorded task outcome for {args.agent}/{args.model} in {path}")


def summary(args: argparse.Namespace) -> None:
    if not re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", args.month):
        raise ValueError("month must use YYYY-MM format")
    path = ledger_path()
    if not path.exists():
        print(f"No entries yet. Ledger: {path}")
        return
    groups: dict[tuple[str, str], dict[str, Decimal]] = defaultdict(
        lambda: {"minutes": Decimal(0), "cost": Decimal(0), "priced": Decimal(0)}
    )
    with path.open(newline="", encoding="utf-8") as stream:
        for row in csv.DictReader(stream):
            if not row["date_utc"].startswith(args.month):
                continue
            group = groups[(row["agent"], row["billing"])]
            group["minutes"] += Decimal(row["minutes"] or "0")
            if row["cost_usd"].strip():
                group["cost"] += Decimal(row["cost_usd"])
                group["priced"] += 1
    if not groups:
        print(f"No entries for {args.month}.")
        return
    print(f"Usage entries for {args.month} (manual session minutes; optional reported costs)")
    print(f"{'AGENT':<13} {'BILLING':<14} {'MINUTES':>8} {'REPORTED USD':>14}")
    for (agent, billing), values in sorted(groups.items()):
        reported = f"{values['cost']:.2f}" if values["priced"] else "—"
        print(f"{agent:<13} {billing:<14} {int(values['minutes']):>8} {reported:>14}")
    print("Reported USD sums only rows where you entered a verified amount.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    add_parser = commands.add_parser("add", help="record a completed work session")
    add_parser.add_argument("--agent", required=True, choices=sorted(AGENTS))
    add_parser.add_argument("--project", required=True)
    add_parser.add_argument("--task", required=True, help="short ID/label; no prompts or transcripts")
    add_parser.add_argument("--model", required=True, help="short model label")
    add_parser.add_argument("--billing", required=True, choices=sorted(BILLING))
    add_parser.add_argument("--minutes", required=True, type=int)
    add_parser.add_argument("--cost-usd", help="optional verified provider-reported amount")
    add_parser.set_defaults(run=add)

    snap = commands.add_parser("snapshot", help="record a quota value read from a provider-native view")
    snap.add_argument("--agent", required=True, choices=sorted(AGENTS))
    snap.add_argument("--billing", required=True, choices=sorted(BILLING))
    snap.add_argument("--window", required=True, choices=sorted(WINDOWS))
    snap.add_argument("--remaining-percent", required=True, type=int, choices=range(0, 101))
    snap.add_argument("--reset-at", help="provider-displayed reset time")
    snap.add_argument("--model-group", help="quota group/model family if provider displays one")
    snap.add_argument("--source", required=True, help="short label such as /usage or account usage page")
    snap.set_defaults(run=snapshot)

    avail = commands.add_parser("availability", help="show installed CLIs and recent manual quota snapshots")
    avail.add_argument("--max-age-hours", type=int, default=72)
    avail.set_defaults(run=availability)

    outcome_parser = commands.add_parser("outcome", help="record the completed quality outcome of a task")
    outcome_parser.add_argument("--task", required=True, help="short ID/label; no prompts or transcripts")
    outcome_parser.add_argument("--agent", required=True, choices=sorted(AGENTS - {"omniroute"}))
    outcome_parser.add_argument("--model", required=True, help="model label used for the task")
    outcome_parser.add_argument("--task-class", required=True,
                                choices=["reasoning-high", "coding-high", "fast-utility", "long-context", "multimodal"])
    outcome_parser.add_argument("--first-pass", required=True, choices=["yes", "no"])
    outcome_parser.add_argument("--checks-passed", required=True, choices=["yes", "no"])
    outcome_parser.add_argument("--repair-rounds", required=True, type=int)
    outcome_parser.add_argument("--review-findings", required=True, type=int)
    outcome_parser.set_defaults(run=record_outcome)

    summary_parser = commands.add_parser("summary", help="summarize a UTC month")
    summary_parser.add_argument("--month", required=True, help="YYYY-MM")
    summary_parser.set_defaults(run=summary)

    path_parser = commands.add_parser("path", help="print private ledger path")
    path_parser.set_defaults(run=lambda _args: print(ledger_path()))

    args = parser.parse_args()
    try:
        args.run(args)
    except (OSError, ValueError, csv.Error) as exc:
        print(f"usage ledger: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
