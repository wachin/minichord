# miniChord — Roadmap

A lightweight but powerful WYSIWYG word processor written in Python + PyQt6.

Inspired by AbiWord, but designed to be:
- modular,
- Linux/Windows/macOS friendly
- optimized for worship songs and ChordPro,
- capable of professional page layout.

Primary target:
- Debian 12, Debian 13
- MX Linux 23
- Ubuntu 24.04
- Python 3.11
- PyQt6

Development dependency references:
- [Debian 12 PyQt6 packages](packages_available_debian12_pyqt6.txt)
- [Debian 12 Python 3 packages](packages_available_debian12_python3.txt)

Currently installed development packages on MX Linux 23:
- `python3-pytest`
- `python3-pytest-qt`
- `python3-pyqt6`
- `qt6-translations-l10n`
- `python3-pyqt6.qtsvg`
- `python3-docx`
- `ripgrep`
- `fd-find`
- `python3-dev`

Dependency policy:
- Before adding a new runtime, development, testing, or packaging dependency, check the local Debian 12 package reference files above and the Debian 12 repositories.
- If a useful required package is available but not already installed, pause development and ask the developer to install it.
- Do not vendor or install system packages automatically during development.

# Project Status

Current Phase:
- Phase 1 — Minimal Working Prototype

Current Priorities:
- Document engine
- ChordPro rendering
- Pagination
- Git-friendly formats

Long-Term Goal:
A professional open-source WYSIWYG ChordPro editor for Linux, Windows, and macOS.

---

# Core Philosophy

miniChord is NOT a simple QTextEdit.

It must behave like a real page-oriented word processor:
- real pages,
- real margins,
- real layout engine,
- real pagination,
- real columns,
- real print preview,
- real WYSIWYG rendering.

The most important component of the entire project is:

# DOCUMENT LAYOUT ENGINE

The layout engine is the heart of the application.

Everything must be based on:
- page geometry,
- text flow,
- margin-aware rendering,
- multi-column layout,
- page reflow.

miniChord must include a music-aware layout system capable of:
- chord-aware pagination,
- section-aware rendering,
- song-aware text flow,
- chord/lyric pairing preservation,
- semantic music document layout.

**IMPORTANT:**

QTextDocument may be used as a helper component,
but miniChord MUST NOT rely entirely on QTextDocument
for pagination, columns, page layout, or ChordPro rendering.

The project must progressively evolve toward a custom
layout engine capable of professional page-oriented rendering.

---

# GLOBAL PROJECT CHECKLIST

## 0. Project Bootstrap

- [x] Create project structure
- [x] Configure Python package layout
- [ ] Add Debian/MX Linux, Windows and macOS installation instructions
- [x] Add PyQt6 installation instructions
- [x] Add qt6-translations-l10n instructions
- [ ] Add SVG application icon
- [ ] Add About dialog
- [ ] Add settings manager
- [ ] Add translation infrastructure
- [ ] Add dark/light theme support
- [ ] Add crash-safe autosave (Data recovery strategies in case of power outages or unexpected crashes)
- [ ] Automatic backup snapshots
- [ ] Document recovery manager
- [ ] Songbook recovery system
- [ ] Crash recovery dialog
- [ ] Document snapshot system
- [ ] Songbook version snapshots
- [ ] Restore previous snapshots


## 0.1 Internationalization with Qt Linguist

miniChord must support internationalization using Qt Linguist.

The application must use:
- Qt translation system
- `.ts` translation source files
- `.qm` compiled translation files
- `QTranslator`
- `QLocale`
- Qt Linguist workflow

### Requirements

- [ ] Wrap all user-visible strings with `self.tr()` or `QCoreApplication.translate()`
- [ ] Keep translation files under `translations/`
- [ ] Create initial Spanish translation file: `translations/minichord_es.ts`
- [ ] Create optional English translation file: `translations/minichord_en.ts`
- [ ] Compile `.ts` files into `.qm` files using `lrelease`
- [ ] Load `.qm` files at startup using `QTranslator`
- [ ] Detect system language using `QLocale`
- [ ] Allow manual language selection in Preferences
- [ ] Save selected language in settings
- [ ] Restart or reload UI after language change
- [ ] Use `qt6-translations-l10n` for native Qt dialogs on Linux
- [ ] Document the translation workflow in README

### Qt Linguist Workflow

```bash
# Generate or update TS translation files
pylupdate6 minichord/ -ts translations/minichord_es.ts

# Open translation file in Qt Linguist
linguist-qt6 translations/minichord_es.ts

# Compile TS to QM
lrelease translations/minichord_es.ts -qm translations/minichord_es.qm
```

### Translation File Structure

```text
translations/
├── minichord_es.ts
├── minichord_es.qm
├── minichord_en.ts
└── minichord_en.qm
```

---

# 1. DOCUMENT ENGINE (MOST IMPORTANT)

## 1.1 Core Architecture

- [ ] Create custom page-based document engine
- [ ] Create document model abstraction
- [ ] Create page model abstraction
- [x] Create layout engine abstraction
- [x] Create pagination engine
- [x] Create render pipeline
- [x] Separate rendering from editing logic
- [ ] Separate visual layout from storage format
- [ ] Internal document object model (DOM)
- [ ] Song block abstraction
- [ ] Paragraph abstraction
- [x] Chord line abstraction
- [x] Layout tree abstraction
- [ ] Internal song model
- [ ] Song section abstraction
- [ ] Verse abstraction
- [ ] Chorus abstraction
- [ ] Bridge abstraction
- [ ] Chord token abstraction
- [ ] Lyric syllable abstraction

---

## 1.2 Real Page System

miniChord MUST NOT use infinite scrolling editing.

It MUST render:
- independent pages
- page spacing
- page shadows
- printable boundaries
- true WYSIWYG page previews


### Rendering Features

- [ ] Printer safe area handling
- [ ] Non-printable margin visualization


### Required Page Features

- [ ] A4 support
- [ ] Letter support
- [ ] Legal support
- [ ] Custom page sizes
- [ ] Portrait orientation
- [ ] Landscape orientation
- [ ] Dynamic page resizing
- [ ] Page background rendering
- [ ] Page shadow rendering
- [ ] Multi-page vertical view
- [ ] Continuous page scrolling
- [ ] Print preview mode

### Orientation Behavior

- [ ] Dynamic portrait/landscape switching
- [ ] Instant page re-layout after orientation changes
- [ ] Column recalculation after orientation changes
- [ ] Margin recalculation after orientation changes
- [ ] Header/footer repositioning after orientation changes
- [ ] Landscape-aware print preview
- [ ] Mixed orientations inside the same document
- [ ] Section-based page orientation
- [ ] Orientation-aware pagination
- [ ] Orientation-aware rulers

### Page Templates

- [ ] Worship song template
- [ ] Songbook template
- [ ] Lyrics-only template
- [ ] Landscape rehearsal template
- [ ] Custom page templates

---

## 1.3 Margin System (VERY IMPORTANT)

Margins must behave like LibreOffice or AbiWord.

Changing margins MUST:
- instantly update the writable area,
- move the text frame,
- reflow the text,
- update columns,
- update headers and footers.

### Required Margin Features

- [ ] Left margin
- [ ] Right margin
- [ ] Top margin
- [ ] Bottom margin
- [ ] Mirror margins
- [ ] Gutter margin
- [ ] Header spacing
- [ ] Footer spacing

### Preset Margin Profiles

- [ ] Normal
- [ ] Narrow
- [ ] Moderate
- [ ] Wide
- [ ] Mirrored
- [ ] Custom margins

### Visual Behavior

- [ ] Writable text frame updates dynamically
- [ ] Text area visually moves after margin changes
- [ ] Rulers update automatically
- [ ] Columns adapt to new margins
- [ ] Headers adapt to new margins
- [ ] Footers adapt to new margins
- [ ] Pagination recalculates automatically

---

## 1.4 Text Flow Engine

- [x] Automatic page overflow handling
- [x] Automatic page creation
- [x] Text reflow between pages
- [ ] Paragraph splitting between pages
- [x] Keep-with-next support
- [ ] Widow/orphan control
- [ ] Page break before paragraph
- [ ] Manual page breaks
- [ ] Soft page breaks
- [ ] Layout invalidation system
- [ ] Incremental re-layout optimization
- [x] Stable pagination algorithm
- [ ] Prevent infinite layout recalculation loops
- [ ] Layout convergence validation

---

## 1.5 Multi-Column Engine

IMPORTANT:
ChordPro songs will frequently be printed in TWO COLUMNS on A4 paper.

The engine MUST support:
- newspaper-style text flow,
- balanced columns,
- automatic overflow to next column,
- automatic overflow to next page.

### Column Features

- [x] One column
- [x] Two columns
- [x] Three columns
- [x] Custom column count
- [ ] Column spacing
- [ ] Column separator line
- [x] Automatic flow to next column
- [x] Automatic flow to next page
- [ ] Independent section columns
- [x] Column-aware pagination
- [ ] Better column balancing in landscape mode
- [ ] Adaptive chord layout in landscape pages

---

## 1.6 Header/Footer System

- [ ] Header support
- [ ] Footer support
- [ ] Different first page
- [ ] Different odd/even pages
- [ ] Dynamic page numbering
- [ ] Current page field
- [ ] Total pages field
- [ ] Date field
- [ ] Time field
- [ ] Document title field

---

## 1.7 Zoom and View Modes

- [ ] Zoom in
- [ ] Zoom out
- [ ] Fit page
- [ ] Fit width
- [ ] Multiple page view
- [ ] Draft mode
- [ ] Print layout mode

---

## 1.8 Section Layout Engine

The document engine must support independent layout sections.

Each section may have:
- different margins,
- different column counts,
- different page orientation,
- different headers/footers,
- different spacing rules.

### Section Features

- [ ] Create document sections
- [ ] Section-based margins
- [ ] Section-based columns
- [ ] Section-based orientation
- [ ] Section-based headers/footers
- [ ] Section-aware pagination
- [ ] Section breaks
- [ ] Continuous section breaks
- [ ] Next-page section breaks
- [ ] Recalculate layout after section changes

---

# 2. TEXT EDITING SYSTEM

## 2.1 Rich Text Editing

- [ ] Bold
- [ ] Italic
- [ ] Underline
- [ ] Strikethrough
- [ ] Font family
- [ ] Font size
- [ ] Text color
- [ ] Background color
- [ ] Paragraph alignment
- [ ] Justification
- [ ] Line spacing
- [ ] Paragraph spacing
- [ ] Indentation
- [ ] Tab stops
- [ ] Bullet lists
- [ ] Numbered lists

## 2.1.1 Style System

miniChord must support reusable semantic document styles.

### Style Features

- [ ] Paragraph styles
- [ ] Character styles
- [ ] Song section styles
- [ ] Chord styles
- [ ] Verse styles
- [ ] Chorus styles
- [ ] Bridge styles
- [ ] Page styles
- [ ] Style inheritance
- [ ] Style presets
- [ ] User-defined styles
- [ ] Style import/export
- [ ] Theme-aware styles

### Print Style Profiles

miniChord should support different visual profiles depending on printing needs.

### Black & White Profiles

- [ ] Ink-saving print profile
- [ ] High-contrast monochrome profile
- [ ] Optimized laser printer profile
- [ ] Compact worship songbook profile
- [ ] Chord readability optimization

### Color Profiles

- [ ] Colored chord rendering
- [ ] Colored section headings
- [ ] Colored song titles
- [ ] Colored metadata
- [ ] Theme-based songbook styles
- [ ] User-defined color themes

### Accessibility Features

- [ ] High-contrast accessibility mode
- [ ] Colorblind-friendly palettes
- [ ] Monochrome compatibility validation

---

## 2.2 Advanced Editing

- [ ] Undo/redo
- [ ] Clipboard support
- [ ] Multi-level undo history
- [ ] Find
- [ ] Replace
- [ ] Replace all
- [ ] Spellcheck integration
- [ ] Word count
- [ ] Character count
- [ ] Command-based undo system
- [ ] Undo grouping
- [ ] Layout-aware undo
- [ ] Chord-aware undo

## 2.3 Spellcheck and Thesaurus System

miniChord must include a cross-platform spellcheck and thesaurus system.

The system must support:
- spell checking,
- word suggestions,
- synonym lookup,
- language selection,
- Linux system dictionaries,
- bundled dictionaries on Windows and macOS.

### Linux Dictionary Backend

On Linux, miniChord should use dictionaries installed from the system repositories.

Recommended Debian/MX Linux packages:

- `hunspell`
- `hunspell-es`
- `myspell-es`
- `mythes-es`

Linux dictionary search paths:

- `/usr/share/hunspell`
- `/usr/share/myspell/dicts`
- `/usr/share/mythes`

Required Linux features:

- [ ] Detect installed Hunspell dictionaries
- [ ] Detect installed Mythes thesaurus files
- [ ] Use `.aff` and `.dic` files for spell checking
- [ ] Use `.dat` and `.idx` files for synonyms
- [ ] Prefer Spanish Ecuador when available
- [ ] Fall back to Spanish Spain or generic Spanish when needed
- [ ] Allow choosing spellcheck language
- [ ] Allow choosing thesaurus language

### Windows and macOS Dictionary Backend

On Windows and macOS, miniChord should use bundled LibreOffice dictionaries from:

```bash
git clone https://github.com/wachin/minichord
cd minichord
git submodule update --init --recursive
```

because the project uses this Git submodule:

```
[submodule "third-party/libreoffice-dictionaries-collection"]
	path = third-party/libreoffice-dictionaries-collection
	url = https://github.com/wachin/libreoffice-dictionaries-collection
```

Required Windows/macOS features:

- [ ] Support bundled Hunspell dictionaries
- [ ] Support bundled Mythes thesaurus files
- [ ] Search dictionaries inside the application data folder
- [ ] Allow the user to configure an external dictionary folder
- [ ] Support the LibreOffice dictionary folder structure
- [ ] Support Spanish dictionaries such as `es_EC`, `es_ES`, `es_MX`, etc.
- [ ] Support thesaurus files such as `th_es_v2.dat` and `th_es_v2.idx`

#### Third-Party Resources

- [ ] Use Git submodules for bundled dictionaries
- [ ] Store bundled dictionaries under `third-party/`
- [ ] Support optional external dictionary repositories
- [ ] Detect missing submodules at startup
- [ ] Show warning if dictionaries are not initialized


### Spellcheck Features

- [ ] Underline misspelled words
- [ ] Ignore ChordPro directives
- [ ] Ignore chord symbols such as `G`, `D/F#`, `Asus4`, `Bm7`
- [ ] Ignore metadata fields such as `{title:}`, `{artist:}`, `{key:}`
- [ ] Ignore section markers such as `{soc}` and `{eoc}`
- [ ] Show suggestions in context menu
- [ ] Replace misspelled word with suggestion
- [ ] Ignore once
- [ ] Add word to personal dictionary
- [ ] Disable spellcheck per document
- [ ] Disable spellcheck per songbook

### Thesaurus Features

- [ ] Show synonyms for selected word
- [ ] Replace selected word with synonym
- [ ] Support Mythes `.dat` and `.idx` files
- [ ] Reuse the thesaurus logic from `chord_autoscroll.py`
- [ ] Cache thesaurus entries for performance
- [ ] Show thesaurus language in dialog title
- [ ] Allow changing thesaurus language from the dialog

### Personal Dictionaries

- [ ] Store user-added words
- [ ] Store ignored words
- [ ] Support per-language personal dictionaries
- [ ] Keep personal dictionaries in a Git-friendly text format

---

## 2.4 Tables

- [ ] Insert table
- [ ] Resize table
- [ ] Cell alignment
- [ ] Cell borders
- [ ] Cell background colors
- [ ] Merge cells
- [ ] Split cells

---

## 2.5 Images

- [ ] Insert images
- [ ] Resize images
- [ ] Inline images
- [ ] Floating images
- [ ] Image wrapping
- [ ] SVG support
- [ ] PNG support
- [ ] JPEG support

---

# 3. CHORDPRO ENGINE (VERY IMPORTANT)

This is one of the MAIN PURPOSES of miniChord.

miniChord must support:
- worship songs,
- guitar chords,
- printable chord sheets,
- WYSIWYG ChordPro rendering.

---

## 3.1 ChordPro Parser

- [x] Create ChordPro parser
- [x] Parse inline chords
- [x] Parse directives
- [x] Parse comments
- [x] Parse metadata
- [x] Parse traditional chord-over-lyrics text
- [x] Convert chord-over-lyrics into internal chord model
- [x] Preserve chord spacing from imported chord sheets
- [x] Detect chord lines automatically
- [x] Detect lyric lines automatically
- [x] Chord/lyric paired line model


### Required Directives

- [x] {title:}
- [x] {subtitle:}
- [x] {comment:}
- [x] {start_of_chorus}
- [x] {end_of_chorus}
- [x] {soc}
- [x] {eoc}
- [x] {key:}
- [x] {tempo:}
- [x] {artist:}
- [x] {album:}
- [x] {capo:}

---

## 3.2 WYSIWYG Chord Rendering

IMPORTANT:
Chords MUST visually align with lyrics.


### Chord Font System

- [ ] Independent chord font settings
- [ ] Independent lyric font settings
- [ ] Chord baseline offset adjustment
- [x] Chord spacing compensation
- [x] Chord collision avoidance

### Rendering Requirements

- [x] Monospaced chord alignment mode
- [ ] Smart chord positioning
- [x] Chord-over-lyrics rendering
- [x] Prevent chord overlap
- [x] Dynamic spacing calculation
- [x] Chord-aware word wrapping
- [x] Chord-aware line breaks
- [ ] Print-accurate rendering
- [ ] Real font metrics calculation
- [ ] Pixel-accurate chord positioning
- [ ] Font fallback handling
- [ ] Monospaced rendering optimization
- [ ] Mixed-font alignment handling

---

## 3.3 ChordPro Editing

- [ ] Live preview
- [ ] Split editor/preview mode
- [ ] Inline WYSIWYG editing
- [ ] Syntax highlighting
- [ ] Directive autocomplete
- [ ] Chord autocomplete
- [ ] Chord transposition
- [ ] Non-destructive chord editing
- [ ] Preserve original spacing when possible
- [ ] Preserve semantic song structure during edits

### Chord Transposition Engine

- [ ] Detect musical keys
- [ ] Detect major/minor keys
- [ ] Detect slash chords
- [ ] Detect chord modifiers
- [ ] Support Nashville notation
- [ ] Support sharp/flat preferences
- [ ] Transpose entire songs
- [ ] Transpose selected sections
- [ ] Preserve chord formatting after transposition
- [ ] Chord-aware spacing recalculation
- [ ] Automatic chord alignment after transposition
- [ ] Capo-aware transposition

---

## 3.4 ChordPro Printing

- [ ] A4 two-column song printing
- [ ] Automatic flow between columns
- [ ] Automatic flow between pages
- [ ] Song section styling
- [ ] Chorus highlighting
- [ ] Configurable chord colors
- [ ] Page numbering
- [ ] Song index generation

---

# 4. FILE FORMAT SYSTEM

miniChord must use fully text-based, Git-friendly formats.

The native formats MUST:
- be human-readable,
- work well with GitHub,
- support clean diffs,
- support merge operations,
- avoid binary containers,
- avoid opaque ZIP-based document formats,
- preserve semantic music structure.

miniChord should follow a philosophy closer to:
- FODT,
- Markdown,
- YAML,
- LaTeX,
- Typst,
- Jekyll,
than traditional binary office documents.

---

## 4.1 Native Formats

miniChord must use two native formats:

### `.mchord`

A reusable single-song document format.

Used for:
- individual songs,
- version control,
- song libraries,
- reusable worship songs,
- ChordPro-based editing.

### `.mchordbook`

A multi-song project/songbook format.

Used for:
- complete worship songbooks,
- page layout,
- printing configuration,
- indexes,
- multi-song organization,
- reusable song collections.

Both formats MUST:
- be fully text-based,
- GitHub-friendly,
- diff-friendly,
- merge-friendly,
- editable with normal text editors.

---

## 4.2 `.mchord` Format Requirements

The `.mchord` format must:

- [ ] Be text-based
- [ ] Use YAML front matter
- [ ] Store original ChordPro source
- [ ] Store parsed song structure
- [ ] Store metadata
- [ ] Store song sections
- [ ] Store rendering settings
- [ ] Store transposition settings
- [ ] Support comments
- [ ] Support UTF-8
- [ ] Support Git-friendly diffs

### Example Structure

```yaml
---
title: Vine a adorarte
artist: Kayros
key: G
tempo: 72
---

{soc}
[G]Vine a adorarte
[D]Vine a postrarme
{eoc}
```

---

## 4.3 `.mchordbook` Format Requirements

The `.mchordbook` format must:

- [ ] Be text-based
- [ ] Use YAML structure
- [ ] Reference multiple `.mchord` files
- [ ] Store page layout configuration
- [ ] Store column configuration
- [ ] Store margin configuration
- [ ] Store orientation configuration
- [ ] Store song ordering
- [ ] Store index settings
- [ ] Support reusable song libraries
- [ ] Support Git-friendly diffs

### Example Structure

```yaml
format: miniChordBook
version: 1

page:
  size: A4
  orientation: portrait
  margins: narrow

columns:
  count: 2

songs:
  - songs/vine-a-adorarte.mchord
  - songs/perfume-a-tus-pies.mchord

index:
  enabled: true
  position: beginning
```

---

## 4.4 Import/Export

- [ ] HTML import/export
- [ ] PDF export
- [ ] ChordPro import/export
- [ ] Markdown export
- [ ] `.mchord` import/export
- [ ] `.mchordbook` import/export

---

## 4.5 Future Format Architecture

- [ ] RTF plugin architecture
- [ ] DOCX plugin architecture
- [ ] ODT plugin architecture
- [ ] FODT plugin architecture

---

## 4.6 Song Library Philosophy

miniChord must support reusable song libraries.

A single `.mchord` file may be reused across multiple `.mchordbook` projects.

Example:

- SundayMorning.mchordbook
- YouthService.mchordbook
- ChristmasSongs.mchordbook

may all reference the same reusable song files.

---

## 4.7 GitHub Workflow Support

miniChord formats must work well with:

- Git
- GitHub
- GitLab
- code review
- pull requests
- collaborative editing
- version history

The formats should prioritize:
- semantic readability,
- minimal diff noise,
- stable formatting,
- deterministic serialization.

---

# 5. MACRO SYSTEM

## 5.1 Secure Macro Engine

Macros must be:
- powerful,
- scriptable,
- sandboxed.

### Requirements

- [ ] Python macro execution
- [ ] Sandbox system
- [ ] Trusted macro list
- [ ] Macro permissions
- [ ] Macro warning dialog
- [ ] Safe execution mode
- [ ] Advanced/unsafe mode
- [ ] Macro API abstraction

---

## 5.2 Macro API

- [ ] document.get_text()
- [ ] document.set_text()
- [ ] document.insert_text()
- [ ] document.find()
- [ ] document.replace_all()
- [ ] document.export_pdf()
- [ ] document.current_page()
- [ ] document.page_count()

---

## 5.3 Macro Manager

- [ ] Macro browser
- [ ] Macro editor
- [ ] Macro execution dialog
- [ ] Macro keyboard shortcuts
- [ ] Macro toolbar

---

# 6. UI SYSTEM

## 6.1 Main Window

- [x] Menu bar
- [x] Toolbar
- [x] Status bar
- [ ] Sidebar
- [ ] Page navigator

---

## 6.2 Rulers

- [ ] Horizontal ruler
- [ ] Vertical ruler
- [ ] Margin markers
- [ ] Tab markers
- [ ] Indent markers

---

## 6.3 Dock Widgets

- [ ] Styles panel
- [ ] Chord panel
- [ ] Macro panel
- [ ] Document outline
- [ ] Song metadata panel

---

# 7. PERFORMANCE

- [ ] Lazy page rendering
- [ ] Incremental pagination
- [ ] Cached layouts
- [ ] Large document optimization
- [ ] Fast scrolling
- [ ] Memory optimization
- [ ] Glyph metrics cache
- [ ] Chord layout cache
- [ ] Page render cache
- [ ] Incremental repaint system
- [ ] Partial document redraw
- [ ] Song metadata index
- [ ] Fast song search index
- [ ] Incremental document indexing

---

# 8. PRINTING SYSTEM

- [ ] Native printing
- [ ] PDF export
- [ ] Print preview
- [ ] Multiple copies
- [ ] Duplex printing
- [ ] Booklet mode
- [ ] Songbook printing
- [ ] Export complete songbooks to PDF
- [ ] Export song indexes to PDF
- [ ] Preserve clickable index links in exported PDF
- [ ] Preserve multi-column layout in exported PDF
- [ ] Preserve headers/footers in exported PDF
- [ ] Black-and-white print optimization
- [ ] Ink-saving rendering mode
- [ ] Grayscale conversion preview
- [ ] Printer-friendly monochrome mode
- [ ] Preserve readability without colors

---

# 9. FUTURE FEATURES

- [ ] Music notation support
- [ ] MIDI chord playback
- [ ] Holyrics compatibility
- [ ] OpenLP compatibility
- [ ] Songbook manager
- [ ] Cloud synchronization
- [ ] Collaborative editing

---

# 10. DEVELOPMENT PHASES

## Phase 1 — Minimal Working Prototype

- [x] Main window
- [x] Single A4 page
- [x] Basic text editing
- [x] Margins
- [x] PDF export
- [x] Native `.mchord` format

---

## Phase 2 — Real Pagination

- [ ] Multi-page support
- [ ] Dynamic page creation
- [ ] Text reflow
- [ ] Manual page breaks
- [ ] Zoom

---

## Phase 3 — Columns + ChordPro

- [ ] Two-column layout
- [x] ChordPro parser
- [ ] Chord rendering
- [ ] WYSIWYG chord display
- [ ] Song printing

---

## Phase 4 — Advanced Layout

- [ ] Headers
- [ ] Footers
- [ ] Page numbering
- [ ] Tables
- [ ] Images
- [ ] Styles
- [ ] Spellcheck system
- [ ] Thesaurus system

---

## Phase 5 — Macro System

- [ ] Sandbox engine
- [ ] Macro API
- [ ] Macro manager
- [ ] Trusted macros

---

## Phase 6 — Optimization

- [ ] Performance optimization
- [ ] Large document support
- [ ] Rendering cache
- [ ] Packaging

---

# 11. SONGBOOK / MULTI-FILE CHORDPRO IMPORT SYSTEM

miniChord must support creating complete worship songbooks from many ChordPro files.
Plain `.txt` chord-over-lyrics conversion is handled by a separate tool:
https://github.com/wachin/txt-to-chordpro-converter

The user may have 50, 100, or more song files. The program must allow importing all of them at once and placing them into the same document using the selected page layout.

## 11.1 Multiple ChordPro File Import

- [ ] Add “Import Multiple Song Files…” action
- [ ] Allow selecting many `.cho`, `.chordpro`, and `.pro` files at once
- [ ] Allow importing an entire folder of song files
- [ ] Detect song title from the first line
- [ ] Detect artist/subtitle from the second line when available
- [ ] Detect key from filename when available, for example `(A)` or `(G)`
- [ ] Convert ChordPro files into internal song blocks
- [ ] Insert each imported song as a separate song section
- [ ] Optionally start each song on a new page
- [ ] Optionally allow songs to continue in the next column/page
- [ ] Show import preview before final insertion
- [ ] Report files that could not be imported
- [ ] Detect duplicated song titles
- [ ] Detect duplicated song IDs
- [ ] Resolve metadata conflicts
- [ ] Warn about conflicting song versions

## 11.2 Songbook Layout

- [ ] Support A4 portrait songbook layout
- [ ] Support A4 landscape songbook layout
- [ ] Support two-column songbook layout
- [ ] Support narrow margins for songbooks
- [ ] Automatically flow each song from column 1 to column 2
- [ ] Automatically continue long songs on the next page
- [ ] Keep song titles with the first lines of the song
- [ ] Avoid leaving a song title alone at the bottom of a column
- [ ] Allow compact spacing for worship chord sheets
- [ ] Allow monospaced font for chord alignment
- [ ] Allow custom song title style
- [ ] Allow custom section heading style
- [ ] Allow custom chord style
- [ ] Prevent chorus split across columns when possible
- [x] Prevent chord lines from separating from lyrics
- [x] Keep chord/lyric blocks together
- [ ] Smart song block pagination  
- [ ] Keep verse blocks together when possible
- [ ] Keep chorus blocks together when possible
- [ ] Avoid page breaks inside short song sections
- [ ] Prefer section-aware pagination

## 11.3 ChordPro Song Index

After importing many ChordPro songs, miniChord must be able to generate an index/table of contents using the song titles.

- [ ] Add “Insert Song Index” feature
- [ ] Generate index from imported song titles
- [ ] Use ChordPro `{title:}` directive when available
- [ ] Use first line as title when `{title:}` is not available
- [ ] Include page number for each song
- [ ] Update page numbers after layout changes
- [ ] Allow alphabetical song index
- [ ] Allow document-order song index
- [ ] Allow index at beginning of document
- [ ] Allow index at end of document
- [ ] Allow refreshing/rebuilding the index
- [ ] Preserve links between index entries and song sections
- [ ] Optional: clickable index entries inside exported PDF

## 11.4 Song Metadata

- [ ] Store song title
- [ ] Store artist
- [ ] Store original filename
- [ ] Store key
- [ ] Store capo
- [ ] Store tempo
- [ ] Store song order
- [ ] Store ChordPro directives

## 11.5 Song Repository Support

- [ ] Support reusable song repositories
- [ ] Support external song folders
- [ ] Support relative song paths
- [ ] Support Git-managed song collections
- [ ] Detect modified songs automatically
- [ ] Reload updated songs from disk
- [ ] Preserve references between `.mchordbook` and `.mchord`
- [ ] File system watching
- [ ] Auto-reload modified songs
- [ ] Detect external Git updates
- [ ] Detect merge conflicts

---

# 12. DOCUMENTATION SYSTEM

- [ ] Developer documentation
- [ ] User manual
- [ ] ChordPro documentation
- [ ] Plugin API documentation
- [ ] Macro API documentation
- [ ] Translation workflow documentation
- [ ] Packaging documentation

---

# FINAL GOAL

miniChord should become:

- a professional WYSIWYG ChordPro editor,
- a semantic music document engine,
- a worship songbook publishing system,
- a Git-friendly music document platform,
- a professional chord-sheet layout engine,
- a reusable songbook composition system,
- a Linux-friendly open-source alternative for worship musicians,
- a modern music-aware publishing application.
