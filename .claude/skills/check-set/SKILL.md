---
name: check-set
description: Check a DJ playlist (Rekordbox m3u/m3u8 export) against YouTube's Content ID. Builds the test video and timestamp list, gets it uploaded to YouTube as Private, reads the copyright claims in YouTube Studio, and reports which tracks are safe, claimed, or blocked. Use when the user wants to check a playlist or set for copyright claims, or asks what got claimed on a set-check video.
---

# Check a set against Content ID

The idea: YouTube is the only thing that knows each label's Content ID policy. So join the playlist's tracks into one video, upload it as Private, and let YouTube say which tracks it claims and what each claim does. The timestamp list maps each claim back to a track.

Work from the repo root. Run `uv sync` once if `.venv` is missing.

## 1. Build the video and timestamps

```
uv run check-set <playlist.m3u8> -o out
```

- This writes `out/<name>.mp4` and `out/<name>.timestamps.txt`. A 4-hour set takes a few minutes, so run it in the background.
- If the video already exists from an earlier run and the playlist hasn't changed, add `--no-rebuild`.
- "tracks not found" usually means the drive with the music isn't plugged in. Tell the user which files are missing; don't edit the playlist.

## 2. Get it uploaded as Private

Uploading publishes to the user's channel, so ask before doing it, even though the video is Private.

- **API (when it's set up):** if `~/.config/check-set/client_secret.json` exists, run `uv run check-set <playlist> -o out --no-rebuild --upload`. If there's no `token.json` next to it yet, the first run opens a browser sign-in. Have the user run that one themselves with `! <command>`. The output ends with the video's Studio copyright URL.
- **By hand (otherwise):** ask the user to upload the mp4:
  1. In studio.youtube.com, choose Create → Upload videos and drop in the mp4.
  2. Set visibility to **Private**.
  3. Title it `set-check: <name> <date>`.
  4. Paste the timestamp file into the description.
  5. Ask them for the video link, or its ID, once it's uploaded.

Don't upload through Studio with the browser tools unless the user asks: the files are hundreds of MB.

## 3. Wait for the checks

Studio runs its copyright check while it processes the video. Claims usually appear within minutes of processing finishing, but a long set can take longer. If the copyright page still says the check is running, wait and look again; don't report a clean result early.

## 4. Read the claims (Claude in Chrome)

Load the `anthropic-skills:chrome-browser` skill first and follow it. Then:

1. Open `https://studio.youtube.com/video/<VIDEO_ID>/copyright`. If that doesn't load, go to Content, find the video, and open its copyright details from the Restrictions column.
2. For every claim, record:
   - the song and artist YouTube matched
   - the claimant (label or publisher)
   - the time range(s) where it was found in the video
   - the impact, in Studio's own words (e.g. monetized by the claimant, blocked in some countries, blocked worldwide)
   - for country blocks, which countries, if Studio lists them
3. The page may list claims in pages or collapse details; open each one.

**This step is read only.** Never click Dispute, Trim, Erase song, Replace song, Mute, or Delete. Those change or remove the video, and they're the user's call.

If the user isn't signed in to Studio, or the extension isn't connected, stop and say so. Don't sign in for them.

## 5. Match claims to tracks

Each line of `out/<name>.timestamps.txt` is `H:MM:SS Artist - Title`. A track runs from its own start time to the next line's start time, and the last track runs to the end of the video.

Assign each claim to the track whose range contains most of the claim's time range. If a claim spans two tracks, or YouTube matched a song that differs from the track's name, list it and say which one you picked. Samples, remixes and edits often match the original song. Expect up to a couple of seconds of drift over a long set; that doesn't matter at this scale.

## 6. Report

Write `out/<name>.claims.md` and give the user the short version in chat:

- **Swap out:** tracks blocked worldwide. Any one of these takes the whole video down.
- **Think about it:** tracks blocked in some countries (list the countries).
- **Fine:** tracks claimed but only monetized or tracked. The video stays up; the label gets the ad money.
- **No claim:** everything else.

Put a full table under that, one row per track in playlist order: start time, track, status, claimant, matched song.

End with the usual caveats: a clean check isn't a guarantee, labels can change policy or claim later, and the recorded mix can match differently from the raw tracks.

## 7. Clean up

Ask whether to keep the test video as a record or delete it in Studio. Don't delete it without a clear yes.
