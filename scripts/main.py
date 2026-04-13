#!/usr/bin/env python3
"""Generate SEO pages then refresh sitemap."""
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def run(cmd):
    subprocess.run(cmd, check=True, cwd=ROOT)

if __name__ == "__main__":
    run(["python3", "scripts/generate_page.py"])
    run(["python3", "scripts/update_sitemap.py"])
    print("SEO generation pipeline complete.")
