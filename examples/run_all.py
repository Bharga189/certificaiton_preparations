#!/usr/bin/env python3
"""Run every example and report a single pass/fail.

Each example asserts its own teaching points, so a green run means the claimed
behaviour actually happens -- not just that the script exits without raising.

    python3 examples/run_all.py
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

EXAMPLES = [
    "d1_patterns.py",
    "d2_context_cost.py",
    "d3_rag_acl.py",
    "d4_eval.py",
    "d5_guardrails.py",
    "d6_sla.py",
    "d7_team_setup.py",
]


def main() -> int:
    here = Path(__file__).parent
    results: list[tuple[str, int, str]] = []

    for name in EXAMPLES:
        proc = subprocess.run(
            [sys.executable, str(here / name)],
            capture_output=True,
            text=True,
            cwd=here,
        )
        tail = ""
        if proc.returncode != 0:
            lines = [ln for ln in (proc.stderr or proc.stdout).strip().splitlines() if ln.strip()]
            tail = lines[-1] if lines else "no output"
        results.append((name, proc.returncode, tail))

    width = max(len(n) for n in EXAMPLES)
    failures = 0
    print(f"{'example':<{width}}  result")
    print("-" * (width + 12))
    for name, code, tail in results:
        status = "PASS" if code == 0 else "FAIL"
        print(f"{name:<{width}}  {status}")
        if code != 0:
            failures += 1
            print(f"{'':<{width}}  {tail}")

    print("-" * (width + 12))
    print(f"{len(results) - failures}/{len(results)} examples passed")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
