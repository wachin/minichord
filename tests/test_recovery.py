from datetime import UTC, datetime, timedelta

from minichord.autosave import AutosaveManager
from minichord.document import MiniChordDocument, MiniChordSongbook
from minichord.recovery import (
    RecoveryManager,
    SongbookAutosaveManager,
    SongbookRecoveryManager,
)


def test_recovery_manager_discovers_autosave_drafts_newest_first(tmp_path):
    autosave_manager = AutosaveManager(tmp_path / "autosave")
    older_time = datetime(2026, 5, 27, 12, 0, tzinfo=UTC)
    newer_time = older_time + timedelta(minutes=5)
    older_source = tmp_path / "older.mchord"
    newer_source = tmp_path / "newer.mchord"
    autosave_manager.write(
        MiniChordDocument(text="[C]Older", title="Older"),
        source_path=older_source,
        draft_id="older-draft",
        saved_at=older_time,
    )
    autosave_manager.write(
        MiniChordDocument(text="[G]Newer", title="Newer"),
        source_path=newer_source,
        draft_id="newer-draft",
        saved_at=newer_time,
    )

    drafts = RecoveryManager(autosave_manager).autosave_drafts()

    assert [draft.draft_id for draft in drafts] == ["newer-draft", "older-draft"]
    assert drafts[0].document.text == "[G]Newer\n"
    assert drafts[0].document.title == "Newer"
    assert drafts[0].source_path == newer_source.resolve(strict=False)
    assert drafts[0].saved_at == newer_time


def test_recovery_manager_ignores_non_autosave_files(tmp_path):
    autosave_manager = AutosaveManager(tmp_path / "autosave")
    autosave_manager.directory.mkdir(parents=True)
    (autosave_manager.directory / "unrelated.autosave.mchord").write_text(
        "not a minichord autosave",
        encoding="utf-8",
    )

    assert RecoveryManager(autosave_manager).autosave_drafts() == []


def test_recovery_manager_discards_autosave_draft(tmp_path):
    autosave_manager = AutosaveManager(tmp_path / "autosave")
    autosave_manager.write(
        MiniChordDocument(text="draft"),
        source_path=None,
        draft_id="untitled",
    )
    recovery_manager = RecoveryManager(autosave_manager)
    draft = recovery_manager.autosave_drafts()[0]

    recovery_manager.discard(draft)

    assert not draft.path.exists()
    assert not recovery_manager.has_recoverable_drafts()


def test_songbook_recovery_manager_discovers_autosave_drafts_newest_first(tmp_path):
    autosave_manager = SongbookAutosaveManager(tmp_path / "autosave")
    older_time = datetime(2026, 5, 27, 12, 0, tzinfo=UTC)
    newer_time = older_time + timedelta(minutes=5)
    older_source = tmp_path / "older.mchordbook"
    newer_source = tmp_path / "newer.mchordbook"
    autosave_manager.write(
        MiniChordSongbook(title="Older Book", songs=["older.mchord"]),
        source_path=older_source,
        draft_id="older-book-draft",
        saved_at=older_time,
    )
    autosave_manager.write(
        MiniChordSongbook(title="Newer Book", songs=["newer.mchord"]),
        source_path=newer_source,
        draft_id="newer-book-draft",
        saved_at=newer_time,
    )

    drafts = SongbookRecoveryManager(autosave_manager).autosave_drafts()

    assert [draft.draft_id for draft in drafts] == ["newer-book-draft", "older-book-draft"]
    assert drafts[0].songbook.title == "Newer Book"
    assert drafts[0].songbook.songs == ["newer.mchord"]
    assert drafts[0].source_path == newer_source.resolve(strict=False)
    assert drafts[0].saved_at == newer_time


def test_songbook_recovery_manager_ignores_document_autosave_files(tmp_path):
    directory = tmp_path / "autosave"
    document_manager = AutosaveManager(directory)
    songbook_manager = SongbookAutosaveManager(directory)
    document_manager.write(
        MiniChordDocument(text="draft"),
        source_path=None,
        draft_id="document-draft",
    )

    assert SongbookRecoveryManager(songbook_manager).autosave_drafts() == []


def test_songbook_recovery_manager_discards_autosave_draft(tmp_path):
    autosave_manager = SongbookAutosaveManager(tmp_path / "autosave")
    autosave_manager.write(
        MiniChordSongbook(title="Draft Book"),
        source_path=None,
        draft_id="untitled-book",
    )
    recovery_manager = SongbookRecoveryManager(autosave_manager)
    draft = recovery_manager.autosave_drafts()[0]

    recovery_manager.discard(draft)

    assert not draft.path.exists()
    assert not recovery_manager.has_recoverable_drafts()
