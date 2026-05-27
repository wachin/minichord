"""Recovery discovery for autosaved miniChord drafts."""

from __future__ import annotations

import contextlib
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from minichord.autosave import AUTOSAVE_SUFFIX, AutosaveManager
from minichord.document import MiniChordDocument
from minichord.document.model import FRONT_MATTER_DELIMITER


@dataclass(frozen=True)
class RecoveryDraft:
    """A recoverable autosave draft discovered on disk."""

    path: Path
    document: MiniChordDocument
    source_path: Path | None
    draft_id: str
    saved_at: datetime


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
