from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict


@dataclass(frozen=True)
class VoiceProfile:
    name: str
    profile_id: str
    voice_id: str
    model_id: str
    stability: float
    similarity_boost: float
    style_exaggeration: float
    speed: float


def load_voice_profiles(config_path: Path) -> tuple[dict[str, VoiceProfile], str]:
    if not config_path.is_dir():
        raise ValueError(
            f"Expected a profiles directory at {config_path}. "
            "Use config/voices with one JSON file per profile."
        )
    return _load_from_directory(config_path)


def _build_profile(name: str, item: dict) -> VoiceProfile:
    profile_id = item.get("profileId", name)
    voice_id = item.get("voiceId")
    if not voice_id:
        raise ValueError(f"Missing required 'voiceId' in profile '{name}'")
    model_id = item.get("modelId")
    if not model_id:
        raise ValueError(f"Missing required 'modelId' in profile '{name}'")

    return VoiceProfile(
        name=name,
        profile_id=profile_id,
        voice_id=voice_id,
        model_id=model_id,
        stability=float(item.get("stability", 0.5)),
        similarity_boost=float(item.get("similarityBoost", 0.5)),
        style_exaggeration=float(item.get("styleExaggeration", 0.0)),
        speed=float(item.get("speed", 1.0)),
    )


def _load_from_directory(config_dir: Path) -> tuple[dict[str, VoiceProfile], str]:
    files = sorted(config_dir.glob("*.json"))
    if not files:
        raise ValueError(f"No profile JSON files found in {config_dir}")

    profiles: Dict[str, VoiceProfile] = {}
    for file_path in files:
        with file_path.open("r", encoding="utf-8") as f:
            item = json.load(f)
        profile_name = file_path.stem
        profile_id = item.get("profileId")
        if profile_id != profile_name:
            raise ValueError(
                f"Profile id mismatch in {file_path}: "
                f"profileId='{profile_id}' must match filename '{profile_name}'."
            )
        profiles[profile_name] = _build_profile(profile_name, item)

    default_profile_path = config_dir / "default_profile.txt"
    default_profile = (
        default_profile_path.read_text(encoding="utf-8").strip()
        if default_profile_path.exists()
        else ""
    )
    if default_profile not in profiles:
        default_profile = next(iter(profiles))

    return profiles, default_profile
