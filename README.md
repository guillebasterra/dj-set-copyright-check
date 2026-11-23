# DJ Set Copyright Check

Check a Rekordbox playlist against YouTube's Content ID before recording a DJ set.

**Status:** building the test video and timestamp list works. Uploading to YouTube is next; for now, upload the video by hand. See [PLAN.md](PLAN.md).

## Install

You need [ffmpeg](https://ffmpeg.org/) and [uv](https://docs.astral.sh/uv/).

```
brew install ffmpeg uv          # macOS; on Debian/Ubuntu: apt install ffmpeg, then install uv
git clone https://github.com/guillebasterra/dj-set-copyright-check.git
cd dj-set-copyright-check
uv sync
```

## Use

In Rekordbox, right-click the playlist and choose **Export a playlist to a file → M3U8**. Keep the drive with the music plugged in. Then run:

```
uv run check-set path/to/playlist.m3u8
```

This writes two files next to the playlist (or into `-o DIR`):

- `playlist.mp4`: every track joined end to end over a black frame at 1 fps. A 4.5-hour set comes out at about 250 MB and takes a few minutes to build.
- `playlist.timestamps.txt`: one `H:MM:SS Artist - Title` line per track. Paste it into the video description so each claim's time maps to a track.

Upload the video to YouTube Studio as **Private**. When processing finishes, open the video's **Copyright** details to see which tracks were claimed and what each claim does.

Options: `--image cover.jpg` uses your own still image instead of black, `--audio-bitrate 192k` changes the audio quality, and `--timestamps-only` skips the video. Artist and title come from each file's tags; when a file has none, the playlist's own label is used instead.

Run the tests with `uv run pytest`. They generate their own tone files, so you don't need any music to run them.

## The problem

When a DJ set is uploaded to YouTube, Content ID matches it track by track against what labels have registered. Each rights holder picks a policy per track, and it can differ by country:

| Outcome | Effect on the set |
|---|---|
| No match | Nothing. |
| Claimed, track or monetise | Video stays up; the label gets any ad revenue. Normal and fine. |
| Claimed, blocked in some countries | Video is invisible in those countries. |
| Claimed, blocked worldwide | One such track takes the whole video down. |

Those policies aren't public, and no third-party tool or API can look them up. Only YouTube knows, and it only tells you after an upload.

## The idea

Let YouTube do the check, before the set is recorded:

1. Build the playlist in Rekordbox as usual and export it as an m3u8 file.
2. Run `check-set playlist.m3u8`.
3. The tool joins the playlist's MP3s end to end into one video with a static image, and uploads it to YouTube as **Private**.
4. YouTube Studio lists every claimed track and its effect. The tool's timestamp list maps each claim back to a song.
5. Swap out anything blocked, then record the real set.

## Limits

- A clean check isn't a guarantee. Labels can change policy later, and claims can land months after upload.
- The real mix may match slightly differently from the raw tracks.
- Live streams are policed more strictly than uploads; this is for recorded sets.
- A claim is not a copyright strike. Strikes come from manual takedowns and can't be predicted.
