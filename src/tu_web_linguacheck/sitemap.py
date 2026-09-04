"""Parser für XML-Sitemaps."""

from xml.etree import ElementTree

_SITEMAP_NAMESPACE = "http://www.sitemaps.org/schemas/sitemap/0.9"
_NAMESPACE = {"sitemap": _SITEMAP_NAMESPACE}


def parse_sitemap(xml: str) -> tuple[list[str], list[str]]:
    """Liest Seiten-URLs und untergeordnete Sitemaps aus einer XML-Sitemap."""
    root = ElementTree.fromstring(xml)

    page_urls = [
        location.text
        for location in root.findall("sitemap:url/sitemap:loc", _NAMESPACE)
        if location.text is not None
    ]
    child_sitemaps = [
        location.text
        for location in root.findall("sitemap:sitemap/sitemap:loc", _NAMESPACE)
        if location.text is not None
    ]

    return page_urls, child_sitemaps
