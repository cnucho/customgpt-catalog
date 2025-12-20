# build_catalog_github_seo.py
# --------------------------------------------------
# SEO helper for Custom GPT Catalog (GitHub Pages)
# - Generates sitemap.xml
# - Generates robots.txt
# --------------------------------------------------

from pathlib import Path
import datetime

SITE_URL = "https://cnucho.github.io/customgpt-catalog"
BASE_DIR = Path(__file__).resolve().parent
DOCS_DIR = BASE_DIR / "docs"


def build_sitemap():
    today = datetime.date.today().isoformat()
    urls = []

    def add(url):
        urls.append(f"""  <url>
    <loc>{url}</loc>
    <lastmod>{today}</lastmod>
  </url>""")

    add(f"{SITE_URL}/")
    add(f"{SITE_URL}/en/")

    details_dir = DOCS_DIR / "details"
    if details_dir.exists():
        for f in sorted(details_dir.glob("*.html")):
            add(f"{SITE_URL}/details/{f.name}")

    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{chr(10).join(urls)}
</urlset>
"""

    DOCS_DIR.mkdir(exist_ok=True)
    (DOCS_DIR / "sitemap.xml").write_text(xml, encoding="utf-8")


def build_robots():
    txt = f"""User-agent: *
Allow: /
Sitemap: {SITE_URL}/sitemap.xml
"""
    DOCS_DIR.mkdir(exist_ok=True)
    (DOCS_DIR / "robots.txt").write_text(txt, encoding="utf-8")


if __name__ == "__main__":
    print("[SEO] generating sitemap.xml and robots.txt")
    build_sitemap()
    build_robots()
    print("[SEO] done")
