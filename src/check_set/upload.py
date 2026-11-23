"""Upload the test video to YouTube as Private, with the YouTube Data API v3."""

from __future__ import annotations

import os
from pathlib import Path

# Only upload access: the tool never reads, edits or deletes anything else.
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
CONFIG_DIR = Path(os.environ.get("CHECK_SET_CONFIG", Path.home() / ".config" / "check-set"))
DESCRIPTION_LIMIT = 5000  # YouTube's limit, in bytes


class UploadError(Exception):
    pass


def credentials(client_secret: Path | None = None):
    """Load saved OAuth credentials, or sign in through the browser once."""
    from google.auth.exceptions import RefreshError
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow

    client_secret = client_secret or CONFIG_DIR / "client_secret.json"
    token = CONFIG_DIR / "token.json"

    creds = None
    if token.exists():
        creds = Credentials.from_authorized_user_file(str(token), SCOPES)
    if creds and creds.valid:
        return creds
    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
        except RefreshError:
            creds = None  # Revoked or expired for good: sign in again.
    if not creds or not creds.valid:
        if not client_secret.is_file():
            raise UploadError(
                f"No OAuth client file at {client_secret}. "
                "See 'Set up uploads' in the README."
            )
        flow = InstalledAppFlow.from_client_secrets_file(str(client_secret), SCOPES)
        creds = flow.run_local_server(port=0)

    token.parent.mkdir(parents=True, exist_ok=True)
    token.write_text(creds.to_json())
    token.chmod(0o600)
    return creds


def fit_description(text: str) -> str:
    data = text.encode("utf-8")
    if len(data) <= DESCRIPTION_LIMIT:
        return text
    note = "\n(timestamp list cut short; see the .timestamps.txt file)"
    cut = data[: DESCRIPTION_LIMIT - len(note.encode("utf-8"))].decode("utf-8", "ignore")
    # Drop the partial last line.
    return cut[: cut.rfind("\n") + 1].rstrip("\n") + note


def upload(video: Path, title: str, description: str, client_secret: Path | None = None) -> str:
    """Upload as Private and return the new video's ID."""
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    from googleapiclient.http import MediaFileUpload

    youtube = build("youtube", "v3", credentials=credentials(client_secret))
    body = {
        "snippet": {
            "title": title[:100],
            "description": fit_description(description),
            "categoryId": "10",  # Music
        },
        "status": {
            "privacyStatus": "private",
            "selfDeclaredMadeForKids": False,
        },
    }
    media = MediaFileUpload(str(video), mimetype="video/mp4", chunksize=16 * 1024 * 1024, resumable=True)
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

    response = None
    try:
        while response is None:
            status, response = request.next_chunk(num_retries=5)
            if status:
                print(f"\rUploading... {status.progress():.0%}", end="", flush=True)
    except HttpError as exc:
        print()
        raise UploadError(f"Upload failed: {exc}") from exc
    print("\rUploading... done")
    return response["id"]
