import argparse
from pathlib import Path

from scripts.reddit_scraper import get_story
from scripts.caption_generator import generate_captions
from scripts.script_formatter import format_story
from scripts.voice_generator import generate_voice
from scripts.video_generator import create_video, split_video
from scripts.uploader import upload_videos

TEMP_OUTPUTS = {
    "voice.mp3",
    "voice.wav",
    "voice_raw.mp3",
    "captions.txt",
    "captions.srt",
    "video_full.mp4",
}


def cleanup_temp_files(temp_dir="temp"):
    for path in Path(temp_dir).glob("*"):
        if path.is_file() and (
            path.name in TEMP_OUTPUTS or path.name.startswith("video_part")
        ):
            path.unlink()


def _get_temp_video_parts(temp_dir="temp"):
    video_parts = sorted(Path(temp_dir).glob("video_part*.mp4"))
    if not video_parts:
        raise FileNotFoundError(
            f"No split video parts were found in '{Path(temp_dir).resolve()}'."
        )
    return video_parts


def generate_video():
    post = get_story()
    print(f"Selected story: {post['title']}")
    script = format_story(post)

    generate_voice(script)
    print("Voice generated.")

    generate_captions("temp/voice.wav")
    print("Captions generated.")

    full_video_path = create_video()
    print(f"Full video generated at {full_video_path}.")

    video_parts = split_video(full_video_path, title=post["title"])
    print(f"Split into {len(video_parts)} part(s).")
    for video_part in video_parts:
        print(f"Created {video_part}.")
    return post, video_parts


def run_full_pipeline():
    post, video_parts = generate_video()

    upload_videos(video_parts, base_title=post["title"])
    print("Upload completed.")

    cleanup_temp_files()
    print("Temporary files deleted.")


def upload_temp_parts(base_title="Crazy Reddit Story", temp_dir="temp"):
    video_parts = _get_temp_video_parts(temp_dir)
    print(f"Found {len(video_parts)} part(s) in {Path(temp_dir).resolve()}.")

    upload_videos(video_parts, base_title=base_title)
    print("Upload completed.")


def build_parser():
    parser = argparse.ArgumentParser(
        description="Generate and upload faceless YouTube Shorts from Reddit stories."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser(
        "generate",
        help="Generate the Reddit story video locally without uploading.",
    )
    subparsers.add_parser(
        "run",
        help="Run the full pipeline: generate, upload, then clean temp files.",
    )
    subparsers.add_parser(
        "clean",
        help="Delete files in the temp directory.",
    )
    upload_parser = subparsers.add_parser(
        "upload-temp",
        help="Upload existing split video parts from the temp directory.",
    )
    upload_parser.add_argument(
        "--title",
        default="Crazy Reddit Story",
        help="Base title to use for the uploaded Shorts.",
    )

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "generate":
        generate_video()
        return

    if args.command == "run":
        run_full_pipeline()
        return

    if args.command == "clean":
        cleanup_temp_files()
        print("Temporary files deleted.")
        return

    if args.command == "upload-temp":
        upload_temp_parts(base_title=args.title)
        return

    parser.error(f"Unknown command: {args.command}")


if __name__ == "__main__":
    main()
