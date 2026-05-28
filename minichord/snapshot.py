"""Document version snapshots for miniChord documents."""

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

from minichord.document import MiniChordDocument, MiniChordSongbook
from minichord.document.model import FRONT_MATTER_DELIMITER
from minichord.settings import APPLICATION_NAME


DOCUMENT_SNAPSHOT_SUFFIX = ".snapshot.mchord"
SONGBOOK_SNAPSHOT_SUFFIX = ".snapshot.mchordbook"
DEFAULT_DOCUMENT_SNAPSHOT_LIMIT = 50
DEFAULT_SONGBOOK_SNAPSHOT_LIMIT = 50


@dataclass(frozen=True)
class DocumentSnapshot:
    """A named restorable version of a miniChord document."""

    path: Path
    document: MiniChordDocument
    source_path: Path | None
    snapshot_id: str
    created_at: datetime
    label: str
    size: int


@dataclass(frozen=True)
class SongbookSnapshot:
    """A named restorable version of a miniChord songbook."""

    path: Path
    songbook: MiniChordSongbook
    source_path: Path | None
    snapshot_id: str
    created_at: datetime
    label: str
    size: int


class DocumentSnapshotManager:
    """Create, list, and discard timestamped document snapshots."""

    def __init__(
        self,
        directory: str | Path | None = None,
        snapshot_limit: int = DEFAULT_DOCUMENT_SNAPSHOT_LIMIT,
    ):
        self.directory = Path(directory) if directory is not None else default_snapshot_directory()
        self.snapshot_limit = max(1, snapshot_limit)

    def create_snapshot(
        self,
        document: MiniChordDocument,
        *,
        source_path: str | Path | None = None,
        document_key: str = "untitled",
        label: str = "",
        snapshot_id: str | None = None,
        created_at: datetime | None = None,
    ) -> DocumentSnapshot:
        """Write a new document snapshot and return its metadata."""
        timestamp = created_at or datetime.now(UTC)
        resolved_snapshot_id = snapshot_id or uuid.uuid4().hex
        content = _serialize_snapshot(
            document,
            source_path=source_path,
            snapshot_id=resolved_snapshot_id,
            created_at=timestamp,
            label=label,
        )
        path = _unique_path(
            self.snapshot_path(
                document,
                source_path=source_path,
                document_key=document_key,
                snapshot_id=resolved_snapshot_id,
                created_at=timestamp,
            )
        )
        _write_text_atomic(path, content)
        self.prune_snapshots(source_path=source_path, document_key=document_key)
        return DocumentSnapshot(
            path=path,
            document=document,
            source_path=_source_path(source_path),
            snapshot_id=resolved_snapshot_id,
            created_at=timestamp,
            label=label,
            size=len(content.encode("utf-8")),
        )

    def snapshot_path(
        self,
        document: MiniChordDocument,
        *,
        source_path: str | Path | None,
        document_key: str,
        snapshot_id: str,
        created_at: datetime,
    ) -> Path:
        """Return the preferred path for a document snapshot."""
        folder = self._document_folder(source_path, document_key)
        timestamp = _timestamp_text(created_at)
        title = _safe_filename(document.title or "Untitled Song")
        return folder / f"{timestamp}-{title}-{snapshot_id[:8]}{DOCUMENT_SNAPSHOT_SUFFIX}"

    def snapshots_for(
        self,
        *,
        source_path: str | Path | None = None,
        document_key: str = "untitled",
    ) -> list[DocumentSnapshot]:
        """Return valid snapshots for a document, newest first."""
        folder = self._document_folder(source_path, document_key)
        if not folder.is_dir():
            return []

        snapshots = [
            snapshot
            for path in folder.glob(f"*{DOCUMENT_SNAPSHOT_SUFFIX}")
            if (snapshot := self.load_snapshot(path)) is not None
        ]
        return sorted(snapshots, key=lambda snapshot: snapshot.created_at, reverse=True)

    def load_snapshot(self, path: str | Path) -> DocumentSnapshot | None:
        """Load a snapshot file from disk."""
        snapshot_path = Path(path)
        try:
            content = snapshot_path.read_text(encoding="utf-8")
        except OSError:
            return None

        metadata = _parse_front_matter(content)
        if metadata.get("snapshot") != "true":
            return None

        document = MiniChordDocument.from_mchord(content)
        return DocumentSnapshot(
            path=snapshot_path,
            document=document,
            source_path=_source_path(metadata.get("source_path")),
            snapshot_id=metadata.get("snapshot_id") or snapshot_path.stem,
            created_at=_parse_datetime(metadata.get("snapshot_created_at"))
            or _mtime_datetime(snapshot_path),
            label=metadata.get("snapshot_label", ""),
            size=len(content.encode("utf-8")),
        )

    def discard(self, snapshot: DocumentSnapshot) -> None:
        """Delete a snapshot file."""
        with contextlib.suppress(FileNotFoundError):
            snapshot.path.unlink()

    def restore_to_path(self, snapshot: DocumentSnapshot, target_path: str | Path) -> Path:
        """Restore a document snapshot to a `.mchord` file."""
        path = Path(target_path)
        _write_text_atomic(path, snapshot.document.to_mchord())
        return path

    def prune_snapshots(
        self,
        *,
        source_path: str | Path | None = None,
        document_key: str = "untitled",
    ) -> None:
        """Keep only the newest configured number of snapshots for a document."""
        for old_snapshot in self.snapshots_for(
            source_path=source_path,
            document_key=document_key,
        )[self.snapshot_limit:]:
            self.discard(old_snapshot)

    def _document_folder(self, source_path: str | Path | None, document_key: str) -> Path:
        if source_path is not None:
            text = str(Path(source_path).expanduser().resolve(strict=False))
            prefix = "file"
        else:
            text = document_key.strip() or "untitled"
            prefix = "document"
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()[:20]
        return self.directory / f"{prefix}-{digest}"


class SongbookSnapshotManager:
    """Create, list, and discard timestamped songbook snapshots."""

    def __init__(
        self,
        directory: str | Path | None = None,
        snapshot_limit: int = DEFAULT_SONGBOOK_SNAPSHOT_LIMIT,
    ):
        self.directory = Path(directory) if directory is not None else default_songbook_snapshot_directory()
        self.snapshot_limit = max(1, snapshot_limit)

    def create_snapshot(
        self,
        songbook: MiniChordSongbook,
        *,
        source_path: str | Path | None = None,
        songbook_key: str = "untitled",
        label: str = "",
        snapshot_id: str | None = None,
        created_at: datetime | None = None,
    ) -> SongbookSnapshot:
        """Write a new songbook snapshot and return its metadata."""
        timestamp = created_at or datetime.now(UTC)
        resolved_snapshot_id = snapshot_id or uuid.uuid4().hex
        content = _serialize_songbook_snapshot(
            songbook,
            source_path=source_path,
            snapshot_id=resolved_snapshot_id,
            created_at=timestamp,
            label=label,
        )
        path = _unique_path(
            self.snapshot_path(
                songbook,
                source_path=source_path,
                songbook_key=songbook_key,
                snapshot_id=resolved_snapshot_id,
                created_at=timestamp,
            )
        )
        _write_text_atomic(path, content)
        self.prune_snapshots(source_path=source_path, songbook_key=songbook_key)
        return SongbookSnapshot(
            path=path,
            songbook=songbook,
            source_path=_source_path(source_path),
            snapshot_id=resolved_snapshot_id,
            created_at=timestamp,
            label=label,
            size=len(content.encode("utf-8")),
        )

    def snapshot_path(
        self,
        songbook: MiniChordSongbook,
        *,
        source_path: str | Path | None,
        songbook_key: str,
        snapshot_id: str,
        created_at: datetime,
    ) -> Path:
        """Return the preferred path for a songbook snapshot."""
        folder = self._songbook_folder(source_path, songbook_key)
        timestamp = _timestamp_text(created_at)
        title = _safe_filename(songbook.title or "Untitled Songbook")
        return folder / f"{timestamp}-{title}-{snapshot_id[:8]}{SONGBOOK_SNAPSHOT_SUFFIX}"

    def snapshots_for(
        self,
        *,
        source_path: str | Path | None = None,
        songbook_key: str = "untitled",
    ) -> list[SongbookSnapshot]:
        """Return valid songbook snapshots, newest first."""
        folder = self._songbook_folder(source_path, songbook_key)
        if not folder.is_dir():
            return []

        snapshots = [
            snapshot
            for path in folder.glob(f"*{SONGBOOK_SNAPSHOT_SUFFIX}")
            if (snapshot := self.load_snapshot(path)) is not None
        ]
        return sorted(snapshots, key=lambda snapshot: snapshot.created_at, reverse=True)

    def load_snapshot(self, path: str | Path) -> SongbookSnapshot | None:
        """Load a songbook snapshot file from disk."""
        snapshot_path = Path(path)
        try:
            content = snapshot_path.read_text(encoding="utf-8")
        except OSError:
            return None

        metadata, body = _parse_wrapped_content(content)
        if metadata.get("snapshot") != "true" or metadata.get("snapshot_kind") != "songbook":
            return None

        return SongbookSnapshot(
            path=snapshot_path,
            songbook=MiniChordSongbook.from_mchordbook(body),
            source_path=_source_path(metadata.get("source_path")),
            snapshot_id=metadata.get("snapshot_id") or snapshot_path.stem,
            created_at=_parse_datetime(metadata.get("snapshot_created_at"))
            or _mtime_datetime(snapshot_path),
            label=metadata.get("snapshot_label", ""),
            size=len(content.encode("utf-8")),
        )

    def discard(self, snapshot: SongbookSnapshot) -> None:
        """Delete a songbook snapshot file."""
        with contextlib.suppress(FileNotFoundError):
            snapshot.path.unlink()

    def restore_to_path(self, snapshot: SongbookSnapshot, target_path: str | Path) -> Path:
        """Restore a songbook snapshot to a `.mchordbook` file."""
        path = Path(target_path)
        _write_text_atomic(path, snapshot.songbook.to_mchordbook())
        return path

    def prune_snapshots(
        self,
        *,
        source_path: str | Path | None = None,
        songbook_key: str = "untitled",
    ) -> None:
        """Keep only the newest configured number of snapshots for a songbook."""
        for old_snapshot in self.snapshots_for(
            source_path=source_path,
            songbook_key=songbook_key,
        )[self.snapshot_limit:]:
            self.discard(old_snapshot)

    def _songbook_folder(self, source_path: str | Path | None, songbook_key: str) -> Path:
        if source_path is not None:
            text = str(Path(source_path).expanduser().resolve(strict=False))
            prefix = "file"
        else:
            text = songbook_key.strip() or "untitled"
            prefix = "songbook"
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()[:20]
        return self.directory / f"{prefix}-{digest}"


def default_snapshot_directory() -> Path:
    """Return the platform-specific document snapshot directory."""
    location = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation)
    if location:
        return Path(location) / "snapshots" / "documents"
    return Path.home() / ".local" / "share" / APPLICATION_NAME / "snapshots" / "documents"


def default_songbook_snapshot_directory() -> Path:
    """Return the platform-specific songbook snapshot directory."""
    location = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation)
    if location:
        return Path(location) / "snapshots" / "songbooks"
    return Path.home() / ".local" / "share" / APPLICATION_NAME / "snapshots" / "songbooks"


def _serialize_snapshot(
    document: MiniChordDocument,
    *,
    source_path: str | Path | None,
    snapshot_id: str,
    created_at: datetime,
    label: str,
) -> str:
    title = _metadata_value(document.title or "Untitled Song")
    text = document.text.rstrip("\n")
    metadata = {
        "format": "minichord-song",
        "version": str(document.version),
        "title": title,
        "snapshot": "true",
        "snapshot_kind": "document",
        "snapshot_created_at": created_at.isoformat(),
        "snapshot_id": snapshot_id,
    }
    if label:
        metadata["snapshot_label"] = label
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


def _serialize_songbook_snapshot(
    songbook: MiniChordSongbook,
    *,
    source_path: str | Path | None,
    snapshot_id: str,
    created_at: datetime,
    label: str,
) -> str:
    metadata = {
        "snapshot": "true",
        "snapshot_kind": "songbook",
        "snapshot_created_at": created_at.isoformat(),
        "snapshot_id": snapshot_id,
    }
    if label:
        metadata["snapshot_label"] = label
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


def _parse_wrapped_content(content: str) -> tuple[dict[str, str], str]:
    normalized = content.replace("\r\n", "\n").replace("\r", "\n")
    if not normalized.startswith(f"{FRONT_MATTER_DELIMITER}\n"):
        return {}, normalized

    parts = normalized.split(f"\n{FRONT_MATTER_DELIMITER}\n", 1)
    if len(parts) != 2:
        return {}, normalized

    metadata: dict[str, str] = {}
    metadata_block = parts[0].removeprefix(f"{FRONT_MATTER_DELIMITER}\n")
    for raw_line in metadata_block.splitlines():
        key, separator, value = raw_line.partition(":")
        if separator:
            metadata[key.strip()] = value.strip()
    return metadata, parts[1].lstrip("\n")


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


def _timestamp_text(value: datetime) -> str:
    timestamp = value.astimezone(UTC) if value.tzinfo is not None else value.replace(tzinfo=UTC)
    return timestamp.strftime("%Y%m%dT%H%M%S%fZ")


def _source_path(value: str | Path | None) -> Path | None:
    if not value:
        return None
    return Path(value)


def _metadata_value(value: str) -> str:
    return " ".join(str(value).splitlines()).strip()


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
