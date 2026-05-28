from datetime import UTC, datetime

from PyQt6.QtWidgets import QTextEdit

from minichord.autosave import AutosaveManager
from minichord.document import MiniChordDocument
from minichord.recovery import RecoveryManager
from minichord.ui.recovery_dialog import RecoveryDialog


def recovery_drafts(tmp_path):
    autosave_manager = AutosaveManager(tmp_path / "autosave")
    autosave_manager.write(
        MiniChordDocument(text="[C]Recovered text", title="Recovered Song"),
        source_path=tmp_path / "song.mchord",
        draft_id="draft-1",
        saved_at=datetime(2026, 5, 27, 12, 0, tzinfo=UTC),
    )
    return RecoveryManager(autosave_manager).autosave_drafts()


def test_recovery_dialog_selects_first_draft_and_shows_preview(qtbot, tmp_path):
    drafts = recovery_drafts(tmp_path)
    dialog = RecoveryDialog(drafts)
    qtbot.addWidget(dialog)

    preview = dialog.findChild(QTextEdit, "recoveryDraftPreview")

    assert dialog.selected_draft() == drafts[0]
    assert preview is not None
    assert preview.toPlainText() == "[C]Recovered text\n"


def test_recovery_dialog_records_recover_action(qtbot, tmp_path):
    dialog = RecoveryDialog(recovery_drafts(tmp_path))
    qtbot.addWidget(dialog)

    dialog.findChild(type(dialog._recover_button), "recoverDraftButton").click()

    assert dialog.result() == RecoveryDialog.DialogCode.Accepted
    assert dialog.selected_action() == RecoveryDialog.RECOVER_ACTION


def test_recovery_dialog_records_discard_action(qtbot, tmp_path):
    dialog = RecoveryDialog(recovery_drafts(tmp_path))
    qtbot.addWidget(dialog)

    dialog.findChild(type(dialog._discard_button), "discardDraftButton").click()

    assert dialog.result() == RecoveryDialog.DialogCode.Accepted
    assert dialog.selected_action() == RecoveryDialog.DISCARD_ACTION
