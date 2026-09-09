"""Tests für zentrale Projektmetadaten."""

from tu_web_linguacheck.project_metadata import ProjectMetadata, load_project_metadata


def test_load_project_metadata_reads_installed_package_metadata(monkeypatch) -> None:
    """Projektmetadaten stammen aus den installierten Paketmetadaten."""
    package_metadata = {
        "Name": "test-linguacheck",
        "Version": "2.3.4",
        "Summary": "Testbeschreibung",
        "Author": "Testautor",
        "License": "Test License\n\nVollständiger Lizenztext.",
    }

    monkeypatch.setattr(
        "tu_web_linguacheck.project_metadata.metadata",
        lambda package_name: package_metadata,
    )

    assert load_project_metadata() == ProjectMetadata(
        name="test-linguacheck",
        version="2.3.4",
        description="Testbeschreibung",
        author="Testautor",
        license_name="Test License",
    )
