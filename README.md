# Vincent Bastille Remixes Legacy Generator

A static-site generator for 70 SEO-focused remix landing pages around the Vincent Bastille universe. It renders valid, mobile-responsive HTML files from `data/pages.json` + `templates/page.html.jinja`, adds internal links with descriptive anchors, and includes a CTA to:

**https://remixes.vincentbastille.online/**

The generator can run in two modes:
- **Bulk mode** (`generate.py`) to build all 70 pages.
- **Daily mode** (`daily.py`) to rebuild one “page of the day” and auto-commit it.

---

## 1) Project description

This project produces a complete set of remix landing pages designed for discoverability and conversion while preserving a natural editorial tone. The output emphasizes:

- Unique page slugs (70 total)
- Human-sounding music writing (not robotic)
- Natural keyword placement
- Descriptive internal links between related pages
- JSON-LD structured data (`WebPage` + `MusicAlbum` context)
- Responsive layout for mobile and desktop
- Static hosting compatibility (no server runtime required)

---

## 2) Setup

> Required command (as requested):

```bash
pip install anthropic jinja2 python-dotenv
```

Then run from the project root:

```bash
python generate.py
```

This generates all 70 HTML pages using local fallback copy by default, or Anthropic-generated copy when `ANTHROPIC_API_KEY` is configured.

---

## 3) Configuration (`.env` setup)

Create your environment file:

```bash
cp .env.example .env
```

Example `.env` values:

```env
ANTHROPIC_API_KEY=your_api_key_here
ANTHROPIC_MODEL=claude-3-5-sonnet-latest
```

Notes:
- `ANTHROPIC_API_KEY` is optional. If empty, generation still works with built-in unique fallback copy.
- `ANTHROPIC_MODEL` is optional and defaults to `claude-3-5-sonnet-latest`.

---

## 4) Usage

### Generate all 70 pages

```bash
python generate.py
```

What it does:
- Loads `data/pages.json`
- Validates all slugs are unique
- Renders each page with Jinja2 template
- Writes `<slug>.html` in the project root

### Generate today’s page + commit

```bash
python daily.py
```

What it does:
- Selects one slug based on today’s date
- Regenerates only that page
- Runs `git add <slug>.html`
- Creates a commit if there are actual content changes

---

## 5) Deployment (static HTML)

Because this is a pure static output, you can deploy to Netlify, Vercel, or GitHub Pages.

### Netlify

1. Push this repo to GitHub.
2. In Netlify, create a new site from that repo.
3. Build settings:
   - **Build command:** `python generate.py`
   - **Publish directory:** `.`
4. (Optional) Add `ANTHROPIC_API_KEY` in Netlify environment variables.
5. Deploy.

### Vercel

1. Import the repo in Vercel.
2. Configure:
   - **Build command:** `python generate.py`
   - **Output directory:** `.`
3. (Optional) Add `ANTHROPIC_API_KEY` in Vercel project env vars.
4. Deploy.

### GitHub Pages

Option A (pre-generated pages in repo):
1. Run `python generate.py` locally.
2. Commit generated `*.html` files.
3. Enable GitHub Pages from `main` branch root.

Option B (GitHub Actions build):
1. Add a workflow that runs `python generate.py`.
2. Publish the generated static files artifact to Pages.

---

## 6) Cron setup for `daily.py`

### Linux cron

Open crontab:

```bash
crontab -e
```

Add this line (8:00 every day):

```cron
0 8 * * * /usr/bin/python3 /path/to/daily.py
```

If needed, run from repo root in cron:

```cron
0 8 * * * cd /path/to/repo && /usr/bin/python3 daily.py
```

### GitHub Actions workflow example

Create `.github/workflows/daily.yml`:

```yaml
name: Daily Remix Page

on:
  schedule:
    - cron: "0 8 * * *"
  workflow_dispatch:

jobs:
  daily:
    runs-on: ubuntu-latest
    permissions:
      contents: write

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: pip install anthropic jinja2 python-dotenv

      - name: Run daily generator
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: python daily.py

      - name: Push commit
        run: |
          git push
```

---

## Quality checklist

- [x] Every page is unique (`data/pages.json` contains 70 unique slugs + per-page metadata)
- [x] Natural language output (fallback + optional AI copy)
- [x] Keywords integrated naturally
- [x] Internal links use descriptive anchor text
- [x] CTA to `https://remixes.vincentbastille.online/` on every page
- [x] JSON-LD schema included and valid JSON
- [x] Mobile responsive template
- [x] Static HTML deployable on Netlify / Vercel / GitHub Pages
- [x] Runs with:

```bash
pip install anthropic jinja2 python-dotenv && python generate.py
```
