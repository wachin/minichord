"""Recovery discovery for autosaved miniChord drafts."""

from __future__ import annotations

import contextlib
import hashlib
import os
import tempfile
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from minichord.autosave import AUTOSAVE_SUFFIX, AutosaveManager
from minichord.document import MiniChordDocument, MiniChordSongbook
from minichord.document.model import FRONT_MATTER_DELIMITER


SONGBOOK_AUTOSAVE_SUFFIX = ".autosave.mchordbook"


@dataclass(frozen=True)
class RecoveryDraft:
    """A recoverable autosave draft discovered on disk."""

    path: Path
    document: MiniChordDocument
    source_path: Path | None
    draft_id: str
    saved_at: datetime


@dataclass(frozen=True)
class SongbookRecoveryDraft:
    """A recoverable songbook autosave draft discovered on disk."""

    path: Path
    songbook: MiniChordSongbook
    source_path: Path | None
    draft_id: str
    saved_at: datetime


class SongbookAutosaveManager:
    """Write crash-recovery drafts for `.mchordbook` projects."""

    def __init__(self, directory: str | Path | None = None):
        self.directory = Path(directory) if directory is not None else AutosaveManager().directory

    def autosave_path(self, source_path: str | Path | None, draft_id: str) -> Path:
        """Return the stable songbook autosave path for a source path or draft."""
        if source_path is None:
            key = f"untitled-songbook-{draft_id}"
        else:
            key = "songbook-" + _path_digest(Path(source_path))
        return self.directory / f"{key}{SONGBOOK_AUTOSAVE_SUFFIX}"

    def write(
        self,
        songbook: MiniChordSongbook,
        *,
        source_path: str | Path | None,
        draft_id: str,
        saved_at: datetime | None = None,
    ) -> SongbookRecoveryDraft:
        """Atomically write a recoverable songbook draft."""
        timestamp = saved_at or datetime.now(UTC)
        path = self.autosave_path(source_path, draft_id)
        content = _serialize_songbook_autosave(songbook, source_path, draft_id, timestamp)
        _write_text_atomic(path, content)
        return SongbookRecoveryDraft(
            path=path,
            songbook=songbook,
            source_path=Path(source_path) if source_path is not None else None,
            draft_id=draft_id,
            saved_at=timestamp,
        )

    def clear(self, source_path: str | Path | None, draft_id: str) -> None:
        """Remove a songbook autosave draft."""
        with contextlib.suppress(FileNotFoundError):
            self.autosave_path(source_path, draft_id).unlink()

    @staticmethod
    def new_draft_id() -> str:
        """Return an identifier for an untitled songbook autosave draft."""
        return uuid.uuid4().hex


class RecoveryManager:
    """Find and manage recoverable document drafts."""

    def __init__(self, autosave_manager: AutosaveManager | None = None):
        self.autosave_manager = autosave_manager or AutosaveManager()

    def autosave_drafts(self) -> list[RecoveryDraft]:
        """Return recoverable autosave drafts from newest to oldest."""
        directory = self.autosave_manager.directory
        if not directory.is_dir():
            return []

        drafts = [
            draft
            for path in directory.glob(f"*{AUTOSAVE_SUFFIX}")
            if (draft := _load_autosave_draft(path)) is not None
        ]
        return sorted(drafts, key=lambda draft: draft.saved_at, reverse=True)

    def has_recoverable_drafts(self) -> bool:
        """Return whether at least one autosave draft is available."""
        return bool(self.autosave_drafts())

    def discard(self, draft: RecoveryDraft) -> None:
        """Delete a draft that has been recovered or intentionally ignored."""
        with contextlib.suppress(FileNotFoundError):
            draft.path.unlink()


class SongbookRecoveryManager:
    """Find and manage recoverable songbook drafts."""

    def __init__(self, autosave_manager: SongbookAutosaveManager | None = None):
        self.autosave_manager = autosave_manager or SongbookAutosaveManager()

    def autosave_drafts(self) -> list[SongbookRecoveryDraft]:
        """Return recoverable songbook autosave drafts from newest to oldest."""
        directory = self.autosave_manager.directory
        if not directory.is_dir():
            return []

        drafts = [
            draft
            for path in directory.glob(f"*{SONGBOOK_AUTOSAVE_SUFFIX}")
            if (draft := _load_songbook_autosave_draft(path)) is not None
        ]
        return sorted(drafts, key=lambda draft: draft.saved_at, reverse=True)

    def has_recoverable_drafts(self) -> bool:
        """Return whether at least one songbook autosave draft is available."""
        return bool(self.autosave_drafts())

    def discard(self, draft: SongbookRecoveryDraft) -> None:
        """Delete a songbook draft that has been recovered or ignored."""
        with contextlib.suppress(FileNotFoundError):
            draft.path.unlink()


def _load_autosave_draft(path: Path) -> RecoveryDraft | None:
    try:
        content = path.read_text(encoding="utf-8")
    except OSError:
        return None

    metadata = _parse_front_matter(content)
    if metadata.get("autosave") != "true":
        return None

    saved_at = _parse_datetime(metadata.get("autosave_saved_at")) or _mtime_datetime(path)
    source_path = _source_path(metadata.get("source_path"))
    draft_id = metadata.get("autosave_draft_id") or path.stem
    return RecoveryDraft(
        path=path,
        document=MiniChordDocument.from_mchord(content),
        source_path=source_path,
        draft_id=draft_id,
        saved_at=saved_at,
    )


def _load_songbook_autosave_draft(path: Path) -> SongbookRecoveryDraft | None:
    try:
        content = path.read_text(encoding="utf-8")
    except OSError:
        return None

    metadata, body = _parse_songbook_autosave(content)
    if metadata.get("autosave") != "true" or metadata.get("autosave_kind") != "songbook":
        return None

    saved_at = _parse_datetime(metadata.get("autosave_saved_at")) or _mtime_datetime(path)
    source_path = _source_path(metadata.get("source_path"))
    draft_id = metadata.get("autosave_draft_id") or path.stem
    return SongbookRecoveryDraft(
        path=path,
        songbook=MiniChordSongbook.from_mchordbook(body),
        source_path=source_path,
        draft_id=draft_id,
        saved_at=saved_at,
    )


def _serialize_songbook_autosave(
    songbook: MiniChordSongbook,
    source_path: str | Path | None,
    draft_id: str,
    saved_at: datetime,
) -> str:
    metadata = {
        "autosave": "true",
        "autosave_kind": "songbook",
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
        f"{songbook.to_mchordbook()}"
    )


def _parse_songbook_autosave(content: str) -> tuple[dict[str, str], str]:
    normalized = content.replace("\r\n", "\n").replace("\r", "\n")
    if not normalized.startswith(f"{FRONT_MATTER_DELIMITER}\n"):
        return {}, normalized

    parts = normalized.split(f"\n{FRONT_MATTER_DELIMITER}\n", 1)
    if len(parts) != 2:
        return {}, normalized

    metadata_block = parts[0].removeprefix(f"{FRONT_MATTER_DELIMITER}\n")
    body = parts[1].lstrip("\n")
    metadata: dict[str, str] = {}
    for raw_line in metadata_block.splitlines():
        key, separator, value = raw_line.partition(":")
        if separator:
            metadata[key.strip()] = value.strip()
    return metadata, body


def _parse_front_matter(content: str) -> dict[str, str]:
    normalized = content.replace("\r\n", "\n").replace("\r", "\n")
    if not normalized.startswith(f"{FRONT_MATTER_DELIMITER}\n"):
        return {}

    parts = normalized.split(f"\n{FRONT_MATTER_DELIMITER}\n", 1)
    if len(parts) != 2:
        return {}

    metadata: dict[str, str] = {}
    metadata_block = parts[0].removeprefix(f"{FRONT_MATTER_DELIMITER}\n")
    for raw_line in metadata_block.splitlines():
        key, separator, value = raw_line.partition(":")
        if separator:
            metadata[key.strip()] = value.strip()
    return metadata


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None

    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None

    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _mtime_datetime(path: Path) -> datetime:
    try:
        return datetime.fromtimestamp(path.stat().st_mtime, UTC)
    except OSError:
        return datetime.now(UTC)


def _source_path(value: str | None) -> Path | None:
    if not value:
        return None
    return Path(value)


def _path_digest(path: Path) -> str:
    text = str(path.expanduser().resolve(strict=False))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:20]


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
