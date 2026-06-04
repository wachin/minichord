from datetime import UTC, datetime, timedelta

from chordpages.backup import BACKUP_SUFFIX, BackupManager


def test_backup_manager_snapshots_existing_file_bytes(tmp_path):
    source_path = tmp_path / "song.mchord"
    source_path.write_text("previous content\n", encoding="utf-8")
    manager = BackupManager(tmp_path / "backups")

    snapshot = manager.create_snapshot(
        source_path,
        created_at=datetime(2026, 5, 27, 12, 0, tzinfo=UTC),
    )

    assert snapshot is not None
    assert snapshot.path.name.endswith(BACKUP_SUFFIX)
    assert snapshot.path.read_text(encoding="utf-8") == "previous content\n"
    assert snapshot.source_path == source_path.resolve(strict=False)
    assert snapshot.size == len("previous content\n".encode("utf-8"))


def test_backup_manager_skips_missing_source_file(tmp_path):
    manager = BackupManager(tmp_path / "backups")

    snapshot = manager.create_snapshot(tmp_path / "missing.mchord")

    assert snapshot is None
    assert not (tmp_path / "backups").exists()


def test_backup_manager_keeps_newest_snapshots(tmp_path):
    source_path = tmp_path / "song.mchord"
    source_path.write_text("version\n", encoding="utf-8")
    manager = BackupManager(tmp_path / "backups", snapshot_limit=2)
    base_time = datetime(2026, 5, 27, 12, 0, tzinfo=UTC)

    first = manager.create_snapshot(source_path, created_at=base_time)
    second = manager.create_snapshot(source_path, created_at=base_time + timedelta(minutes=1))
    third = manager.create_snapshot(source_path, created_at=base_time + timedelta(minutes=2))

    assert first is not None
    assert second is not None
    assert third is not None
    assert not first.path.exists()
    assert second.path.exists()
    assert third.path.exists()
    assert manager.snapshots_for(source_path) == [third.path, second.path]
