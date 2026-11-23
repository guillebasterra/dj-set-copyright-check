"""check-set: turn a playlist into a test video for YouTube's Content ID."""

from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

from . import playlist, tracks, upload, video


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
    parser.add_argument(
        "--no-rebuild", action="store_true",
        help="reuse the video from an earlier run if it's there",
    )
    parser.add_argument(
        "--upload", action="store_true",
        help="upload the video to YouTube as Private (see 'Set up uploads' in the README)",
    )
    parser.add_argument(
        "--client-secret", type=Path,
        help=f"OAuth client file (default: {upload.CONFIG_DIR / 'client_secret.json'})",
    )
    args = parser.parse_args(argv)
    if args.timestamps_only and args.upload:
        parser.error("--upload needs the video, so it can't be used with --timestamps-only")

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

    stamps = tracks.timestamps(set_tracks)
    timestamps_path.write_text(stamps, encoding="utf-8")
    print(f"Wrote {timestamps_path}")

    if args.timestamps_only:
        return 0

    if args.no_rebuild and video_path.is_file():
        print(f"Reusing {video_path}")
    else:
        print(f"Building {video_path} ...")
        try:
            video.build(set_tracks, video_path, args.image, args.audio_bitrate)
        except video.VideoError as exc:
            print(f"check-set: {exc}", file=sys.stderr)
            return 1
        print(f"Wrote {video_path}")

    if args.upload:
        title = f"set-check: {stem} {date.today().isoformat()}"
        try:
            video_id = upload.upload(video_path, title, stamps, args.client_secret)
        except upload.UploadError as exc:
            print(f"check-set: {exc}", file=sys.stderr)
            return 1
        print(f"Uploaded as Private: https://studio.youtube.com/video/{video_id}/copyright")
        print("Claims show up there once YouTube finishes processing.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
