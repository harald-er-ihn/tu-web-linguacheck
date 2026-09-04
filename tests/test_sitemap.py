"""Tests für XML-Sitemaps."""

from tu_web_linguacheck.sitemap import parse_sitemap


def test_parse_sitemap_separates_page_urls_and_child_sitemaps() -> None:
    """Der Parser trennt URL-Set-Einträge von Sitemap-Index-Einträgen."""
    urlset_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">
  <url>
    <loc>https://example.org/seite/</loc>
    <image:image>
      <image:loc>https://example.org/bild.webp</image:loc>
    </image:image>
  </url>
</urlset>
"""
    index_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <sitemap>
    <loc>https://example.org/page-sitemap.xml</loc>
  </sitemap>
</sitemapindex>
"""

    page_urls, child_sitemaps = parse_sitemap(urlset_xml)
    assert page_urls == ["https://example.org/seite/"]
    assert child_sitemaps == []

    page_urls, child_sitemaps = parse_sitemap(index_xml)
    assert page_urls == []
    assert child_sitemaps == ["https://example.org/page-sitemap.xml"]
