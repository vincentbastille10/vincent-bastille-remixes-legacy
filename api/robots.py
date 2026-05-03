def handler(request):
    content = "User-agent: *\nAllow: /\nSitemap: https://remixes.vincentbastille.online/sitemap.xml\n"
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "text/plain; charset=utf-8",
            "Cache-Control": "public, max-age=0, s-maxage=3600"
        },
        "body": content
    }
