"""CLI input validation and JSON output; no repository or policy access."""

import argparse
import json
import re
import sys
from dataclasses import asdict
from typing import Sequence

from agentic_dev_harness.codex import CodexSmokePlanner
from agentic_dev_harness.planner import DummyPlanner, Planner, PlannerRequest


def repository_name(value: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9-]*/[A-Za-z0-9_.-]+", value):
        raise argparse.ArgumentTypeError("repository must be OWNER/REPO")
    if value.split("/")[1] in {".", ".."}:
        raise argparse.ArgumentTypeError("repository must be OWNER/REPO")
    return value


def positive_integer(value: str) -> int:
    try:
        number = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError("issue must be a positive integer") from None
    if number < 1:
        raise argparse.ArgumentTypeError("issue must be a positive integer")
    return number


def policy_path(value: str) -> str:
    if not value.strip():
        raise argparse.ArgumentTypeError("policy path must not be empty")
    return value


def timeout_seconds(value: str) -> int:
    try:
        number = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError("timeout must be an integer from 1 to 300") from None
    if not 1 <= number <= 300:
        raise argparse.ArgumentTypeError("timeout must be an integer from 1 to 300")
    return number


def main(argv: Sequence[str] | None = None, *, planner: Planner | None = None) -> int:
    parser = argparse.ArgumentParser(prog="agentic-dev-harness")
    commands = parser.add_subparsers(dest="command", required=True)
    plan = commands.add_parser("plan", help="Emit an offline dummy Plan as JSON")
    plan.add_argument("--repository", required=True, type=repository_name)
    plan.add_argument("--issue", required=True, type=positive_integer)
    plan.add_argument("--policy", default=".agent/policy.yaml", type=policy_path)
    plan.add_argument(
        "--codex-smoke-test",
        action="store_true",
        help="Check Codex ChatGPT connectivity with fixed input; does not generate a Plan",
    )
    plan.add_argument(
        "--timeout",
        type=timeout_seconds,
        default=60,
        help="Codex inference timeout in seconds (1-300; default: 60)",
    )
    args = parser.parse_args(argv)
    request = PlannerRequest(args.repository, args.issue, args.policy)
    selected_planner = (
        planner
        if planner is not None
        else (CodexSmokePlanner(timeout=args.timeout) if args.codex_smoke_test else DummyPlanner())
    )
    try:
        result = selected_planner.plan(request)
        output = json.dumps(asdict(result), ensure_ascii=False, indent=2)
    except Exception as exc:
        print(f"Planner failed: {exc}", file=sys.stderr)
        return 1
    print(output)
    return 0
