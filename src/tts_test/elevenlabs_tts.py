from __future__ import annotations

import base64
import json
import os
import uuid
import wave
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from elevenlabs import VoiceSettings
from elevenlabs.client import ElevenLabs

from .voice_profiles import VoiceProfile


class ElevenLabsTTS:
    def __init__(self, api_key: str | None = None) -> None:
        load_dotenv()
        key = api_key or os.getenv("ELEVENLABS_API_KEY")
        if not key:
            raise ValueError("ELEVENLABS_API_KEY is not set. Add it to .env.")
        self.client = ElevenLabs(api_key=key)

    def text_to_speech_file(
        self,
        text: str,
        profile: VoiceProfile,
        output_dir: Path,
        output_format: str,
        filename_prefix: str | None = None,
        save_metadata: bool = True,
    ) -> tuple[Path, Path | None]:
        output_dir.mkdir(parents=True, exist_ok=True)
        file_id = filename_prefix or str(uuid.uuid4())
        extension = _extension_for_output_format(output_format)
        output_path = output_dir / f"{file_id}.{extension}"

        if save_metadata:
            response = self.client.text_to_speech.convert_with_timestamps(
                voice_id=profile.voice_id,
                output_format=output_format,
                text=text,
                model_id=profile.model_id,
                voice_settings=VoiceSettings(
                    stability=profile.stability,
                    similarity_boost=profile.similarity_boost,
                    style=profile.style_exaggeration,
                    speed=profile.speed,
                ),
            )
            payload = _to_serializable(response)
            audio_bytes = _extract_audio_bytes(payload, response)
            _write_audio_file(output_path, output_format, audio_bytes)

            metadata_path = output_dir / f"{file_id}.json"
            payload_without_audio = {
                k: v
                for k, v in payload.items()
                if k not in {"audio_base64", "audio_base_64", "audio"}
            }
            metadata = {
                "provider": "elevenlabs",
                "profile_name": profile.name,
                "voiceProfile": {
                    "profileId": profile.profile_id,
                    "voiceId": profile.voice_id,
                    "modelId": profile.model_id,
                    "stability": profile.stability,
                    "similarityBoost": profile.similarity_boost,
                    "styleExaggeration": profile.style_exaggeration,
                    "speed": profile.speed,
                },
                "output_format": output_format,
                "text": text,
                "response": payload_without_audio,
            }
            with metadata_path.open("w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2, ensure_ascii=True)
            return output_path, metadata_path

        response = self.client.text_to_speech.convert(
            voice_id=profile.voice_id,
            output_format=output_format,
            text=text,
            model_id=profile.model_id,
            voice_settings=VoiceSettings(
                stability=profile.stability,
                similarity_boost=profile.similarity_boost,
                style=profile.style_exaggeration,
                speed=profile.speed,
            ),
        )
        if output_format == "pcm_16000":
            raw_audio = bytearray()
            for chunk in response:
                if chunk:
                    raw_audio.extend(chunk)
            _write_audio_file(output_path, output_format, bytes(raw_audio))
            return output_path, None
        with output_path.open("wb") as f:
            for chunk in response:
                if chunk:
                    f.write(chunk)
        return output_path, None


def _to_serializable(obj: Any) -> dict[str, Any]:
    if isinstance(obj, dict):
        return obj
    if hasattr(obj, "model_dump"):
        dumped = obj.model_dump(by_alias=True)
        if isinstance(dumped, dict):
            return dumped
        dumped = obj.model_dump()
        if isinstance(dumped, dict):
            return dumped
    if hasattr(obj, "dict"):
        dumped = obj.dict()
        if isinstance(dumped, dict):
            return dumped
    if hasattr(obj, "__dict__"):
        data = dict(obj.__dict__)
        if isinstance(data, dict):
            return data
    raise ValueError("Unable to serialize ElevenLabs response payload.")


def _extract_audio_bytes(payload: dict[str, Any], response_obj: Any) -> bytes:
    candidates: list[Any] = [
        payload.get("audio_base64"),
        payload.get("audio_base_64"),
        payload.get("audio"),
    ]
    for attr in ("audio_base64", "audio_base_64", "audio"):
        if hasattr(response_obj, attr):
            candidates.append(getattr(response_obj, attr))

    for value in candidates:
        if value is None:
            continue
        if isinstance(value, bytes):
            return value
        if isinstance(value, str):
            try:
                return base64.b64decode(value)
            except Exception:
                continue

    keys = ", ".join(sorted(payload.keys()))
    raise ValueError(
        f"ElevenLabs response did not include recognizable audio field. payload keys: {keys}"
    )


def _extension_for_output_format(output_format: str) -> str:
    if output_format == "pcm_16000":
        return "wav"
    return output_format.split("_", 1)[0]


def _write_audio_file(path: Path, output_format: str, audio_bytes: bytes) -> None:
    if output_format == "pcm_16000":
        _write_pcm_16khz_wav(path, audio_bytes)
        return
    with path.open("wb") as f:
        f.write(audio_bytes)


def _write_pcm_16khz_wav(path: Path, pcm_bytes: bytes) -> None:
    with wave.open(str(path), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(16000)
        wav_file.writeframes(pcm_bytes)
