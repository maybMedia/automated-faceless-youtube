import subprocess
from pathlib import Path
import math
import textwrap

from scripts.config import log_step

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FULL_VIDEO_PATH = PROJECT_ROOT / "temp" / "video_full.mp4"
PART_VIDEO_TEMPLATE = "video_part{index:02}.mp4"


def _ffmpeg_subtitle_path(path):
    resolved = (PROJECT_ROOT / path).resolve()
    normalized = resolved.as_posix()
    drive, remainder = normalized.split(":/", maxsplit=1)
    return f"{drive}\\:/{remainder}"


def _escape_drawtext(text):
    return (
        text.replace("\\", "\\\\")
        .replace("\n", r"\n")
        .replace(":", r"\:")
        .replace("'", r"\'")
        .replace(",", r"\,")
        .replace("[", r"\[")
        .replace("]", r"\]")
        .replace("%", r"\%")
    )


def _format_title_for_card(title, width=28):
    return textwrap.wrap(title.strip(), width=width) or [title.strip()]


def _part_intro_filter(title, part_index, total_parts, duration=4):
    title_lines = _format_title_for_card(title)
    card_part = _escape_drawtext(f"Part {part_index}/{total_parts}")
    title_start_y = 196
    title_line_height = 52
    footer_y = title_start_y + (len(title_lines) * title_line_height) + 12
    card_height = max(250, footer_y - 108 + 58)
    filters = [
        f"drawbox=x=96:y=120:w=888:h={card_height}:color=black@0.22:t=fill:enable='lt(t,4)'",
        f"drawbox=x=84:y=108:w=888:h={card_height}:color=white@0.94:t=fill:enable='lt(t,4)'",
        "drawbox=x=84:y=108:w=888:h=24:color=0xFF4500@1.0:t=fill:enable='lt(t,4)'",
        (
            "drawtext=font='Segoe UI Semibold':fontsize=26:fontcolor=0xFF4500:"
            f"text='{card_part}':x=132:y=156:enable='lt(t,{duration})'"
        ),
    ]

    for index, line in enumerate(title_lines, start=0):
        filters.append(
            "drawtext=font='Segoe UI Semibold':fontsize=40:fontcolor=0x1A1A1B:"
            f"text='{_escape_drawtext(line)}':x=132:y={title_start_y + (index * title_line_height)}:"
            f"enable='lt(t,{duration})'"
        )

    filters.append(
        "drawtext=font='Segoe UI':fontsize=22:fontcolor=0x787C7E:"
        f"text='r/AskReddit Story':x=132:y={footer_y}:"
        f"enable='lt(t,{duration})'"
    )

    return ",".join(filters)


def create_video(subtitle_path="temp/captions.srt", output_path=None):
    subtitle_filter = (
        "scale='if(gte(iw/ih,9/16),-2,1080)':'if(gte(iw/ih,9/16),1920,-2)',"
        "crop=1080:1920,"
        f"subtitles='{_ffmpeg_subtitle_path(subtitle_path)}':"
        "force_style='FontName=Segoe UI Semibold,Alignment=2,FontSize=18,"
        "PrimaryColour=&HFFFFFF&,OutlineColour=&H202020&,BorderStyle=1,"
        "Outline=1.2,Shadow=0.8,MarginV=72,Spacing=0.2'"
    )
    target_path = output_path or FULL_VIDEO_PATH

    command = [
        "ffmpeg",
        "-y",
        "-stream_loop", "-1",
        "-i", str((PROJECT_ROOT / "assets" / "gameplay.mp4").resolve()),
        "-i", str((PROJECT_ROOT / "temp" / "voice.wav").resolve()),
        "-shortest",
        "-vf", subtitle_filter,
        "-c:v", "libx264",
        "-c:a", "aac",
        str(target_path),
    ]

    log_step(f"Starting ffmpeg render for full video at {target_path}.")
    log_step(f"Using subtitles file {subtitle_path}.")
    subprocess.run(command, check=True)
    log_step(f"Finished ffmpeg render for full video at {target_path}.")
    return target_path


def _get_media_duration(path):
    log_step(f"Probing media duration for {path}.")
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    duration = float(result.stdout.strip())
    log_step(f"Detected duration {duration:.2f}s for {path}.")
    return duration


def split_video(video_path=None, max_duration=59, title="Reddit Story"):
    source_path = Path(video_path) if video_path else FULL_VIDEO_PATH
    temp_dir = source_path.parent
    duration = _get_media_duration(source_path)
    part_count = max(1, math.ceil(duration / max_duration))
    output_paths = []
    log_step(
        f"Splitting {source_path} into {part_count} part(s) with max duration "
        f"{max_duration}s."
    )

    for part_index in range(part_count):
        start_time = part_index * max_duration
        part_duration = min(max_duration, duration - start_time)
        output_path = temp_dir / PART_VIDEO_TEMPLATE.format(index=part_index + 1)
        video_filter = _part_intro_filter(title, part_index + 1, part_count)

        command = [
            "ffmpeg",
            "-y",
            "-ss",
            str(start_time),
            "-i",
            str(source_path),
            "-t",
            str(part_duration),
            "-vf",
            video_filter,
            "-c:v",
            "libx264",
            "-c:a",
            "aac",
            str(output_path),
        ]
        log_step(
            f"Rendering part {part_index + 1}/{part_count}: "
            f"start={start_time:.2f}s duration={part_duration:.2f}s."
        )
        subprocess.run(command, check=True)
        log_step(f"Finished rendering {output_path}.")
        output_paths.append(output_path)

    return output_paths
