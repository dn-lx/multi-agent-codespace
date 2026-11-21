#!/usr/bin/env python3
"""Private, manual session-usage ledger for Claude Code, Codex, and Antigravity.

No provider APIs are contacted and no prompts, outputs, or credentials are stored.
"""
from __future__ import annotations

import argparse
import csv
import os
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

FIELDS = ["date_utc", "agent", "project", "task", "model", "billing", "minutes", "cost_usd"]
AGENTS = {"claude", "codex", "antigravity"}
BILLING = {"subscription", "api", "credits", "unknown"}
LEDGER = Path.home() / ".local" / "share" / "multi-agent-codespace" / "usage.csv"


def ledger_path() -> Path:
    return Path(os.environ.get("MULTI_AGENT_USAGE_FILE", LEDGER))


def add(args: argparse.Namespace) -> None:
    if args.agent not in AGENTS:
        raise ValueError(f"agent must be one of: {', '.join(sorted(AGENTS))}")
    if args.billing not in BILLING:
        raise ValueError(f"billing must be one of: {', '.join(sorted(BILLING))}")
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
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(path.parent, 0o700)
    is_new = not path.exists()
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    try:
        os.chmod(path, 0o600)
        with os.fdopen(fd, "a", newline="", encoding="utf-8") as stream:
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
    except Exception:
        # fdopen owns and closes the descriptor after it succeeds.
        raise
    print(f"Recorded {args.minutes} minutes for {args.agent} in {path}")


def summary(args: argparse.Namespace) -> None:
    if not re.fullmatch(r"\d{4}-\d{2}", args.month):
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
    add_parser.add_argument("--task", required=True, help="short ID or label; no prompts/transcripts")
    add_parser.add_argument("--model", required=True, help="short model label")
    add_parser.add_argument("--billing", required=True, choices=sorted(BILLING))
    add_parser.add_argument("--minutes", required=True, type=int)
    add_parser.add_argument("--cost-usd", help="optional verified amount reported by provider")
    add_parser.set_defaults(run=add)

    summary_parser = commands.add_parser("summary", help="summarize a UTC month")
    summary_parser.add_argument("--month", required=True, help="YYYY-MM")
    summary_parser.set_defaults(run=summary)

    path_parser = commands.add_parser("path", help="print the private ledger path")
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
