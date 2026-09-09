"""Zentraler Zugriff auf die installierten Projektmetadaten."""

from dataclasses import dataclass
from importlib.metadata import metadata

_PACKAGE_NAME = "tu-web-linguacheck"


@dataclass(frozen=True)
class ProjectMetadata:
    """Die für Oberflächen benötigten Projektmetadaten."""

    name: str
    version: str
    description: str
    author: str
    license_name: str


def load_project_metadata() -> ProjectMetadata:
    """Lädt Projektmetadaten aus den installierten Paketmetadaten."""
    package_metadata = metadata(_PACKAGE_NAME)
    license_text = package_metadata["License"]
    license_name = next(line for line in license_text.splitlines() if line)

    return ProjectMetadata(
        name=package_metadata["Name"],
        version=package_metadata["Version"],
        description=package_metadata["Summary"],
        author=package_metadata["Author"],
        license_name=license_name,
    )
