"""Join the tracks into one audio track over a still image, with ffmpeg."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from .tracks import Track


class VideoError(Exception):
    pass


def ffmpeg_command(
    tracks: list[Track],
    output: Path,
    image: Path | None = None,
    audio_bitrate: str = "128k",
) -> list[str]:
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-stats", "-y"]
    for track in tracks:
        cmd += ["-i", str(track.path)]

    # The picture only has to exist: 1 fps keeps the file small and the
    # upload fast. Content ID only listens to the audio.
    if image:
        cmd += ["-loop", "1", "-framerate", "1", "-i", str(image)]
    else:
        cmd += ["-f", "lavfi", "-i", "color=c=black:s=640x360:r=1"]
    video_input = len(tracks)

    # Tracks can differ in sample rate and channel count (or be FLAC, WAV,
    # AIFF...), so bring each to the same format before joining them.
    parts = [
        f"[{i}:a]aresample=44100,aformat=sample_fmts=fltp:channel_layouts=stereo[a{i}]"
        for i in range(len(tracks))
    ]
    joined = "".join(f"[a{i}]" for i in range(len(tracks)))
    parts.append(f"{joined}concat=n={len(tracks)}:v=0:a=1[aout]")
    # libx264 needs even dimensions; user images may not have them.
    parts.append(
        f"[{video_input}:v]scale=trunc(iw/2)*2:trunc(ih/2)*2,format=yuv420p,fps=1[vout]"
    )

    cmd += [
        "-filter_complex", ";".join(parts),
        "-map", "[vout]", "-map", "[aout]",
        "-c:v", "libx264", "-preset", "veryfast", "-tune", "stillimage",
        "-c:a", "aac", "-b:a", audio_bitrate,
        "-shortest",
        "-movflags", "+faststart",
        str(output),
    ]
    return cmd


def build(
    tracks: list[Track],
    output: Path,
    image: Path | None = None,
    audio_bitrate: str = "128k",
) -> None:
    if shutil.which("ffmpeg") is None:
        raise VideoError(
            "ffmpeg not found. Install it (macOS: `brew install ffmpeg`, "
            "Debian/Ubuntu: `sudo apt install ffmpeg`) and try again."
        )
    if image is not None and not image.is_file():
        raise VideoError(f"Image not found: {image}")

    result = subprocess.run(ffmpeg_command(tracks, output, image, audio_bitrate))
    if result.returncode != 0:
        raise VideoError(f"ffmpeg failed with exit code {result.returncode}")
