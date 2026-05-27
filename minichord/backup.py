"""Automatic backup snapshots for saved miniChord documents."""

from __future__ import annotations

import contextlib
import hashlib
import os
import tempfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from PyQt6.QtCore import QStandardPaths

from minichord.settings import APPLICATION_NAME


BACKUP_SUFFIX = ".backup"
DEFAULT_BACKUP_SNAPSHOT_LIMIT = 20


@dataclass(frozen=True)
class BackupSnapshot:
    """A preserved previous on-disk version of a document."""

    path: Path
    source_path: Path
    created_at: datetime
    size: int


class BackupManager:
    """Create timestamped snapshots before an existing document is overwritten."""

    def __init__(
        self,
        directory: str | Path | None = None,
        snapshot_limit: int = DEFAULT_BACKUP_SNAPSHOT_LIMIT,
    ):
        self.directory = Path(directory) if directory is not None else default_backup_directory()
        self.snapshot_limit = max(1, snapshot_limit)

    def create_snapshot(
        self,
        source_path: str | Path,
        *,
        created_at: datetime | None = None,
    ) -> BackupSnapshot | None:
        """Copy an existing source file into a timestamped backup snapshot."""
        normalized_source = _normalized_path(source_path)
        if not normalized_source.is_file():
            return None

        content = normalized_source.read_bytes()
        timestamp = created_at or datetime.now(UTC)
        snapshot_path = _unique_path(self.snapshot_path(normalized_source, timestamp))
        _write_bytes_atomic(snapshot_path, content)
        self.prune_snapshots(normalized_source)
        return BackupSnapshot(
            path=snapshot_path,
            source_path=normalized_source,
            created_at=timestamp,
            size=len(content),
        )

    def snapshot_path(self, source_path: str | Path, created_at: datetime) -> Path:
        """Return the preferred snapshot path for a source file and timestamp."""
        normalized_source = _normalized_path(source_path)
        folder = self._source_folder(normalized_source)
        timestamp = _timestamp_text(created_at)
        source_name = _safe_filename(normalized_source.name)
        return folder / f"{timestamp}-{source_name}{BACKUP_SUFFIX}"

    def snapshots_for(self, source_path: str | Path) -> list[Path]:
        """Return snapshot paths for a source file, newest first."""
        folder = self._source_folder(_normalized_path(source_path))
        if not folder.is_dir():
            return []
        return sorted(folder.glob(f"*{BACKUP_SUFFIX}"), reverse=True)

    def prune_snapshots(self, source_path: str | Path) -> None:
        """Keep only the newest configured number of snapshots for a source file."""
        for old_snapshot in self.snapshots_for(source_path)[self.snapshot_limit:]:
            with contextlib.suppress(FileNotFoundError):
                old_snapshot.unlink()

    def _source_folder(self, source_path: Path) -> Path:
        digest = hashlib.sha256(str(source_path).encode("utf-8")).hexdigest()[:20]
        return self.directory / f"file-{digest}"


def default_backup_directory() -> Path:
    """Return the platform-specific backup snapshot directory."""
    location = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation)
    if location:
        return Path(location) / "backups"
    return Path.home() / ".local" / "share" / APPLICATION_NAME / "backups"


def _normalized_path(path: str | Path) -> Path:
    return Path(path).expanduser().resolve(strict=False)


def _timestamp_text(value: datetime) -> str:
    timestamp = value.astimezone(UTC) if value.tzinfo is not None else value.replace(tzinfo=UTC)
    return timestamp.strftime("%Y%m%dT%H%M%S%fZ")


def _safe_filename(filename: str) -> str:
    safe = "".join(character if _is_safe_filename_character(character) else "_" for character in filename)
    return (safe.strip("._") or "document")[:120]


def _is_safe_filename_character(character: str) -> bool:
    return character.isalnum() or character in {".", "-", "_"}


def _unique_path(path: Path) -> Path:
    if not path.exists():
        return path

    for index in range(2, 1000):
        candidate = path.with_name(f"{path.stem}-{index}{path.suffix}")
        if not candidate.exists():
            return candidate

    raise FileExistsError(path)


def _write_bytes_atomic(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    file_descriptor, temp_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=path.parent,
    )
    temp_path = Path(temp_name)
    try:
        with os.fdopen(file_descriptor, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, path)
        _sync_directory(path.parent)
    except Exception:
        with contextlib.suppress(FileNotFoundError):
            temp_path.unlink()
        raise


def _sync_directory(path: Path) -> None:
    if os.name != "posix":
        return

    try:
        directory_descriptor = os.open(path, os.O_RDONLY)
    except OSError:
        return

    try:
        os.fsync(directory_descriptor)
    finally:
        os.close(directory_descriptor)
