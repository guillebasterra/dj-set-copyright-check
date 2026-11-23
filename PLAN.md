# Plan

## Target

One command:

```
check-set path/to/playlist.m3u8
```

It ends with a private video on the channel and a local timestamp file, ready for the claims to be read in YouTube Studio.

## Pipeline

1. **Parse the m3u8.** Rekordbox's playlist export lists the path to each MP3. Resolve every path and fail loudly on any missing file.
2. **Build the test video.** Use ffmpeg to join the MP3s in playlist order into one audio track over a static image. Low video bitrate and 1 fps keep the file small and the upload fast.
3. **Write the timestamp list.** Record each track's start time in the joined video (from the MP3 durations), with artist and title from the ID3 tags. Save it next to the video, e.g. `playlist.timestamps.txt`.
4. **Upload as Private.** YouTube Data API v3 `videos.insert`, with OAuth for the channel. Title it something like `set-check: <playlist name> <date>`, and put the timestamp list in the description.
5. **Read the claims.** Manual: open YouTube Studio, check the Restrictions column, open the copyright details. Match each claim's time range to the timestamp list.

## What can't be automated

Per-track claim details are only shown in YouTube Studio. The API that exposes them is restricted to labels and partners. Options for step 5:

- Look in Studio by hand (about 30 seconds).
- Have Claude read the Studio page through the Chrome browser tool and produce a per-track table. Works in a Claude session, not as a standalone script.

## One-time setup

- Install ffmpeg.
- Create a Google Cloud project and enable the YouTube Data API v3.
- Create OAuth desktop credentials and sign in once to authorise uploads. Keep the credentials and token out of git.

## Build order

1. **m3u8 → video + timestamps.** Useful on its own: the video can be dragged into Studio by hand.
2. **First manual test.** Upload one generated video through Studio and confirm claims appear on a private video with the detail we need.
3. **API upload.** Add the OAuth flow and `videos.insert`.
4. **Compare.** Confirm the API upload gets the same claims as the manual one (see open questions).
5. **Optional: results table.** Claude-in-Chrome reading of Studio, or a paste-in parser for the claim list.

## Open questions

- **Does Content ID treat API uploads from an unaudited project like normal uploads?** Such uploads are forced to Private, which is what we want, but it needs confirming that claims still appear. Fallback: script builds the video, upload stays manual.
- **Upload quota.** The API allows a handful of uploads per day. Check the current cost per upload.
- **How long until claims appear?** Usually minutes after processing; measure it on the first test.
- **Exact Rekordbox export menu and m3u8 format** in the installed version, including how it writes paths (absolute or relative, encoding).
- **Do raw tracks match the same as mixed audio?** Compare one test video against a real recorded set.
- **Cleanup.** Delete test videos after reading the claims, or keep them as a record?

## Likely stack

Python, ffmpeg, `mutagen` for tags and durations, `google-api-python-client` and `google-auth-oauthlib` for the upload.
