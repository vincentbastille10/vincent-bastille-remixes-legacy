#!/usr/bin/env python3
"""
Fix sitemap 404 on remixes.vincentbastille.online
Applies 3 changes to the GitHub repo:
  1. Creates/overwrites sitemap.xml at root (copied from public/sitemap.xml)
  2. Ensures robots.txt at root has correct Sitemap line
  3. Fixes vercel.json to serve from root correctly
"""

import urllib.request
import urllib.error
import json
import base64
import sys


REPO  = "vincentbastille10/vincent-bastille-remixes-legacy"
BRANCH = "main"
API   = "https://api.github.com"

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github.v3+json",
    "Content-Type": "application/json",
    "User-Agent": "sitemap-fixer"
}

def api_get(path):
    url = f"{API}/repos/{REPO}/contents/{path}?ref={BRANCH}"
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise

def api_put(path, content_str, message, sha=None):
    content_b64 = base64.b64encode(content_str.encode("utf-8")).decode("ascii")
    body = {"message": message, "content": content_b64, "branch": BRANCH}
    if sha:
        body["sha"] = sha
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        f"{API}/repos/{REPO}/contents/{path}",
        data=data, headers=HEADERS, method="PUT"
    )
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())

def log(msg):
    print(msg, flush=True)

# ── 1. Read public/sitemap.xml ────────────────────────────────────────────────
log("→ Reading public/sitemap.xml...")
pub = api_get("public/sitemap.xml")
if pub:
    sitemap_content = base64.b64decode(pub["content"].replace("\n","")).decode("utf-8")
    log(f"  ✓ Found ({len(sitemap_content)} chars)")
else:
    log("  ✗ public/sitemap.xml not found — using minimal fallback")
    sitemap_content = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        '  <url><loc>https://remixes.vincentbastille.online/</loc>'
        '<changefreq>weekly</changefreq><priority>1.0</priority></url>\n'
        '</urlset>\n'
    )

# ── 2. Write sitemap.xml at root ──────────────────────────────────────────────
log("→ Writing sitemap.xml at root...")
root_sitemap = api_get("sitemap.xml")
sha = root_sitemap["sha"] if root_sitemap else None
api_put("sitemap.xml", sitemap_content,
        "fix: add sitemap.xml to root for Vercel static serving", sha)
log("  ✓ sitemap.xml written to root")

# ── 3. Ensure robots.txt at root is correct ───────────────────────────────────
log("→ Checking robots.txt at root...")
root_robots = api_get("robots.txt")
robots_content = "User-agent: *\nAllow: /\nSitemap: https://remixes.vincentbastille.online/sitemap.xml\n"
if root_robots:
    existing = base64.b64decode(root_robots["content"].replace("\n","")).decode("utf-8")
    if "Sitemap: https://remixes.vincentbastille.online/sitemap.xml" in existing:
        log("  ✓ robots.txt already correct — skipping")
    else:
        api_put("robots.txt", robots_content,
                "fix: ensure robots.txt has correct Sitemap line", root_robots["sha"])
        log("  ✓ robots.txt updated")
else:
    api_put("robots.txt", robots_content, "fix: add robots.txt to root", None)
    log("  ✓ robots.txt created at root")

# ── 4. Fix vercel.json ────────────────────────────────────────────────────────
log("→ Fixing vercel.json...")
new_vercel = {
    "version": 2,
    "routes": [
        {
            "src": "/sitemap.xml",
            "dest": "/sitemap.xml",
            "headers": {"Content-Type": "application/xml; charset=utf-8"}
        },
        {
            "src": "/robots.txt",
            "dest": "/robots.txt",
            "headers": {"Content-Type": "text/plain; charset=utf-8"}
        },
        {"handle": "filesystem"},
        {"src": "/(.*)", "dest": "/$1"}
    ]
}
root_vercel = api_get("vercel.json")
sha = root_vercel["sha"] if root_vercel else None
api_put("vercel.json", json.dumps(new_vercel, indent=2) + "\n",
        "fix: correct vercel.json to serve sitemap.xml and robots.txt from root", sha)
log("  ✓ vercel.json fixed")

# ── Done ──────────────────────────────────────────────────────────────────────
log("")
log("━" * 50)
log("✅ ALL FIXES APPLIED — Vercel will redeploy in ~60s")
log("")
log("Test URLs:")
log("  https://remixes.vincentbastille.online/sitemap.xml")
log("  https://remixes.vincentbastille.online/robots.txt")
