import os
import subprocess

from elevenlabs import save
from elevenlabs.client import ElevenLabs

from scripts.config import PROJECT_ROOT

DEFAULT_VOICE_ID = "EXAVITQu4vr4xnSDxMaL"
VOICE_SPEED_MULTIPLIER = 1.3


def _generate_voice_with_windows_tts(script, output_path):
    escaped_script = script.replace("'", "''")
    escaped_output = str(output_path).replace("'", "''")
    command = (
        "Add-Type -AssemblyName System.Speech; "
        "$speaker = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
        f"$speaker.SetOutputToWaveFile('{escaped_output}'); "
        f"$speaker.Speak('{escaped_script}'); "
        "$speaker.Dispose()"
    )
    subprocess.run(["powershell", "-NoProfile", "-Command", command], check=True)


def _speed_up_audio(input_path, output_path):
    sped_up_path = output_path.with_name(f"{output_path.stem}_sped{output_path.suffix}")
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(input_path),
            "-filter:a",
            f"atempo={VOICE_SPEED_MULTIPLIER}",
            str(sped_up_path),
        ],
        check=True,
    )
    sped_up_path.replace(output_path)


def _convert_audio(input_path, output_path):
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(input_path),
            str(output_path),
        ],
        check=True,
    )


def generate_voice(script):
    temp_dir = PROJECT_ROOT / "temp"
    temp_dir.mkdir(parents=True, exist_ok=True)
    wav_output = temp_dir / "voice.wav"
    mp3_output = temp_dir / "voice.mp3"

    api_key = os.getenv("ELEVENLABS_API_KEY")
    if api_key:
        voice_id = os.getenv("ELEVENLABS_VOICE_ID", DEFAULT_VOICE_ID)
        if not voice_id or voice_id.startswith("your_"):
            voice_id = DEFAULT_VOICE_ID

        client = ElevenLabs(api_key=api_key)
        audio = client.text_to_speech.convert(
            voice_id=voice_id,
            text=script,
            model_id="eleven_multilingual_v2",
        )

        raw_mp3_output = temp_dir / "voice_raw.mp3"
        save(audio, str(raw_mp3_output))
        _convert_audio(raw_mp3_output, wav_output)
        raw_mp3_output.unlink(missing_ok=True)
        _speed_up_audio(wav_output, wav_output)
        _convert_audio(wav_output, mp3_output)
        return

    _generate_voice_with_windows_tts(script, wav_output)
    _speed_up_audio(wav_output, wav_output)
    _convert_audio(wav_output, mp3_output)
