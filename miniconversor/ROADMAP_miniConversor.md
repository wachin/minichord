# miniConversor — ROADMAP

A tolerant and intelligent chord-sheet normalization tool written in Python + PyQt6.

miniConversor is designed to:
- import messy real-world chord sheets,
- understand internet chord formats,
- normalize inconsistent formatting,
- convert malformed chord sheets into clean semantic ChordPro,
- work together with miniChord.

Primary target:
- Debian 12
- MX Linux 23
- Windows 10/11
- macOS
- Python 3.11
- PyQt6

---

# Project Status

Current Phase:
- Planning / Architecture

Current Priorities:
- Import engine
- Heuristic parser
- Chord normalization
- Semantic reconstruction
- ChordPro generation

Long-Term Goal:
A professional open-source chord-sheet normalization and conversion tool for musicians and worship teams.

---

# Core Philosophy

miniConversor is NOT a strict parser.

It must behave as:
- a tolerant importer,
- a semantic reconstruction engine,
- a chord-sheet cleaner,
- a musical normalization system.

miniConversor should prioritize:
- tolerance,
- semantic understanding,
- user convenience,
over strict syntax validation.

---

# GLOBAL PROJECT CHECKLIST

## 0. Project Bootstrap

- [ ] Create project structure
- [ ] Configure Python package layout
- [ ] Add Debian/MX Linux installation instructions
- [ ] Add Windows installation instructions
- [ ] Add macOS installation instructions
- [ ] Add PyQt6 installation instructions
- [ ] Add About dialog
- [ ] Add translation infrastructure
- [ ] Add dark/light theme support
- [ ] Add autosave system
- [ ] Add crash recovery system
- [ ] Add settings manager
- [ ] Add logging system

---

# 1. USER INTERFACE

## 1.1 Main Window

- [ ] Split-pane interface
- [ ] Raw input panel (left)
- [ ] Generated ChordPro panel (right)
- [ ] Live conversion preview
- [ ] Responsive layout
- [ ] Adjustable splitter
- [ ] Toolbar
- [ ] Status bar
- [ ] Keyboard shortcuts

---

## 1.2 Input Features

- [ ] Paste-from-clipboard support
- [ ] Drag & drop support
- [ ] File open dialog
- [ ] Multi-file import
- [ ] Folder import
- [ ] UTF-8 support
- [ ] Encoding detection
- [ ] Line ending normalization

---

## 1.3 Output Features

- [ ] Copy-to-clipboard button
- [ ] Export `.cho`
- [ ] Export `.chordpro`
- [ ] Export `.pro`
- [ ] Export normalized plain text
- [ ] Save conversion session
- [ ] Preview final ChordPro

---

## 1.4 Visual Features

- [ ] Syntax highlighting
- [ ] Chord highlighting
- [ ] Metadata highlighting
- [ ] Error highlighting
- [ ] Section highlighting
- [ ] Warning markers
- [ ] Ambiguous detection markers
- [ ] Side-by-side comparison mode

---

# 2. HEURISTIC IMPORT ENGINE

miniConversor must use heuristic-based parsing.

The system should:
- infer song structure,
- infer chord placement,
- infer metadata,
- infer sections,
- infer formatting intent,
even from malformed input.

---

## 2.1 Real-World Import Dataset

miniConversor should maintain a large real-world chord sheet dataset for parser testing and normalization improvements.

The dataset should include:

- internet chord sheets,
- malformed chord sheets,
- legacy worship files,
- mixed formatting styles,
- multilingual songs,
- malformed ChordPro,
- chord-over-lyrics text,
- inline chord formats,
- tablature mixtures,
- copied web content.

### Dataset Goals

- [ ] Build parser regression test suite
- [ ] Build normalization test suite
- [ ] Build chord detection test suite
- [ ] Build malformed input test suite
- [ ] Build multilingual import tests
- [ ] Build large-scale import benchmarks

### Parser Robustness Philosophy

The parser should prioritize:

- musical understanding,
- semantic reconstruction,
- user convenience,
- tolerance of malformed formatting,
over strict syntax validation.

---

## 2.2 Supported Real-World Sources

- [ ] Ultimate Guitar style
- [ ] CifraClub style
- [ ] LaCuerda style
- [ ] e-Chords style
- [ ] WorshipTools exports
- [ ] SongSelect exports
- [ ] OpenLP exports
- [ ] Holyrics exports
- [ ] Chord-over-lyrics plain text
- [ ] Inline chord styles
- [ ] Mixed chord styles
- [ ] User-pasted internet content

---

## 2.3 Format Fingerprint System

miniConversor should recognize common internet chord-sheet styles.

### Supported Fingerprints

- [ ] CifraClub
- [ ] LaCuerda
- [ ] Ultimate Guitar
- [ ] e-Chords
- [ ] WorshipTools
- [ ] SongSelect
- [ ] OpenLP
- [ ] Holyrics

---

## 2.4 Chord Detection Features

- [ ] Detect chord lines
- [ ] Detect inline chords
- [ ] Detect chord blocks
- [ ] Detect repeated chorus sections
- [ ] Detect intros
- [ ] Detect bridges
- [ ] Detect tags
- [ ] Detect metadata
- [ ] Detect tonalities
- [ ] Detect capo information
- [ ] Detect section headers
- [ ] Detect repeated sections
- [ ] Detect malformed spacing
- [ ] Detect mixed tabs and lyrics

---

## 2.5 Chord Recognition Features

- [ ] Detect major chords
- [ ] Detect minor chords
- [ ] Detect seventh chords
- [ ] Detect slash chords
- [ ] Detect sus chords
- [ ] Detect add chords
- [ ] Detect diminished chords
- [ ] Detect augmented chords
- [ ] Detect Nashville notation
- [ ] Detect Roman numeral notation

---

## 2.6 Smart Chord Detection

miniConversor should intelligently detect traditional chord-over-lyrics text pasted by users.

The system should:
- detect chord lines automatically,
- detect lyric lines automatically,
- pair chords with lyrics,
- preserve visual alignment,
- convert internally into semantic chord structures,
- optionally export as clean ChordPro.

This feature is intended for:
- pasted text,
- legacy song sheets,
- copied internet content,
- old worship song files,
- manual editing workflows.

---

# 3. NORMALIZATION ENGINE

## 3.1 Safe Normalization

miniConversor should preserve musical meaning whenever possible.

Normalization should:
- preserve chord positioning,
- preserve lyrical meaning,
- preserve section boundaries,
- preserve repeated sections,
- preserve capo information,
- preserve tonalities,
while improving formatting consistency.

---

## 3.2 Normalization Features

- [ ] Normalize spacing
- [ ] Normalize chord alignment
- [ ] Normalize section names
- [ ] Normalize metadata
- [ ] Normalize empty lines
- [ ] Normalize repeated spaces
- [ ] Normalize tab indentation
- [ ] Normalize chord casing
- [ ] Normalize Unicode symbols
- [ ] Normalize quotation marks
- [ ] Normalize section headers

---

## 3.3 Semantic Import Pipeline

miniConversor should internally process imported songs using the following pipeline:

1. Raw text import
2. Format detection
3. Chord detection
4. Section detection
5. Metadata extraction
6. Chord normalization
7. Semantic song model conversion
8. Internal validation
9. ChordPro generation
10. Preview rendering

---

## 3.4 Conversion Confidence System

- [ ] Detect ambiguous chord lines
- [ ] Detect uncertain metadata
- [ ] Highlight low-confidence conversions
- [ ] Show parser warnings
- [ ] Show normalization suggestions
- [ ] Show unsupported constructs

---

# 4. INTERNAL SONG MODEL

## 4.1 Semantic Music Model

- [ ] Internal document object model (DOM)
- [ ] Song abstraction
- [ ] Verse abstraction
- [ ] Chorus abstraction
- [ ] Bridge abstraction
- [ ] Intro abstraction
- [ ] Outro abstraction
- [ ] Chord token abstraction
- [ ] Lyric syllable abstraction
- [ ] Metadata abstraction

---

## 4.2 Chord/Lyric Pair Model

- [ ] Chord/lyric paired line model
- [ ] Preserve chord alignment
- [ ] Preserve syllable association
- [ ] Chord-aware wrapping
- [ ] Chord-aware spacing
- [ ] Chord-aware line breaks

---

# 5. CHORDPRO GENERATION ENGINE

## 5.1 ChordPro Output

- [ ] Generate semantic ChordPro
- [ ] Generate normalized ChordPro
- [ ] Preserve metadata
- [ ] Preserve sections
- [ ] Preserve repeated blocks
- [ ] Preserve chord formatting
- [ ] Preserve transposition safety

---

## 5.2 Supported Directives

- [ ] {title:}
- [ ] {subtitle:}
- [ ] {comment:}
- [ ] {artist:}
- [ ] {album:}
- [ ] {key:}
- [ ] {tempo:}
- [ ] {capo:}
- [ ] {soc}
- [ ] {eoc}
- [ ] {start_of_verse}
- [ ] {end_of_verse}
- [ ] {start_of_bridge}
- [ ] {end_of_bridge}

---

# 6. VALIDATION SYSTEM

## 6.1 Validation Features

- [ ] Detect malformed chords
- [ ] Detect malformed directives
- [ ] Detect duplicated metadata
- [ ] Detect invalid section nesting
- [ ] Detect suspicious formatting
- [ ] Detect malformed Unicode
- [ ] Detect unsupported structures

---

## 6.2 Error Recovery

- [ ] Recover malformed sections
- [ ] Recover malformed directives
- [ ] Recover malformed spacing
- [ ] Recover malformed chord lines
- [ ] Recover malformed metadata

---

# 7. SPELLCHECK AND LANGUAGE SUPPORT

## 7.1 Spellcheck Features

- [ ] Hunspell integration
- [ ] Mythes integration
- [ ] Ignore chord symbols
- [ ] Ignore ChordPro directives
- [ ] Ignore metadata blocks
- [ ] Multi-language support
- [ ] Language detection

---

## 7.2 Supported Dictionaries

### Linux

Use system packages:
- hunspell
- mythes-es
- hunspell-es

### Windows/macOS

Use bundled dictionaries from:

https://github.com/wachin/libreoffice-dictionaries-collection

---

# 8. PERFORMANCE

- [ ] Large file support
- [ ] Incremental parsing
- [ ] Parser cache
- [ ] Chord recognition cache
- [ ] Partial reprocessing
- [ ] Lazy normalization
- [ ] Fast live preview
- [ ] Large dataset benchmarks

---

# 9. DATASET AND TESTING

## 9.1 Import Dataset Repository

miniConversor should maintain a separate public dataset repository for parser training and regression testing.

Suggested repository names:

- miniconversor-import-test-suite
- miniconversor-parser-dataset

---

## 9.2 Testing Goals

- [ ] Real-world parser tests
- [ ] Regression testing
- [ ] Multi-language testing
- [ ] Malformed input testing
- [ ] Stress testing
- [ ] Large-file testing
- [ ] Encoding compatibility testing

---

# 10. FUTURE FEATURES

- [ ] AI-assisted chord detection
- [ ] AI-assisted section detection
- [ ] AI-assisted metadata reconstruction
- [ ] OCR import support
- [ ] PDF chord-sheet import
- [ ] Image-based chord recognition
- [ ] Batch conversion mode
- [ ] Command-line interface
- [ ] miniChord direct integration

---

# 11. DEVELOPMENT PHASES

## Phase 1 — Minimal Prototype

- [ ] Split-pane UI
- [ ] Paste input
- [ ] Generate simple ChordPro
- [ ] Copy button
- [ ] Save `.cho`

---

## Phase 2 — Heuristic Parsing

- [ ] Chord detection
- [ ] Metadata detection
- [ ] Section detection
- [ ] Smart normalization

---

## Phase 3 — Real-World Compatibility

- [ ] CifraClub compatibility
- [ ] LaCuerda compatibility
- [ ] Ultimate Guitar compatibility
- [ ] e-Chords compatibility
- [ ] Holyrics compatibility

---

## Phase 4 — Validation + Recovery

- [ ] Error recovery
- [ ] Validation engine
- [ ] Confidence system
- [ ] Warning system

---

## Phase 5 — Optimization

- [ ] Performance optimization
- [ ] Large dataset testing
- [ ] Packaging
- [ ] Cross-platform releases

---

# FINAL GOAL

miniConversor should become:

- a professional chord-sheet normalization tool,
- a semantic ChordPro generator,
- a tolerant internet chord importer,
- a real-world chord parser,
- an ideal companion for miniChord.
