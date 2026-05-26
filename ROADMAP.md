# miniChord — Roadmap

A lightweight but powerful WYSIWYG word processor written in Python + PyQt6.

Inspired by AbiWord, but designed to be:
- modular,
- Linux/Microsoft/macOS friendly
- optimized for worship songs and ChordPro,
- capable of professional page layout.

Primary target:
- Debian 12
- MX Linux 23
- Python 3.11
- PyQt6

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

- [ ] Create project structure
- [ ] Configure Python package layout
- [ ] Add Debian/MX Linux, Windows and macOS installation instructions
- [ ] Add PyQt6 installation instructions
- [ ] Add qt6-translations-l10n instructions
- [ ] Add SVG application icon
- [ ] Add About dialog
- [ ] Add settings manager
- [ ] Add translation infrastructure
- [ ] Add dark/light theme support
- [ ] Add crash-safe autosave (Data recovery strategies in case of power outages or unexpected crashes)

---

# 1. DOCUMENT ENGINE (MOST IMPORTANT)

## 1.1 Core Architecture

- [ ] Create custom page-based document engine
- [ ] Create document model abstraction
- [ ] Create page model abstraction
- [ ] Create layout engine abstraction
- [ ] Create pagination engine
- [ ] Create render pipeline
- [ ] Separate rendering from editing logic
- [ ] Separate visual layout from storage format
- [ ] Internal document object model (DOM)
- [ ] Song block abstraction
- [ ] Paragraph abstraction
- [ ] Chord line abstraction
- [ ] Layout tree abstraction
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
- [ ] independent pages,
- [ ] page spacing,
- [ ] page shadows,
- [ ] printable boundaries,
- [ ] true WYSIWYG page previews.
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

- [ ] Automatic page overflow handling
- [ ] Automatic page creation
- [ ] Text reflow between pages
- [ ] Paragraph splitting between pages
- [ ] Keep-with-next support
- [ ] Widow/orphan control
- [ ] Page break before paragraph
- [ ] Manual page breaks
- [ ] Soft page breaks
- [ ] Layout invalidation system
- [ ] Incremental re-layout optimization
- [ ] Stable pagination algorithm
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

- [ ] One column
- [ ] Two columns
- [ ] Three columns
- [ ] Custom column count
- [ ] Column spacing
- [ ] Column separator line
- [ ] Automatic flow to next column
- [ ] Automatic flow to next page
- [ ] Independent section columns
- [ ] Column-aware pagination
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

---

## 2.3 Tables

- [ ] Insert table
- [ ] Resize table
- [ ] Cell alignment
- [ ] Cell borders
- [ ] Cell background colors
- [ ] Merge cells
- [ ] Split cells

---

## 2.4 Images

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

- [ ] Create ChordPro parser
- [ ] Parse inline chords
- [ ] Parse directives
- [ ] Parse comments
- [ ] Parse metadata
- [ ] Parse traditional chord-over-lyrics text
- [ ] Convert chord-over-lyrics into internal chord model
- [ ] Preserve chord spacing from plain text files
- [ ] Detect chord lines automatically
- [ ] Detect lyric lines automatically
- [ ] Chord/lyric paired line model


### Required Directives

- [ ] {title:}
- [ ] {subtitle:}
- [ ] {comment:}
- [ ] {start_of_chorus}
- [ ] {end_of_chorus}
- [ ] {soc}
- [ ] {eoc}
- [ ] {key:}
- [ ] {tempo:}
- [ ] {artist:}
- [ ] {album:}
- [ ] {capo:}

---

## 3.2 WYSIWYG Chord Rendering

IMPORTANT:
Chords MUST visually align with lyrics.

### Rendering Requirements

- [ ] Monospaced chord alignment mode
- [ ] Smart chord positioning
- [ ] Chord-over-lyrics rendering
- [ ] Prevent chord overlap
- [ ] Dynamic spacing calculation
- [ ] Chord-aware word wrapping
- [ ] Chord-aware line breaks
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

- [ ] Menu bar
- [ ] Toolbar
- [ ] Status bar
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

---

# 8. PRINTING SYSTEM

- [ ] Native printing
- [ ] PDF export
- [ ] Print preview
- [ ] Multiple copies
- [ ] Duplex printing
- [ ] Booklet mode
- [ ] Songbook printing

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

- [ ] Main window
- [ ] Single A4 page
- [ ] Basic text editing
- [ ] Margins
- [ ] PDF export
- [ ] Native `.mchord` format

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
- [ ] ChordPro parser
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
- [ ] Prevent chord lines from separating from lyrics
- [ ] Keep chord/lyric blocks together
- [ ] Smart song block pagination  
- [ ] Keep verse blocks together when possible
- [ ] Keep chorus blocks together when possible
- [ ] Avoid page breaks inside short song sections
- [ ] Prefer section-aware pagination

## 11.3 ChordPro Song Index

After importing many ChordPro or chord-text songs, miniChord must be able to generate an index/table of contents using the song titles.

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

---

# FINAL GOAL

miniChord should become:

- a professional ChordPro editor,
- a worship song book creator,
- a real WYSIWYG page-layout editor,


