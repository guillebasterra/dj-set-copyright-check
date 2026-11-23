"""Parse m3u/m3u8 playlists as exported by Rekordbox (and most other players)."""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote, urlparse


@dataclass
class Entry:
    path: Path
    # From the #EXTINF line, if there was one. Rekordbox truncates long titles
    # (and filenames), so these are only a fallback for the file's own tags.
    title: str | None = None
    duration: float | None = None


class PlaylistError(Exception):
    pass


def parse(playlist: Path) -> list[Entry]:
    """Read a playlist and return its entries, with every path resolved.

    Raises PlaylistError listing every file that can't be found.
    """
    text = playlist.read_text(encoding="utf-8-sig", errors="replace")
    entries: list[Entry] = []
    title = duration = None

    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("#EXTINF:"):
            duration, title = _parse_extinf(line)
            continue
        if line.startswith("#"):
            continue
        entries.append(Entry(_resolve(line, playlist.parent), title, duration))
        title = duration = None

    if not entries:
        raise PlaylistError(f"No tracks found in {playlist}")

    missing = [e.path for e in entries if not e.path.is_file()]
    if missing:
        listing = "\n".join(f"  {p}" for p in missing)
        raise PlaylistError(
            f"{len(missing)} of {len(entries)} tracks not found "
            f"(is the USB drive plugged in?):\n{listing}"
        )
    return entries


def _parse_extinf(line: str) -> tuple[float | None, str | None]:
    info = line[len("#EXTINF:"):]
    length, _, title = info.partition(",")
    try:
        duration = float(length.split()[0])
    except (ValueError, IndexError):
        duration = None
    if duration is not None and duration < 0:
        duration = None
    return duration, title.strip() or None


def _resolve(location: str, base: Path) -> Path:
    if location.startswith("file://"):
        location = unquote(urlparse(location).path)
    path = Path(location).expanduser()
    if not path.is_absolute():
        path = base / path
    if path.exists():
        return path
    # macOS filesystems and playlist writers disagree on Unicode normalisation
    # (e.g. "ñ" as one code point or two), so try both forms.
    for form in ("NFC", "NFD"):
        alt = Path(unicodedata.normalize(form, str(path)))
        if alt.exists():
            return alt
    return path
