#!/usr/bin/env python3
from __future__ import annotations

import datetime as dt
import subprocess
from pathlib import Path

from generate import load_pages, render_pages

ROOT = Path(__file__).resolve().parent


def run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=ROOT, check=False, capture_output=True, text=True)


def pick_today_slug() -> str:
    pages = load_pages()
    today = dt.date.today()
    idx = today.toordinal() % len(pages)
    return pages[idx].slug


def commit_if_needed(slug: str) -> None:
    html_file = f"{slug}.html"
    run(["git", "add", html_file])

    diff = run(["git", "diff", "--cached", "--quiet"])
    if diff.returncode == 0:
        print("No content changes detected; nothing to commit.")
        return

    message = f"chore: regenerate daily remix page for {dt.date.today().isoformat()} ({slug})"
    commit = run(["git", "commit", "-m", message])
    if commit.returncode != 0:
        print(commit.stdout)
        print(commit.stderr)
        raise SystemExit("git commit failed")
    print(message)


def main() -> None:
    slug = pick_today_slug()
    render_pages(selected_slug=slug)
    commit_if_needed(slug)


if __name__ == "__main__":
    main()
