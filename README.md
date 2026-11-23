# dj-set-check

Check a Rekordbox playlist against YouTube's Content ID before recording a DJ set.

**Status:** planning only, nothing is built yet. See [PLAN.md](PLAN.md).

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
