"""Read each track's duration and artist/title, and lay out the timestamps."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import mutagen

from .playlist import Entry


@dataclass
class Track:
    path: Path
    artist: str | None
    title: str
    duration: float  # seconds
    start: float = 0.0  # seconds from the start of the joined video

    @property
    def label(self) -> str:
        return f"{self.artist} - {self.title}" if self.artist else self.title


class TrackError(Exception):
    pass


def load(entries: list[Entry]) -> list[Track]:
    tracks = [_load_one(e) for e in entries]
    start = 0.0
    for track in tracks:
        track.start = start
        start += track.duration
    return tracks


def _load_one(entry: Entry) -> Track:
    try:
        audio = mutagen.File(entry.path, easy=True)
    except mutagen.MutagenError as exc:
        raise TrackError(f"Can't read {entry.path}: {exc}") from exc

    duration = audio.info.length if audio is not None and audio.info else None
    if not duration:
        duration = entry.duration
    if not duration:
        raise TrackError(f"Can't tell how long {entry.path} is")

    artist = _first_tag(audio, "artist")
    title = _first_tag(audio, "title")
    if not title:
        # Fall back to the playlist's own label, then the filename.
        title = entry.title or entry.path.stem
        if artist and title.startswith(f"{artist} - "):
            title = title[len(artist) + 3:]

    return Track(entry.path, artist, title, float(duration))


def _first_tag(audio, key: str) -> str | None:
    if audio is None or audio.tags is None:
        return None
    try:
        values = audio.tags.get(key)
    except (KeyError, ValueError):
        return None
    if not values:
        return None
    value = str(values[0]).strip()
    return value or None


def format_time(seconds: float) -> str:
    """YouTube chapter style: 4:05, or 1:04:05 past the hour."""
    total = int(seconds)
    h, rem = divmod(total, 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def timestamps(tracks: list[Track]) -> str:
    # One "M:SS Artist - Title" per line, starting at 0:00, which YouTube
    # also turns into chapters when it's pasted into the description.
    return "".join(f"{format_time(t.start)} {t.label}\n" for t in tracks)
