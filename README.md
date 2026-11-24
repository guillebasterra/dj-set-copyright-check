# DJ Set Copyright Check

Check a Rekordbox playlist against YouTube's Content ID before recording a DJ set.

**Status:** works. Building the video and reading the claims by hand are tested on a real 4-hour set. Uploading through the API (`--upload`) is written but not yet tested against a real channel. See [PLAN.md](PLAN.md).

## Install

You need [ffmpeg](https://ffmpeg.org/) and [uv](https://docs.astral.sh/uv/):

```
brew install ffmpeg uv          # macOS; on Debian/Ubuntu: apt install ffmpeg, then install uv
```

### With Claude Code (easiest)

In [Claude Code](https://claude.com/claude-code), run:

```
/plugin install check-set --marketplace guillebasterra/dj-set-copyright-check
```

On Claude Code versions older than 2.1.275, run `/plugin marketplace add guillebasterra/dj-set-copyright-check` and then `/plugin install check-set@dj-set-copyright-check`. Also install [Claude in Chrome](https://claude.ai/chrome) and sign in to YouTube Studio in Chrome.

### Command line only

```
uv tool install git+https://github.com/guillebasterra/dj-set-copyright-check
```

This puts `check-set` on your PATH. Update it with `uv tool upgrade dj-set-copyright-check`.

## Use

In Rekordbox, right-click the playlist and choose **Export a playlist to a file → M3U8**. Keep the drive with the music plugged in.

### With Claude Code

Ask Claude Code something like "check ~/Desktop/myset.m3u8 for copyright claims", or type `/` and pick the check-set skill. Claude:

1. Builds the video and installs the `check-set` command if it's missing.
2. Has you drag the video into YouTube Studio as Private, or uses `--upload` if you've set it up.
3. Reads the claims in Studio through Claude in Chrome. This is read only: it never disputes, trims or deletes anything.
4. Writes a per-track report: which tracks to swap out, which are blocked in some countries, which are only monetized, and which aren't claimed.

### Command line

```
check-set path/to/playlist.m3u8
```

This writes two files next to the playlist (or into `-o DIR`):

- `playlist.mp4`: every track joined end to end over a black frame at 1 fps. A 4.5-hour set comes out at about 250 MB and takes a few minutes to build.
- `playlist.timestamps.txt`: one `H:MM:SS Artist - Title` line per track. Paste it into the video description so each claim's time maps to a track.

Upload the video to YouTube Studio as **Private**. When processing finishes, open the video's **Copyright** details to see which tracks were claimed and what each claim does.

Options:
- `--image cover.jpg` uses your own still image instead of black.
- `--audio-bitrate 192k` changes the audio quality.
- `--timestamps-only` skips the video.
- `--no-rebuild` reuses a video from an earlier run.

Artist and title come from each file's tags. When a file has none, the playlist's own label is used instead.

## Set up uploads (optional)

`check-set playlist.m3u8 --upload` builds the video and then uploads it to your channel as Private, with the timestamp list in the description. Uploading needs your own Google Cloud OAuth client. Setting it up takes about ten minutes and only has to be done once:

1. In the [Google Cloud console](https://console.cloud.google.com/), create a project.
2. Under **APIs & Services → Library**, find **YouTube Data API v3** and enable it.
3. Under **Google Auth Platform** (formerly the OAuth consent screen), set the app up as **External**, then add the Google account that owns your channel under **Audience → Test users**.
4. Under **Clients** (or **Credentials → Create credentials → OAuth client ID**), create a **Desktop app** client and download its JSON file.
5. Save the file as `~/.config/check-set/client_secret.json`, or pass its path with `--client-secret`.

The first `--upload` opens your browser so you can sign in. If your channel is a Brand Account, pick the channel there, not your personal account. The sign-in is saved in `~/.config/check-set/token.json`, and the tool only asks for permission to upload.

Things to know:

- **Uploads stay Private.** YouTube forces videos uploaded through an unverified API project to Private, which is what you want here anyway.
- **Quota.** The default API quota is 10,000 units a day and one upload costs about 1,600, so you get roughly six uploads a day.
- **Weekly re-sign-in.** While the Google app is in "Testing" mode, the saved sign-in expires after 7 days. The tool asks you to sign in again when that happens.

Set `CHECK_SET_CONFIG` to keep these files somewhere other than `~/.config/check-set`.

## Development

```
git clone https://github.com/guillebasterra/dj-set-copyright-check.git
cd dj-set-copyright-check
uv sync
uv run pytest
```

Inside the clone, the skill also loads straight from `.claude/skills/` (a symlink to `skills/`), and `uv run check-set` runs your working copy. To check the plugin files, run `claude plugin validate .`.

The tests generate their own tone files, so you don't need any music to run them.

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

## License

MIT. See [LICENSE](LICENSE).
