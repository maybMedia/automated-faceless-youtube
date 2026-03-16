import os
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from scripts.config import PROJECT_ROOT

YOUTUBE_SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
DEFAULT_CLIENT_SECRETS_FILE = "client_secret.json"
DEFAULT_TOKEN_FILE = "youtube_token.json"


def _get_client_secrets_path():
    configured_path = os.getenv("YOUTUBE_CLIENT_SECRETS_FILE")
    client_secrets_path = Path(configured_path) if configured_path else PROJECT_ROOT / DEFAULT_CLIENT_SECRETS_FILE
    return client_secrets_path.expanduser().resolve()


def _get_token_path():
    configured_path = os.getenv("YOUTUBE_TOKEN_FILE")
    token_path = Path(configured_path) if configured_path else PROJECT_ROOT / DEFAULT_TOKEN_FILE
    return token_path.expanduser().resolve()


def _save_credentials(credentials, token_path):
    token_path.parent.mkdir(parents=True, exist_ok=True)
    token_path.write_text(credentials.to_json(), encoding="utf-8")


def _load_saved_credentials(token_path):
    if not token_path.exists():
        return None

    return Credentials.from_authorized_user_file(str(token_path), YOUTUBE_SCOPES)


def _prompt_for_login(client_secrets_path, token_path):
    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError as exc:
        raise RuntimeError(
            "YouTube login requires the 'google-auth-oauthlib' package. "
            "Install it in the virtual environment, then run the upload again."
        ) from exc

    if not client_secrets_path.exists():
        raise RuntimeError(
            "YouTube login requires an OAuth client secrets file. "
            f"Expected it at '{client_secrets_path}'. "
            "Create a Desktop app OAuth client in Google Cloud and save the JSON file there, "
            "or set YOUTUBE_CLIENT_SECRETS_FILE to its path."
        )

    print("YouTube credentials not found. Opening the Google login flow...")
    credentials = InstalledAppFlow.from_client_secrets_file(
        str(client_secrets_path),
        YOUTUBE_SCOPES,
    ).run_local_server(port=0)
    _save_credentials(credentials, token_path)
    return credentials


def _get_youtube_credentials():
    existing_credentials = globals().get("creds")
    if existing_credentials and getattr(existing_credentials, "valid", True):
        return existing_credentials

    token_path = _get_token_path()
    client_secrets_path = _get_client_secrets_path()
    credentials = _load_saved_credentials(token_path)

    if credentials and credentials.expired and credentials.refresh_token:
        try:
            credentials.refresh(Request())
            _save_credentials(credentials, token_path)
        except Exception:
            credentials = None

    if credentials and credentials.valid:
        return credentials

    return _prompt_for_login(client_secrets_path, token_path)

def _build_video_request(youtube, title, description, video_path):
    return youtube.videos().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": title,
                "description": description,
                "tags": ["reddit", "aita", "stories", "shorts"],
            },
            "status": {"privacyStatus": "public"},
        },
        media_body=MediaFileUpload(str(video_path)),
    )


def upload_videos(video_paths, base_title="Crazy Reddit Story"):
    youtube = build("youtube", "v3", credentials=_get_youtube_credentials())
    uploads = []
    total_parts = len(video_paths)

    for index, video_path in enumerate(video_paths, start=1):
        title = f"{base_title} #Shorts"
        description = "Subscribe for more Reddit stories! #Shorts"

        if total_parts > 1:
            title = f"{base_title} Part {index}/{total_parts} #Shorts"
            description = (
                f"Part {index} of {total_parts}. Subscribe for more Reddit stories! "
                "#Shorts"
            )

        request = _build_video_request(youtube, title, description, video_path)
        uploads.append(request.execute())

    return uploads
