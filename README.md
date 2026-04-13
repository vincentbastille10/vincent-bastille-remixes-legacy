## Vincent Bastille Remixes – SEO & Conversion Toolkit

### Run locally
- `python3 -m venv .venv && source .venv/bin/activate`
- `pip install -r requirements.txt`
- `cp .env.example .env` and fill values if needed.
- `python3 scripts/main.py`

### What the scripts do
- `scripts/generate_page.py`: generates SEO pages (template fallback, Together AI optional).
- `scripts/update_sitemap.py`: updates `sitemap.xml` with core conversion pages.
- `scripts/main.py`: runs both in sequence.

### Automation-ready
- Docker: `docker build -t vb-seo . && docker run --rm vb-seo`
- GitHub Actions: workflow at `.github/workflows/seo-generator.yml`.
- Cron example: `15 4 * * * cd /path/to/repo && /usr/bin/python3 scripts/main.py`
