from datetime import UTC, datetime

from chordpages.autosave import AUTOSAVE_SUFFIX, AutosaveManager
from chordpages.document import ChordPagesDocument


def test_autosave_manager_writes_recoverable_mchord_draft(tmp_path):
    manager = AutosaveManager(tmp_path / "autosave")
    document = ChordPagesDocument(text="[C]Amazing grace", title="Amazing Grace")

    draft = manager.write(
        document,
        source_path=tmp_path / "song.mchord",
        draft_id="draft-1",
        saved_at=datetime(2026, 5, 27, 12, 0, tzinfo=UTC),
    )

    assert draft.path.suffixes[-2:] == [".autosave", ".mchord"]
    assert draft.path.name.endswith(AUTOSAVE_SUFFIX)
    assert draft.path.is_file()

    content = draft.path.read_text(encoding="utf-8")
    assert "format: chordpages-song" in content
    assert "autosave: true" in content
    assert "source_path:" in content
    assert "[C]Amazing grace" in content
    assert ChordPagesDocument.from_mchord(content).text == "[C]Amazing grace\n"


def test_autosave_manager_uses_stable_path_for_saved_document(tmp_path):
    manager = AutosaveManager(tmp_path / "autosave")
    source_path = tmp_path / "song.mchord"

    first_path = manager.autosave_path(source_path, "first-draft")
    second_path = manager.autosave_path(source_path, "second-draft")

    assert first_path == second_path


def test_autosave_manager_clears_draft(tmp_path):
    manager = AutosaveManager(tmp_path / "autosave")
    draft = manager.write(
        ChordPagesDocument(text="draft"),
        source_path=None,
        draft_id="untitled-1",
    )

    manager.clear(None, "untitled-1")

    assert not draft.path.exists()
