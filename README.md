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
- Row-based pagination that flows render rows through one or more columns while
  keeping chord/lyric segments together
- Manual page and column break directives in the structured layout engine
- Qt Linguist translation loading with initial English and Spanish catalogs

## Installation

miniChord is currently an early source-run prototype. Packaged installers are not
available yet, so install the platform dependencies, clone the repository, and
run the application from the checkout.

Clone the project on every platform:

```bash
git clone https://github.com/wachin/minichord.git
cd minichord
git submodule update --init --recursive
```

The submodule step prepares bundled dictionary resources for future Windows and
macOS spellcheck support.

### Debian / MX Linux

Primary development target:

- MX Linux 23 / Debian 12
- Python 3.11
- PyQt6

Install the known development packages:

```bash
sudo apt install \
  python3-pytest \
  python3-pytest-qt \
  python3-pyqt6 \
  qt6-translations-l10n \
  python3-pyqt6.qtsvg \
  python3-docx \
  pyqt6-dev-tools \
  qt6-l10n-tools \
  ripgrep \
  fd-find \
  python3-dev
```

Dependency reference files:

- [Debian 12 PyQt6 packages](packages_available_debian12_pyqt6.txt)
- [Debian 12 Python 3 packages](packages_available_debian12_python3.txt)

If development needs another Debian package, pause and install it with the
system package manager before continuing.

Run miniChord from the repository root:

```bash
python3 -m minichord
```

Run the test suite:

```bash
pytest -q
```

### Windows

Install Python 3.11 or newer and Git, then create a virtual environment from the
repository root:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install PyQt6 pytest
python -m pip install -e .
```

Run miniChord:

```powershell
python -m minichord
```

Run the test suite:

```powershell
pytest -q
```

### macOS

Install Python 3.11 or newer and Git, then create a virtual environment from the
repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install PyQt6 pytest
python -m pip install -e .
```

Run miniChord:

```bash
python -m minichord
```

Run the test suite:

```bash
pytest -q
```

## Run

```bash
python3 -m minichord
```

## Test

```bash
pytest -q
```

## Translation Workflow

miniChord keeps Qt Linguist source and compiled translation files under
`translations/`. Runtime startup loads `minichord_<locale>.qm` with
`QTranslator`, detects the default locale with `QLocale`, and also loads Qt's
native dialog translations from the Qt translations directory when available.
On Debian/MX Linux, native Qt dialog translations come from
`qt6-translations-l10n`.

Update translation source files after changing user-visible strings:

```bash
pylupdate6 minichord/ --ts translations/minichord_es.ts
pylupdate6 minichord/ --ts translations/minichord_en.ts
```

Edit translations with Qt Linguist, then compile `.qm` files:

```bash
linguist-qt6 translations/minichord_es.ts
lrelease translations/minichord_es.ts -qm translations/minichord_es.qm
lrelease translations/minichord_en.ts -qm translations/minichord_en.qm
```
