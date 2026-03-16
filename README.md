# Automated Faceless YouTube

Create faceless YouTube Shorts from Reddit stories with voiceover, captions, and gameplay footage.

## Commands

Run these from the project root:

```powershell
.venv\Scripts\python.exe pipeline.py generate
```

Generates the full Reddit story locally, renders one full captioned video, then splits it into Shorts-sized parts in `temp/`. This does not upload anything.

```powershell
.venv\Scripts\python.exe pipeline.py run
```

Runs the full pipeline: fetch story, generate the full script, create voice, generate captions, render the full video, split it into 59-second parts, upload all parts, and then delete temp files after a successful upload.

```powershell
.venv\Scripts\python.exe pipeline.py clean
```

Deletes files from the `temp/` folder.

```powershell
.venv\Scripts\python.exe pipeline.py upload-temp --title "My Story Title"
```

Uploads any existing `temp/video_part*.mp4` files without regenerating the video. This is useful if rendering succeeded but the upload step failed.

## Setup

1. Create and activate a virtual environment if needed.
2. Install project dependencies in `.venv`.
3. Fill in your environment variables in [`.env`](/c:/Users/brait/Documents/Desktop/VSCode/automated-faceless-youtube/.env).

Required environment variables:

```env
ELEVENLABS_API_KEY=your_elevenlabs_api_key
ELEVENLABS_VOICE_ID=your_elevenlabs_voice_id
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
```

A template is available in [`env.example`](/c:/Users/brait/Documents/Desktop/VSCode/automated-faceless-youtube/env.example).

Optional YouTube upload settings:

```env
YOUTUBE_CLIENT_SECRETS_FILE=client_secret.json
YOUTUBE_TOKEN_FILE=youtube_token.json
```

For uploads, save your Google OAuth Desktop app credentials JSON as `client_secret.json` in the project root, or point `YOUTUBE_CLIENT_SECRETS_FILE` to it. The first time `run` uploads without a saved token, the script will open a Google login flow and store the resulting token in `youtube_token.json`.

## Output

- Full local render: `temp/video_full.mp4`
- Split Shorts parts: `temp/video_part01.mp4`, `temp/video_part02.mp4`, ...
- Generated audio: `temp/voice.mp3`
- Source render audio: `temp/voice.wav`
- Subtitle text: `temp/captions.txt`
- Subtitle timing file: `temp/captions.srt`

## Notes

- The video is rendered as `1080x1920`.
- Gameplay footage is scaled to cover the frame and center-cropped instead of stretched.
- `generate` skips uploading completely.
- Stories are no longer truncated to a single Short. The pipeline renders the full story first, then splits it into 59-second parts.
- `run` uploads every generated part and titles them as `Part X/Y` when there is more than one video.
- `run` now prompts for Google login if a saved YouTube upload token is unavailable.
- `upload-temp` retries uploading the already-generated `temp/video_part*.mp4` files.
