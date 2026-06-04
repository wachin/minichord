"""Dialog for recovering autosaved document drafts."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from chordpages.recovery import RecoveryDraft


class RecoveryDialog(QDialog):
    """Let the user choose an autosaved document draft to recover or discard."""

    RECOVER_ACTION = "recover"
    DISCARD_ACTION = "discard"
    CANCEL_ACTION = "cancel"

    def __init__(self, drafts: list[RecoveryDraft], parent: QWidget | None = None):
        super().__init__(parent)
        self._drafts = drafts
        self._selected_action = self.CANCEL_ACTION

        self.setWindowTitle(self.tr("Recover Autosaved Drafts"))
        self.resize(680, 460)

        self._summary_label = QLabel(self.tr("Autosaved drafts were found."))
        self._draft_list = QListWidget()
        self._draft_list.setObjectName("recoveryDraftList")
        self._draft_list.currentItemChanged.connect(self._update_preview)

        self._preview = QTextEdit()
        self._preview.setObjectName("recoveryDraftPreview")
        self._preview.setReadOnly(True)
        self._preview.setAcceptRichText(False)

        self._buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel)
        self._recover_button = self._buttons.addButton(
            self.tr("Recover"),
            QDialogButtonBox.ButtonRole.AcceptRole,
        )
        self._recover_button.setObjectName("recoverDraftButton")
        self._discard_button = self._buttons.addButton(
            self.tr("Discard"),
            QDialogButtonBox.ButtonRole.DestructiveRole,
        )
        self._discard_button.setObjectName("discardDraftButton")
        self._buttons.rejected.connect(self.reject)
        self._buttons.clicked.connect(self._handle_button_clicked)

        layout = QVBoxLayout(self)
        layout.addWidget(self._summary_label)
        layout.addWidget(self._draft_list, 2)
        layout.addWidget(self._preview, 3)
        layout.addWidget(self._buttons)

        self._populate_drafts()

    def selected_action(self) -> str:
        """Return the action chosen by the user."""
        return self._selected_action

    def selected_draft(self) -> RecoveryDraft | None:
        """Return the selected recovery draft."""
        item = self._draft_list.currentItem()
        if item is None:
            return None
        draft = item.data(Qt.ItemDataRole.UserRole)
        if isinstance(draft, RecoveryDraft):
            return draft
        return None

    def _populate_drafts(self) -> None:
        for draft in self._drafts:
            item = QListWidgetItem(_draft_label(draft, self.tr("Untitled Song")))
            item.setData(Qt.ItemDataRole.UserRole, draft)
            self._draft_list.addItem(item)

        if self._draft_list.count() > 0:
            self._draft_list.setCurrentRow(0)

    def _update_preview(self, current=None, previous=None) -> None:  # noqa: ANN001 - Qt signal
        draft = self.selected_draft()
        self._preview.setPlainText(draft.document.text if draft is not None else "")

    def _handle_button_clicked(self, button) -> None:  # noqa: ANN001 - Qt signal
        if button is self._recover_button:
            self._selected_action = self.RECOVER_ACTION
            self.accept()
            return
        if button is self._discard_button:
            self._selected_action = self.DISCARD_ACTION
            self.accept()


def _draft_label(draft: RecoveryDraft, default_title: str) -> str:
    title = draft.document.title or default_title
    saved_at = draft.saved_at.astimezone().strftime("%Y-%m-%d %H:%M:%S")
    if draft.source_path is None:
        return f"{title} - {saved_at}"
    return f"{title} - {draft.source_path.name} - {saved_at}"
