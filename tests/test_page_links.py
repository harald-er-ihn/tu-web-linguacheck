"""Tests für die Extraktion allgemeiner Seitenlinks."""
# pylint: disable=duplicate-code

from tu_web_linguacheck.config import CrawlConfig
from tu_web_linguacheck.page_links import extract_page_links, find_crawlable_page_links


def test_extract_page_links_resolves_regular_main_links() -> None:
    """Normale Links aus dem Hauptinhalt werden aufgelöst und gefiltert."""
    html = """
    <html>
      <body>
        <nav>
          <a href="/navigation/">Navigation</a>
        </nav>
        <main>
          <a href="team/">Team</a>
          <a href="https://cs.tu-dortmund.de/studium/">Studium</a>
          <a href="#kontakt">Kontakt</a>
          <a href="mailto:info@example.org">E-Mail</a>
          <a href="tel:+492317550">Telefon</a>
          <a href="javascript:void(0)">Menü</a>
        </main>
      </body>
    </html>
    """

    links = extract_page_links(
        "https://cs.tu-dortmund.de/fakultaet/",
        html,
    )

    assert links == [
        "https://cs.tu-dortmund.de/fakultaet/team/",
        "https://cs.tu-dortmund.de/studium/",
    ]


def test_find_crawlable_page_links_filters_and_normalizes_main_links() -> None:
    """Nur erlaubte, normalisierte und eindeutige Hauptlinks bleiben erhalten."""
    config = CrawlConfig(
        allowed_domains=["example.org"],
        max_depth=1,
        max_pages=10,
        requests_per_second=1.0,
        obey_robots_txt=True,
        tracking_parameters=["utm_source"],
        exclude_patterns=[r"\.(?:pdf|zip)(?:$|[?#])"],
    )
    html = """
    <main>
      <a href="team/?article=42&utm_source=newsletter#members">Team</a>
      <a href="team/?article=42">Team erneut</a>
      <a href="/downloads/report.pdf">PDF</a>
      <a href="https://external.example/page/">Extern</a>
      <a href="https://example.org/contact/">Kontakt</a>
    </main>
    """

    links = find_crawlable_page_links(
        "https://example.org/about/",
        html,
        config,
    )

    assert links == [
        "https://example.org/about/team/?article=42",
        "https://example.org/contact/",
    ]
