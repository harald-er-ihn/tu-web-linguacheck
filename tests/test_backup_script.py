"""Tests für das Script zur Sicherung lokaler Arbeitsdaten."""

import os
import subprocess
from pathlib import Path

SCRIPT_PATH = Path(__file__).parents[1] / "tools" / "backup_local_data.sh"


def _run_backup(
    project_root: Path,
    backup_root: Path,
    timestamp: str,
) -> None:
    """Führt das Backup-Script mit reproduzierbaren Pfaden und Zeitstempel aus."""
    environment = os.environ | {
        "PROJECT_ROOT": str(project_root),
        "BACKUP_ROOT": str(backup_root),
        "BACKUP_TIMESTAMP": timestamp,
    }

    subprocess.run(
        [str(SCRIPT_PATH)],
        check=True,
        capture_output=True,
        text=True,
        env=environment,
    )


def test_backup_script_keeps_two_newest_readable_backups(tmp_path: Path) -> None:
    """Das Script sichert lokale Daten und behält nur zwei aktuelle Backups."""
    project_root = tmp_path / "project"
    backup_root = tmp_path / "backups"
    config_directory = project_root / "config"
    data_directory = project_root / "data"
    reports_directory = project_root / "reports"

    config_directory.mkdir(parents=True)
    data_directory.mkdir()
    reports_directory.mkdir()
    (config_directory / "site.local.yaml").write_text("profile: tu-de\n")
    (config_directory / "example.yaml").write_text("profile: generic-de\n")
    (data_directory / "crawl.json").write_text('{"pages": 3}\n')
    (reports_directory / "site.html").write_text("<html>Report</html>\n")

    _run_backup(project_root, backup_root, "2026-03-18_120000")
    _run_backup(project_root, backup_root, "2026-03-19_120000")
    _run_backup(project_root, backup_root, "2026-03-20_120000")

    backup_directories = sorted(
        directory.name for directory in backup_root.iterdir() if directory.is_dir()
    )

    assert backup_directories == [
        "tu-web-linguacheck-2026-03-19_120000",
        "tu-web-linguacheck-2026-03-20_120000",
    ]

    latest_backup = backup_root / "tu-web-linguacheck-2026-03-20_120000"
    assert (
        latest_backup / "config" / "site.local.yaml"
    ).read_text() == "profile: tu-de\n"
    assert not (latest_backup / "config" / "example.yaml").exists()
    assert (latest_backup / "data" / "crawl.json").read_text() == '{"pages": 3}\n'
    assert (
        latest_backup / "reports" / "site.html"
    ).read_text() == "<html>Report</html>\n"
