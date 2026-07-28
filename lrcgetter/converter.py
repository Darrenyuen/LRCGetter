"""QRC parsing and LRC conversion for LRCGetter."""

from __future__ import annotations

import html
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple


LINE_RE = re.compile(r"^\[(\d+),(\d+)\](.*)$")
TOKEN_RE = re.compile(r"(.+?)\((\d+),(\d+)\)")
LRC_LINE_RE = re.compile(r"^\[(\d+):(\d+(?:\.\d+)?)\](.*)$")
METADATA_RE = re.compile(r"^\[([A-Za-z][A-Za-z0-9_-]*):(.*)\]$")


@dataclass(frozen=True)
class TimedLine:
    start: int
    duration: int
    text: str
    tokens: Tuple[Tuple[str, int, int], ...] = ()


def extract_qrc_text(decoded: bytes) -> str:
    text = decoded.decode("utf-8", errors="replace").lstrip("\ufeff")
    if not text.lstrip().startswith("<?xml"):
        if any(LINE_RE.match(line) for line in text.replace("\r", "").splitlines()):
            return text
        return lrc_to_qrc(text)
    # Parse the raw attribute first. XML parsers normalize line breaks inside
    # attributes to spaces, while QRC intentionally stores the lyric's line
    # boundaries there as character references.
    match = re.search(
        r'<Lyric_1\s+[^>]*LyricContent="(.*?)"\s*/?>', text, re.DOTALL
    )
    if match:
        return html.unescape(match.group(1))
    try:
        root = ET.fromstring(text)
        lyric = root.find(".//Lyric_1")
        if lyric is None:
            raise ValueError("Lyric_1 element missing")
        content = lyric.attrib.get("LyricContent")
        if content is None:
            raise ValueError("LyricContent attribute missing")
        return html.unescape(content)
    except ET.ParseError as exc:
        raise ValueError("Unable to find LyricContent in QRC XML") from exc


def lrc_to_qrc(text: str) -> str:
    parsed: List[Tuple[int, str]] = []
    metadata: List[str] = []
    for raw in text.replace("\r", "").splitlines():
        if METADATA_RE.match(raw):
            metadata.append(raw)
            continue
        match = LRC_LINE_RE.match(raw)
        if not match:
            continue
        minute, second, content = match.groups()
        parsed.append((int((int(minute) * 60 + float(second)) * 1000), content))
    lines = []
    for index, (start, content) in enumerate(parsed):
        end = parsed[index + 1][0] if index + 1 < len(parsed) else start + 5000
        if content:
            lines.append(f"[{start},{max(0, end - start)}]{content}")
    return "\n".join(metadata + lines)


def extract_metadata(text: str) -> Dict[str, str]:
    metadata: Dict[str, str] = {}
    for raw in text.replace("\r", "").splitlines():
        match = METADATA_RE.match(raw)
        if not match:
            continue
        key, value = match.groups()
        value = value.strip()
        if value:
            metadata.setdefault(key.lower(), value)
    return metadata


def parse_qrc(text: str) -> Tuple[List[str], List[TimedLine]]:
    ignored: List[str] = []
    lines: List[TimedLine] = []
    for raw in text.replace("\r", "").splitlines():
        match = LINE_RE.match(raw)
        if not match:
            if raw:
                ignored.append(raw)
            continue
        start_s, duration_s, content = match.groups()
        tokens = tuple(
            (token, int(token_start), int(token_duration))
            for token, token_start, token_duration in TOKEN_RE.findall(content)
        )
        plain = TOKEN_RE.sub(lambda item: item.group(1), content)
        lines.append(TimedLine(int(start_s), int(duration_s), plain, tokens))
    return ignored, lines


def format_time(milliseconds: int) -> str:
    milliseconds = max(0, round(milliseconds / 10) * 10)
    return (
        f"{milliseconds // 60000:02d}:"
        f"{(milliseconds // 1000) % 60:02d}."
        f"{(milliseconds % 1000) // 10:02d}"
    )


def line_lrc(lines: Iterable[TimedLine]) -> str:
    return "".join(f"[{format_time(line.start)}]{line.text}\n" for line in lines)


def char_lrc(lines: Iterable[TimedLine]) -> str:
    output: List[str] = []
    for line in lines:
        if not line.tokens:
            continue
        content = "".join(
            f"[{format_time(token_start)}]{token}"
            for token, token_start, _ in line.tokens
        )
        output.append(
            f"{content}[{format_time(line.start + line.duration)}]\n"
        )
    return "".join(output)


def bilingual_lrc(original: Sequence[TimedLine], translation: Sequence[TimedLine]) -> str:
    translated_by_start = {line.start: line for line in translation}
    output: List[str] = []
    for index, source in enumerate(original):
        tokens = char_lrc([source]).rstrip("\n")
        output.append(tokens or f"[{format_time(source.start)}]{source.text}")
        translated = translated_by_start.get(source.start)
        if translated is None and index < len(translation):
            translated = translation[index]
        if translated and translated.text:
            at = max(source.start, source.start + source.duration - 20)
            output.append(f"[{format_time(at)}]{translated.text}")
    return "\n".join(output) + ("\n" if output else "")


def safe_component(value: str) -> str:
    value = re.sub(r'[\x00-\x1f/:"*?<>|\\]', "＿", value).strip(" .")
    return value or "unknown"


def write_outputs(
    output_dir: Path,
    title: str,
    decoded: Dict[str, str],
) -> List[Path]:
    prefixes = {"orig": "og", "ts": "ch", "roma": "rm"}
    parsed = {kind: parse_qrc(decoded.get(kind, "")) for kind in prefixes}
    output_dir.mkdir(parents=True, exist_ok=True)
    created: List[Path] = []
    safe_title = safe_component(title)

    def save(suffix: str, content: str) -> None:
        if not content:
            return
        path = output_dir / f"{safe_title}-{suffix}.lrc"
        path.write_text(content, encoding="utf-8")
        created.append(path)

    for kind, prefix in prefixes.items():
        ignored, lines = parsed[kind]
        if ignored:
            path = output_dir / f"{safe_title}-{prefix}-ignr.txt"
            path.write_text("\n".join(ignored) + "\n", encoding="utf-8")
            created.append(path)
        save(f"{prefix}-line", line_lrc(lines))
        if kind in {"orig", "roma"}:
            save(f"{prefix}-char", char_lrc(lines))

    save(
        "og&ch-mix",
        bilingual_lrc(parsed["orig"][1], parsed["ts"][1])
        if parsed["orig"][1] and parsed["ts"][1]
        else "",
    )
    return created
