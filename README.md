# miniChord

miniChord is an early PyQt6 prototype for a page-oriented WYSIWYG ChordPro
editor and worship songbook layout tool.

## Current Prototype

- A main window with File actions
- A visible A4 page editing surface
- Basic text editing through Qt
- Page margins in the editor surface
- Save/load support for the initial text-based `.mchord` format
- PDF export through Qt printing
- Plain-Python ChordPro parser foundation for metadata, directives, inline chords,
  and traditional chord-over-lyrics text
- Monospaced chord-over-lyrics renderer with basic chord collision avoidance
- Chord-aware renderer wrapping for narrow columns and future pagination
- Structured ChordPro render rows for future page, column, and paint layout
- Row-based pagination that flows render rows through one or more columns

## Debian / MX Linux Setup

Primary development target:

- MX Linux 23 / Debian 12
- Python 3.11
- PyQt6

Known installed development packages:

```bash
sudo apt install \
  python3-pytest \
  python3-pytest-qt \
  python3-pyqt6 \
  qt6-translations-l10n \
  python3-pyqt6.qtsvg \
  python3-docx \
  ripgrep \
  fd-find \
  python3-dev
```

Dependency reference files:

- [Debian 12 PyQt6 packages](packages_available_debian12_pyqt6.txt)
- [Debian 12 Python 3 packages](packages_available_debian12_python3.txt)

If development needs another Debian package, pause and install it with the
system package manager before continuing.

## Run

```bash
python3 -m minichord
```

## Test

```bash
pytest -q
```
