from pathlib import Path

import whisper

from scripts.config import log_step


def _format_srt_timestamp(seconds):
    milliseconds = int(round(seconds * 1000))
    hours, remainder = divmod(milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    secs, millis = divmod(remainder, 1000)
    return f"{hours:02}:{minutes:02}:{secs:02},{millis:03}"


def generate_captions(
    audio_path="temp/voice.mp3",
    output_path="temp/captions.txt",
    subtitle_path="temp/captions.srt",
):
    log_step("Loading Whisper model 'base' for caption generation.")
    model = whisper.load_model("base")
    log_step(f"Starting transcription for {Path(audio_path).resolve()}.")
    result = model.transcribe(audio_path, word_timestamps=True)
    log_step(
        f"Transcription complete with {len(result.get('segments', []))} segments."
    )

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(result["text"], encoding="utf-8")
    log_step(f"Wrote caption text to {output_file.resolve()}.")

    subtitle_file = Path(subtitle_path)
    subtitle_lines = []

    subtitle_index = 1
    for segment in result.get("segments", []):
        words = segment.get("words") or []

        if words:
            for word in words:
                word_text = word.get("word", "").strip()
                if not word_text:
                    continue

                subtitle_lines.extend(
                    [
                        str(subtitle_index),
                        (
                            f"{_format_srt_timestamp(word['start'])} --> "
                            f"{_format_srt_timestamp(word['end'])}"
                        ),
                        word_text,
                        "",
                    ]
                )
                subtitle_index += 1
            continue

        # Fallback for segments without word timestamps.
        segment_text = segment.get("text", "").strip()
        split_words = segment_text.split()
        if not split_words:
            continue

        segment_start = segment["start"]
        segment_end = segment["end"]
        word_duration = (segment_end - segment_start) / len(split_words)

        for word_offset, word_text in enumerate(split_words):
            word_start = segment_start + (word_offset * word_duration)
            word_end = word_start + word_duration
            subtitle_lines.extend(
                [
                    str(subtitle_index),
                    (
                        f"{_format_srt_timestamp(word_start)} --> "
                        f"{_format_srt_timestamp(word_end)}"
                    ),
                    word_text,
                    "",
                ]
            )
            subtitle_index += 1

    subtitle_file.write_text("\n".join(subtitle_lines), encoding="utf-8")
    log_step(
        f"Wrote subtitle timings to {subtitle_file.resolve()} "
        f"({subtitle_index - 1} subtitle lines)."
    )

    return result["text"]
