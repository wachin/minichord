from pathlib import Path

from minichord.main_window import MainWindow


def test_main_window_starts_with_page_editor(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)

    assert window.windowTitle() == "miniChord - Untitled"
    assert window.editor.text() == ""


def test_main_window_saves_mchord_file(qtbot, tmp_path):
    window = MainWindow()
    qtbot.addWidget(window)
    path = Path(tmp_path) / "song.mchord"

    window.editor.set_text("[C]Amazing grace")
    window.save_path(path)

    content = path.read_text(encoding="utf-8")
    assert "format: minichord-song" in content
    assert "[C]Amazing grace" in content
