"""Plain-text file detection helpers for tabbed editing."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


TEXT_FILE_SUFFIXES = {
    ".txt": "text",
    ".md": "markdown",
    ".pro": "chordpro",
    ".cho": "chordpro",
    ".chord": "chordpro",
    ".chordpro": "chordpro",
    ".mchord": "chordpages",
}


@dataclass(slots=True)
class TextFileInfo:
    text: str
    encoding: str
    newline: str
    file_type: str


def detect_file_type(path: Path) -> str:
    return TEXT_FILE_SUFFIXES.get(path.suffix.lower(), "text")


def detect_newline(raw_text: str) -> str:
    crlf = raw_text.count("\r\n")
    without_crlf = raw_text.replace("\r\n", "")
    cr = without_crlf.count("\r")
    lf = without_crlf.count("\n")
    if crlf >= cr and crlf >= lf and crlf > 0:
        return "\r\n"
    if cr > lf and cr > 0:
        return "\r"
    return "\n"


def normalize_newlines(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def restore_newlines(text: str, newline: str) -> str:
    normalized = normalize_newlines(text)
    if newline == "\n":
        return normalized
    return normalized.replace("\n", newline)


def read_text_file(path: Path) -> TextFileInfo:
    raw = path.read_bytes()
    text, encoding = decode_text(raw)
    return TextFileInfo(
        text=normalize_newlines(text),
        encoding=encoding,
        newline=detect_newline(text),
        file_type=detect_file_type(path),
    )


def write_text_file(path: Path, text: str, encoding: str, newline: str) -> None:
    path.write_bytes(restore_newlines(text, newline).encode(encoding, errors="replace"))


def decode_text(raw: bytes) -> tuple[str, str]:
    if raw.startswith(b"\xef\xbb\xbf"):
        return raw.decode("utf-8-sig"), "utf-8-sig"
    if raw.startswith(b"\xff\xfe"):
        return raw.decode("utf-16"), "utf-16"
    if raw.startswith(b"\xfe\xff"):
        return raw.decode("utf-16"), "utf-16"

    for encoding in ("utf-8", "cp1252", "latin-1"):
        try:
            return raw.decode(encoding), encoding
        except UnicodeDecodeError:
            continue

    return raw.decode("utf-8", errors="replace"), "utf-8"

