from datetime import UTC, datetime, timedelta

from chordpages.document import ChordPagesDocument, ChordPagesSongbook
from chordpages.snapshot import (
    DOCUMENT_SNAPSHOT_SUFFIX,
    SONGBOOK_SNAPSHOT_SUFFIX,
    DocumentSnapshotManager,
    SongbookSnapshotManager,
)


def test_document_snapshot_manager_creates_restorable_snapshot(tmp_path):
    manager = DocumentSnapshotManager(tmp_path / "snapshots")
    document = ChordPagesDocument(text="[C]Amazing grace", title="Amazing Grace")
    source_path = tmp_path / "song.mchord"
    created_at = datetime(2026, 5, 27, 12, 0, tzinfo=UTC)

    snapshot = manager.create_snapshot(
        document,
        source_path=source_path,
        label="Before transpose",
        snapshot_id="snapshot-1",
        created_at=created_at,
    )
    loaded = manager.load_snapshot(snapshot.path)

    assert snapshot.path.name.endswith(DOCUMENT_SNAPSHOT_SUFFIX)
    assert snapshot.path.is_file()
    assert loaded is not None
    assert loaded.document.title == "Amazing Grace"
    assert loaded.document.text == "[C]Amazing grace\n"
    assert loaded.source_path == source_path.resolve(strict=False)
    assert loaded.snapshot_id == "snapshot-1"
    assert loaded.created_at == created_at
    assert loaded.label == "Before transpose"


def test_document_snapshot_manager_keeps_newest_snapshots(tmp_path):
    manager = DocumentSnapshotManager(tmp_path / "snapshots", snapshot_limit=2)
    source_path = tmp_path / "song.mchord"
    document = ChordPagesDocument(text="version", title="Song")
    base_time = datetime(2026, 5, 27, 12, 0, tzinfo=UTC)

    first = manager.create_snapshot(
        document,
        source_path=source_path,
        snapshot_id="first",
        created_at=base_time,
    )
    second = manager.create_snapshot(
        document,
        source_path=source_path,
        snapshot_id="second",
        created_at=base_time + timedelta(minutes=1),
    )
    third = manager.create_snapshot(
        document,
        source_path=source_path,
        snapshot_id="third",
        created_at=base_time + timedelta(minutes=2),
    )

    snapshots = manager.snapshots_for(source_path=source_path)

    assert not first.path.exists()
    assert second.path.exists()
    assert third.path.exists()
    assert [snapshot.snapshot_id for snapshot in snapshots] == ["third", "second"]


def test_document_snapshot_manager_ignores_non_snapshot_files(tmp_path):
    manager = DocumentSnapshotManager(tmp_path / "snapshots")
    invalid_snapshot = tmp_path / "invalid.snapshot.mchord"
    invalid_snapshot.write_text("not a snapshot", encoding="utf-8")

    assert manager.snapshots_for() == []
    assert manager.load_snapshot(invalid_snapshot) is None


def test_document_snapshot_manager_discards_snapshot(tmp_path):
    manager = DocumentSnapshotManager(tmp_path / "snapshots")
    snapshot = manager.create_snapshot(
        ChordPagesDocument(text="draft", title="Draft"),
        document_key="draft",
        snapshot_id="snapshot-1",
    )

    manager.discard(snapshot)

    assert not snapshot.path.exists()
    assert manager.snapshots_for(document_key="draft") == []


def test_document_snapshot_manager_restores_snapshot_to_path(tmp_path):
    manager = DocumentSnapshotManager(tmp_path / "snapshots")
    target_path = tmp_path / "restored.mchord"
    snapshot = manager.create_snapshot(
        ChordPagesDocument(text="[F]Restored", title="Restored"),
        source_path=target_path,
        snapshot_id="snapshot-1",
    )

    manager.restore_to_path(snapshot, target_path)

    content = target_path.read_text(encoding="utf-8")
    assert "title: Restored" in content
    assert "[F]Restored" in content


def test_songbook_snapshot_manager_creates_restorable_snapshot(tmp_path):
    manager = SongbookSnapshotManager(tmp_path / "songbook-snapshots")
    songbook = ChordPagesSongbook(
        title="Sunday Morning",
        songs=["songs/amazing-grace.mchord"],
        column_count=2,
        index_enabled=True,
    )
    source_path = tmp_path / "sunday.mchordbook"
    created_at = datetime(2026, 5, 27, 12, 0, tzinfo=UTC)

    snapshot = manager.create_snapshot(
        songbook,
        source_path=source_path,
        label="Before reorder",
        snapshot_id="songbook-snapshot-1",
        created_at=created_at,
    )
    loaded = manager.load_snapshot(snapshot.path)

    assert snapshot.path.name.endswith(SONGBOOK_SNAPSHOT_SUFFIX)
    assert loaded is not None
    assert loaded.songbook.title == "Sunday Morning"
    assert loaded.songbook.songs == ["songs/amazing-grace.mchord"]
    assert loaded.songbook.column_count == 2
    assert loaded.songbook.index_enabled is True
    assert loaded.source_path == source_path.resolve(strict=False)
    assert loaded.snapshot_id == "songbook-snapshot-1"
    assert loaded.created_at == created_at
    assert loaded.label == "Before reorder"


def test_songbook_snapshot_manager_keeps_newest_snapshots(tmp_path):
    manager = SongbookSnapshotManager(tmp_path / "songbook-snapshots", snapshot_limit=2)
    source_path = tmp_path / "sunday.mchordbook"
    songbook = ChordPagesSongbook(title="Sunday Morning")
    base_time = datetime(2026, 5, 27, 12, 0, tzinfo=UTC)

    first = manager.create_snapshot(
        songbook,
        source_path=source_path,
        snapshot_id="first",
        created_at=base_time,
    )
    second = manager.create_snapshot(
        songbook,
        source_path=source_path,
        snapshot_id="second",
        created_at=base_time + timedelta(minutes=1),
    )
    third = manager.create_snapshot(
        songbook,
        source_path=source_path,
        snapshot_id="third",
        created_at=base_time + timedelta(minutes=2),
    )

    snapshots = manager.snapshots_for(source_path=source_path)

    assert not first.path.exists()
    assert second.path.exists()
    assert third.path.exists()
    assert [snapshot.snapshot_id for snapshot in snapshots] == ["third", "second"]


def test_songbook_snapshot_manager_ignores_document_snapshot_files(tmp_path):
    document_manager = DocumentSnapshotManager(tmp_path / "snapshots")
    songbook_manager = SongbookSnapshotManager(tmp_path / "snapshots")
    document_snapshot = document_manager.create_snapshot(
        ChordPagesDocument(text="draft", title="Draft"),
        source_path=tmp_path / "song.mchord",
        snapshot_id="document-snapshot",
    )

    assert songbook_manager.load_snapshot(document_snapshot.path) is None
    assert songbook_manager.snapshots_for(source_path=tmp_path / "song.mchordbook") == []


def test_songbook_snapshot_manager_restores_snapshot_to_path(tmp_path):
    manager = SongbookSnapshotManager(tmp_path / "songbook-snapshots")
    target_path = tmp_path / "restored.mchordbook"
    snapshot = manager.create_snapshot(
        ChordPagesSongbook(title="Restored Book", songs=["songs/restored.mchord"]),
        source_path=target_path,
        snapshot_id="songbook-snapshot-1",
    )

    manager.restore_to_path(snapshot, target_path)

    content = target_path.read_text(encoding="utf-8")
    assert "format: ChordPagesBook" in content
    assert "title: Restored Book" in content
    assert "  - songs/restored.mchord" in content
