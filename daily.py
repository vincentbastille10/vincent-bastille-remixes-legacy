#!/usr/bin/env python3
from __future__ import annotations

import datetime as dt
import json
import subprocess
from pathlib import Path

from generate import DATA_FILE, load_pages, render_pages

ROOT = Path(__file__).resolve().parent

TREND_TOPICS = [
    "best michael jackson remix ever",
    "sade remix deep house version",
    "legendary house remixes 90s club",
    "iconic remix songs history",
    "madonna classic remix legacy",
    "daft punk iconic remix versions",
    "david guetta club remix history",
]


def run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=ROOT, check=False, capture_output=True, text=True)


def slugify(topic: str) -> str:
    return "-".join(topic.lower().replace("'", "").split())


def ensure_daily_page() -> str:
    pages = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    today = dt.date.today()
    topic = TREND_TOPICS[today.toordinal() % len(TREND_TOPICS)]
    slug = f"{slugify(topic)}-{today.isoformat()}"

    if any(p["slug"] == slug for p in pages):
        return slug

    new_id = max(p["id"] for p in pages) + 1
    pages.append(
        {
            "id": new_id,
            "slug": slug,
            "keyword": topic,
            "title": f"Best {topic.title()} – The Ultimate Remix Legacy Guide",
            "description": f"{topic.title()} explained with remix history, musical analysis, and direct access to Vincent Bastille remixes.",
        }
    )
    DATA_FILE.write_text(json.dumps(pages, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Added daily page: {slug}")
    return slug


def commit_if_needed(slug: str) -> None:
    run(["git", "add", f"{slug}.html", "sitemap.xml", str(DATA_FILE.relative_to(ROOT))])

    diff = run(["git", "diff", "--cached", "--quiet"])
    if diff.returncode == 0:
        print("No content changes detected; nothing to commit.")
        return

    message = f"chore: add daily remix seo page for {dt.date.today().isoformat()} ({slug})"
    commit = run(["git", "commit", "-m", message])
    if commit.returncode != 0:
        print(commit.stdout)
        print(commit.stderr)
        raise SystemExit("git commit failed")
    print(message)


def main() -> None:
    slug = ensure_daily_page()
    render_pages(selected_slug=slug)
    commit_if_needed(slug)


if __name__ == "__main__":
    main()
