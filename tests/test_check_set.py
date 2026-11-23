import json
import shutil
import subprocess
from pathlib import Path

import pytest
from mutagen.easyid3 import EasyID3

from check_set import cli, playlist, tracks

needs_ffmpeg = pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg not installed")


def make_tone(path: Path, seconds: float, artist=None, title=None, rate=44100, channels=2):
    """Synthesise a short MP3 so the tests ship no real music."""
    path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
         "-f", "lavfi", "-i", f"sine=frequency=440:duration={seconds}:sample_rate={rate}",
         "-ac", str(channels), "-c:a", "libmp3lame", "-b:a", "64k", str(path)],
        check=True,
    )
    if artist or title:
        tags = EasyID3()
        if artist:
            tags["artist"] = artist
        if title:
            tags["title"] = title
        tags.save(path)
    return path


def write_playlist(path: Path, lines: list[str]) -> Path:
    # Rekordbox writes UTF-8 with CRLF line endings.
    path.write_bytes(("\r\n".join(["#EXTM3U", *lines]) + "\r\n").encode("utf-8"))
    return path


def test_format_time():
    assert tracks.format_time(0) == "0:00"
    assert tracks.format_time(65.9) == "1:05"
    assert tracks.format_time(3600 + 4 * 60 + 5) == "1:04:05"


def test_missing_files_are_all_listed(tmp_path):
    pl = write_playlist(tmp_path / "set.m3u8", [
        "#EXTINF:100,A - One", str(tmp_path / "one.mp3"),
        "#EXTINF:100,B - Two", "two.mp3",
    ])
    with pytest.raises(playlist.PlaylistError) as exc:
        playlist.parse(pl)
    assert "2 of 2 tracks not found" in str(exc.value)
    assert "one.mp3" in str(exc.value) and "two.mp3" in str(exc.value)


def test_extinf_and_relative_paths(tmp_path):
    (tmp_path / "music").mkdir()
    (tmp_path / "music" / "Señorita.mp3").write_bytes(b"")
    pl = write_playlist(tmp_path / "set.m3u8", [
        "#EXTINF:357,Ninetree - Señorita", "music/Señorita.mp3",
    ])
    [entry] = playlist.parse(pl)
    assert entry.duration == 357
    assert entry.title == "Ninetree - Señorita"
    assert entry.path == tmp_path / "music" / "Señorita.mp3"


@needs_ffmpeg
def test_tags_win_over_truncated_playlist_names(tmp_path):
    tagged = make_tone(tmp_path / "Artist - A Very Long Ti.mp3", 2, "Artist", "A Very Long Title")
    untagged = make_tone(tmp_path / "x.mp3", 3)
    pl = write_playlist(tmp_path / "set.m3u8", [
        "#EXTINF:2,Artist - A Very Long Ti...", tagged.name,
        "#EXTINF:3,Other - Untagged", untagged.name,
    ])
    one, two = tracks.load(playlist.parse(pl))
    assert one.label == "Artist - A Very Long Title"
    assert two.label == "Other - Untagged"
    assert one.start == 0
    assert two.start == pytest.approx(one.duration)


@needs_ffmpeg
def test_end_to_end(tmp_path):
    # Mixed sample rates and a mono file, as real libraries have.
    make_tone(tmp_path / "a.mp3", 3, "A", "One")
    make_tone(tmp_path / "b.mp3", 4, "B", "Two", rate=48000, channels=1)
    make_tone(tmp_path / "c.mp3", 2, "C", "Three")
    pl = write_playlist(tmp_path / "set.m3u8", ["a.mp3", "b.mp3", "c.mp3"])

    assert cli.main([str(pl), "-o", str(tmp_path / "out")]) == 0

    stamps = (tmp_path / "out" / "set.timestamps.txt").read_text().splitlines()
    assert stamps[0] == "0:00 A - One"
    assert stamps[1].endswith(" B - Two")
    assert stamps[2].endswith(" C - Three")

    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type",
         "-of", "json", str(tmp_path / "out" / "set.mp4")],
        capture_output=True, text=True, check=True,
    )
    info = json.loads(probe.stdout)
    assert sorted(s["codec_type"] for s in info["streams"]) == ["audio", "video"]
    assert float(info["format"]["duration"]) == pytest.approx(9, abs=0.5)
