#!/usr/bin/env python3
"""Regenerate the auto-section of STATUS.md from git history.

Only the block between the ``AUTO:BEGIN`` and ``AUTO:END`` markers is rewritten;
the hand-maintained AC checklist and "next steps" above it are preserved.

Usage:
    python experiments/jmoshi_long_context/tools/gen_digest.py [--status PATH]
"""

from __future__ import annotations

import argparse
import datetime as dt
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
EXP_DIR = HERE.parents[1]  # experiments/jmoshi_long_context
REPO_ROOT = HERE.parents[3]  # repo root
DEFAULT_STATUS = EXP_DIR / "STATUS.md"
REL = "experiments/jmoshi_long_context"

BEGIN = "<!-- AUTO:BEGIN -->"
END = "<!-- AUTO:END -->"


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def build_auto_section() -> str:
    log = _git(
        "log", "-n", "15", "--pretty=format:- `%h` %s （%cs）", "--", REL
    )
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        BEGIN,
        f"_自動生成: {now} （`tools/gen_digest.py`）_",
        "",
        f"### 直近の変更（`{REL}` 配下のコミット）",
        "",
        log if log else "- （まだ該当コミットがありません）",
        "",
        END,
    ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--status", type=Path, default=DEFAULT_STATUS)
    args = parser.parse_args(argv)

    status: Path = args.status
    if not status.exists():
        print(f"STATUS.md not found at {status}", file=sys.stderr)
        return 1

    text = status.read_text(encoding="utf-8")
    if BEGIN not in text or END not in text:
        print("AUTO markers not found in STATUS.md", file=sys.stderr)
        return 2

    pre = text.split(BEGIN, 1)[0]
    post = text.split(END, 1)[1]
    status.write_text(pre + build_auto_section() + post, encoding="utf-8")
    print(f"Updated {status}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
