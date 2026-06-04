"""Crash-safe autosave drafts for ChordPages documents."""

from __future__ import annotations

import contextlib
import hashlib
import os
import tempfile
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from PyQt6.QtCore import QStandardPaths

from chordpages.document.model import FRONT_MATTER_DELIMITER, ChordPagesDocument
from chordpages.settings import APPLICATION_NAME


DEFAULT_AUTOSAVE_INTERVAL_MS = 30_000
AUTOSAVE_SUFFIX = ".autosave.mchord"


@dataclass(frozen=True)
class AutosaveDraft:
    """A written autosave draft and the source document it protects."""

    path: Path
    source_path: Path | None
    draft_id: str
    saved_at: datetime


class AutosaveManager:
    """Write document drafts with atomic replace semantics."""

    def __init__(self, directory: str | Path | None = None):
        self.directory = Path(directory) if directory is not None else default_autosave_directory()

    def autosave_path(self, source_path: str | Path | None, draft_id: str) -> Path:
        """Return the stable autosave path for a source path or untitled draft."""
        return self.directory / f"{_draft_key(source_path, draft_id)}{AUTOSAVE_SUFFIX}"

    def write(
        self,
        document: ChordPagesDocument,
        *,
        source_path: str | Path | None,
        draft_id: str,
        saved_at: datetime | None = None,
    ) -> AutosaveDraft:
        """Atomically write an autosave draft and return its metadata."""
        timestamp = saved_at or datetime.now(UTC)
        path = self.autosave_path(source_path, draft_id)
        content = _serialize_autosave(document, source_path, draft_id, timestamp)
        _write_text_atomic(path, content)
        return AutosaveDraft(
            path=path,
            source_path=Path(source_path) if source_path is not None else None,
            draft_id=draft_id,
            saved_at=timestamp,
        )

    def clear(self, source_path: str | Path | None, draft_id: str) -> None:
        """Remove the autosave draft for a source path or untitled draft."""
        with contextlib.suppress(OSError):
            self.autosave_path(source_path, draft_id).unlink()

    @staticmethod
    def new_draft_id() -> str:
        """Return an identifier for an untitled autosave draft."""
        return uuid.uuid4().hex


def default_autosave_directory() -> Path:
    """Return the platform-specific autosave draft directory."""
    location = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation)
    if location:
        return Path(location) / "autosave"
    return Path.home() / ".local" / "share" / APPLICATION_NAME / "autosave"


def _draft_key(source_path: str | Path | None, draft_id: str) -> str:
    if source_path is None:
        return f"untitled-{draft_id}"

    source_text = str(Path(source_path).expanduser().resolve(strict=False))
    digest = hashlib.sha256(source_text.encode("utf-8")).hexdigest()[:20]
    return f"file-{digest}"


def _serialize_autosave(
    document: ChordPagesDocument,
    source_path: str | Path | None,
    draft_id: str,
    saved_at: datetime,
) -> str:
    text = document.text.rstrip("\n")
    metadata = {
        "format": "chordpages-song",
        "version": str(document.version),
        "title": document.title,
        "autosave": "true",
        "autosave_saved_at": saved_at.isoformat(),
        "autosave_draft_id": draft_id,
    }
    if source_path is not None:
        metadata["source_path"] = str(Path(source_path).expanduser().resolve(strict=False))

    metadata_lines = "\n".join(
        f"{key}: {_metadata_value(value)}"
        for key, value in metadata.items()
    )
    return (
        f"{FRONT_MATTER_DELIMITER}\n"
        f"{metadata_lines}\n"
        f"{FRONT_MATTER_DELIMITER}\n\n"
        f"{text}\n"
    )


def _metadata_value(value: str) -> str:
    return " ".join(str(value).splitlines()).strip()


def _write_text_atomic(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    file_descriptor, temp_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=path.parent,
    )
    temp_path = Path(temp_name)
    try:
        with os.fdopen(file_descriptor, "w", encoding="utf-8", newline="\n") as handle:
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
