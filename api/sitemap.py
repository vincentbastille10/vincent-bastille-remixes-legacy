from pathlib import Path

def handler(request):
    root = Path(__file__).resolve().parents[1]
    sitemap_path = root / "public" / "sitemap.xml"
    if not sitemap_path.exists():
        sitemap_path = root / "sitemap.xml"
    content = sitemap_path.read_text(encoding="utf-8")
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/xml; charset=utf-8",
            "Cache-Control": "public, max-age=0, s-maxage=3600"
        },
        "body": content
    }
