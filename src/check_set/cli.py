"""check-set: turn a playlist into a test video for YouTube's Content ID."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import playlist, tracks, video


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="check-set",
        description=(
            "Join a playlist's tracks into one video and write a timestamp "
            "list, so YouTube's copyright claims can be matched to tracks."
        ),
    )
    parser.add_argument("playlist", type=Path, help="m3u or m3u8 playlist (e.g. a Rekordbox export)")
    parser.add_argument(
        "-o", "--out-dir", type=Path,
        help="where to write the video and timestamps (default: next to the playlist)",
    )
    parser.add_argument("--image", type=Path, help="still image for the video (default: black)")
    parser.add_argument("--audio-bitrate", default="128k", help="AAC bitrate (default: 128k)")
    parser.add_argument(
        "--timestamps-only", action="store_true",
        help="write the timestamp list but skip building the video",
    )
    args = parser.parse_args(argv)

    try:
        entries = playlist.parse(args.playlist)
        set_tracks = tracks.load(entries)
    except (playlist.PlaylistError, tracks.TrackError, OSError) as exc:
        print(f"check-set: {exc}", file=sys.stderr)
        return 1

    out_dir = args.out_dir or args.playlist.parent
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = args.playlist.stem
    timestamps_path = out_dir / f"{stem}.timestamps.txt"
    video_path = out_dir / f"{stem}.mp4"

    total = set_tracks[-1].start + set_tracks[-1].duration
    print(f"{len(set_tracks)} tracks, {tracks.format_time(total)} total")

    timestamps_path.write_text(tracks.timestamps(set_tracks), encoding="utf-8")
    print(f"Wrote {timestamps_path}")

    if args.timestamps_only:
        return 0

    print(f"Building {video_path} ...")
    try:
        video.build(set_tracks, video_path, args.image, args.audio_bitrate)
    except video.VideoError as exc:
        print(f"check-set: {exc}", file=sys.stderr)
        return 1
    print(f"Wrote {video_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
