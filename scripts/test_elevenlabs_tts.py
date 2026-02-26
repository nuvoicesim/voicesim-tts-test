#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tts_test.voice_profiles import load_voice_profiles


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate TTS audio using per-patient ElevenLabs voice profiles"
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=ROOT / "config" / "voices",
        help="Path to voice profiles directory",
    )
    parser.add_argument(
        "--profile",
        default=None,
        help="Profile name from config. If omitted, uses default profile",
    )
    parser.add_argument(
        "--text",
        default="Hello, this is a test line for our virtual patient.",
        help="Text to synthesize",
    )
    parser.add_argument(
        "--input-file",
        type=Path,
        default=None,
        help="Batch mode: text file with one utterance per line (# starts a comment)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "outputs",
        help="Directory for generated audio files",
    )
    parser.add_argument(
        "--format",
        default="pcm_16000",
        help="Output format (for example pcm_16000, mp3_22050_32)",
    )
    parser.add_argument(
        "--name",
        default=None,
        help="Optional output filename prefix (without extension)",
    )
    parser.add_argument(
        "--no-metadata",
        action="store_true",
        help="Disable writing ElevenLabs response metadata JSON sidecar",
    )
    parser.add_argument(
        "--play",
        action="store_true",
        help="Play the generated audio file after synthesis",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available profiles and exit",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    profiles, default_profile = load_voice_profiles(args.config)

    if args.list:
        print("Available profiles:")
        for name, profile in profiles.items():
            marker = " (default)" if name == default_profile else ""
            print(
                f"- {name}{marker}: profileId={profile.profile_id} | voiceId={profile.voice_id}"
            )
        return 0

    chosen_name = args.profile or default_profile
    if chosen_name not in profiles:
        valid = ", ".join(sorted(profiles.keys()))
        raise ValueError(f"Unknown profile '{chosen_name}'. Valid profiles: {valid}")

    from tts_test.elevenlabs_tts import ElevenLabsTTS

    profile = profiles[chosen_name]
    tts = ElevenLabsTTS()

    if args.input_file:
        texts = _read_input_lines(args.input_file)
        if not texts:
            raise ValueError(f"No usable lines found in {args.input_file}")

        print(f"Batch mode: {len(texts)} lines from {args.input_file}")
        print(f"Profile: {profile.name} (voiceId={profile.voice_id})")
        for idx, text in enumerate(texts, start=1):
            prefix = f"{args.name}_{idx:03d}" if args.name else f"{idx:03d}"
            output_path, metadata_path = tts.text_to_speech_file(
                text=text,
                profile=profile,
                output_dir=args.output_dir,
                output_format=args.format,
                filename_prefix=prefix,
                save_metadata=not args.no_metadata,
            )
            print(f"[{idx}/{len(texts)}] Saved: {output_path}")
            if metadata_path:
                print(f"[{idx}/{len(texts)}] Metadata: {metadata_path}")
            if args.play and idx == 1:
                _play_audio(output_path)
                print("Playback: completed (first item only)")
        return 0

    output_path, metadata_path = tts.text_to_speech_file(
        text=args.text,
        profile=profile,
        output_dir=args.output_dir,
        output_format=args.format,
        filename_prefix=args.name,
        save_metadata=not args.no_metadata,
    )

    print(f"Saved: {output_path}")
    if metadata_path:
        print(f"Metadata: {metadata_path}")
    print(f"Profile: {profile.name} (voiceId={profile.voice_id})")
    if args.play:
        _play_audio(output_path)
        print("Playback: completed")
    return 0


def _play_audio(audio_path: Path) -> None:
    candidates = [
        ["afplay", str(audio_path)],
        ["ffplay", "-nodisp", "-autoexit", "-loglevel", "error", str(audio_path)],
        ["aplay", str(audio_path)],
        ["paplay", str(audio_path)],
    ]
    for cmd in candidates:
        if shutil.which(cmd[0]):
            subprocess.run(cmd, check=True)
            return
    raise RuntimeError(
        "No supported audio player found. Install ffplay/aplay/paplay or use macOS afplay."
    )


def _read_input_lines(input_file: Path) -> list[str]:
    lines: list[str] = []
    for raw_line in input_file.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        lines.append(line)
    return lines


if __name__ == "__main__":
    raise SystemExit(main())
