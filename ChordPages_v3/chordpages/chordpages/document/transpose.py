"""Chord transposition helpers for text and ChordPro-like documents."""

from __future__ import annotations

import re


NOTE_NAMES = [
    ("C",),
    ("C#", "Db"),
    ("D",),
    ("D#", "Eb"),
    ("E",),
    ("F",),
    ("F#", "Gb"),
    ("G",),
    ("G#", "Ab"),
    ("A",),
    ("A#", "Bb"),
    ("B",),
]

NOTE_TO_INDEX = {
    note: index
    for index, names in enumerate(NOTE_NAMES)
    for note in names
}

CHORD_RE = re.compile(
    r"^(?P<root>[A-G])(?P<accidental>#|b)?"
    r"(?P<suffix>(?:m|maj|min|dim|aug|sus|add|M)?"
    r"(?:[0-9]+)?(?:[#b][0-9]+)*(?:/[A-G](?:#|b)?)?)$"
)

INLINE_CHORD_RE = re.compile(r"\[([^\[\]]+)\]")
TOKEN_RE = re.compile(r"(?<!\w)([A-G](?:#|b)?(?:m|maj|min|dim|aug|sus|add|M)?(?:[0-9]+)?(?:[#b][0-9]+)*(?:/[A-G](?:#|b)?)?)(?!\w)")


def transpose_text(text: str, semitones: int, use_sharps: bool = True) -> str:
    """Transpose ChordPro inline chords and traditional chord-only lines."""
    lines = text.split("\n")
    return "\n".join(
        _transpose_line(line, semitones, use_sharps)
        for line in lines
    )


def _transpose_line(line: str, semitones: int, use_sharps: bool) -> str:
    if "[" in line and "]" in line:
        return INLINE_CHORD_RE.sub(
            lambda match: f"[{transpose_chord(match.group(1), semitones, use_sharps)}]",
            line,
        )

    if not _is_chord_line(line):
        return line

    return TOKEN_RE.sub(
        lambda match: transpose_chord(match.group(1), semitones, use_sharps),
        line,
    )


def transpose_chord(chord: str, semitones: int, use_sharps: bool = True) -> str:
    match = CHORD_RE.fullmatch(chord.strip())
    if match is None:
        return chord

    root = f"{match.group('root')}{match.group('accidental') or ''}"
    suffix = match.group("suffix") or ""
    transposed_root = transpose_note(root, semitones, use_sharps)
    suffix = _transpose_slash_bass(suffix, semitones, use_sharps)
    return f"{transposed_root}{suffix}"


def transpose_note(note: str, semitones: int, use_sharps: bool = True) -> str:
    index = NOTE_TO_INDEX.get(note)
    if index is None:
        return note
    names = NOTE_NAMES[(index + semitones) % len(NOTE_NAMES)]
    return names[0] if use_sharps or len(names) == 1 else names[-1]


def _transpose_slash_bass(suffix: str, semitones: int, use_sharps: bool) -> str:
    return re.sub(
        r"/([A-G](?:#|b)?)",
        lambda match: f"/{transpose_note(match.group(1), semitones, use_sharps)}",
        suffix,
    )


def _is_chord_line(line: str) -> bool:
    words = [word.strip("|:;,()") for word in line.split() if word.strip("|:;,()")]
    if not words:
        return False
    matches = sum(1 for word in words if CHORD_RE.fullmatch(word))
    return matches > len(words) / 2

