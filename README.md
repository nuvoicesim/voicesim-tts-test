# ElevenLabs TTS Test (voice-sim)

This project gives you a clean way to test ElevenLabs voices per virtual patient.

## Structure

- `config/voices/`: one JSON file per voice profile
- `config/voices/default_profile.txt`: default profile name
- `src/tts_test/voice_profiles.py`: profile loading
- `src/tts_test/elevenlabs_tts.py`: ElevenLabs client wrapper
- `scripts/test_elevenlabs_tts.py`: CLI for quick tests
- `outputs/`: generated audio files

This repo is for rapid TTS iteration: create or tune patient voice profiles, synthesize sample lines, and review audio output before Unity/App integration.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Set `ELEVENLABS_API_KEY` in `.env` before running synthesis.

## Usage

List patient profiles:

```bash
python scripts/test_elevenlabs_tts.py --list
```

Generate audio with default profile:

```bash
python scripts/test_elevenlabs_tts.py --text "Hi, I am your virtual patient."
```

Generate audio with a specific patient profile:

```bash
python scripts/test_elevenlabs_tts.py \
  --profile simulation_level_2 \
  --text "I have had chest pain for two days." \
  --name sim2_case_001
```

Generate in batch from a text file (one utterance per line):

```bash
python scripts/test_elevenlabs_tts.py \
  --profile simulation_level_2 \
  --input-file scripts/sample_lines.txt \
  --name sim2_batch
```

Batch notes:

- Empty lines are ignored.
- Lines starting with `#` are treated as comments.
- Output names are indexed: `sim2_batch_001.wav`, `sim2_batch_002.wav`, etc.

Output files are written to `outputs/` by default:

- `*.wav`: synthesized audio (PCM 16-bit mono @ 16kHz)
- `*.json`: ElevenLabs response metadata (for example alignment/timestamp data)

If you only want audio:

```bash
.venv/bin/python scripts/test_elevenlabs_tts.py --no-metadata --text "Test line"
```

Play generated audio immediately:

```bash
.venv/bin/python scripts/test_elevenlabs_tts.py --play --text "Test line"
```

`--play` uses `afplay` (macOS) or `ffplay`/`aplay`/`paplay` when available.

## Adding a new patient voice

Create a new file in `config/voices/` (filename becomes profile name):

```json
{
  "profileId": "broca_aphasia_male_elderly_anxious",
  "voiceId": "YOUR_ELEVENLABS_VOICE_ID",
  "modelId": "eleven_multilingual_v2",
  "stability": 0.25,
  "similarityBoost": 0.65,
  "styleExaggeration": 0.15,
  "speed": 1.0
}
```

Convention (required): set `profileId` exactly equal to the filename stem.

Example: `config/voices/broca_aphasia_male_elderly_anxious.json` should contain `"profileId": "broca_aphasia_male_elderly_anxious"`.

To change the default profile, edit `config/voices/default_profile.txt`.

Audio format is selected at runtime via `--format` (default: `pcm_16000`).

### Steps for adding a new profile

1. Choose a profile key (for example `broca_aphasia_female_task2`).
2. Create `config/voices/<profile_key>.json`.
3. Set `"profileId"` to exactly the same `<profile_key>`.
4. Fill `voiceId`, `modelId`, and voice settings fields.
5. Run `python scripts/test_elevenlabs_tts.py --list` and confirm the new profile appears.
6. Add the new profile name to the `Starter profile set` section in this README.
7. If it should be default, update `config/voices/default_profile.txt`.

## Starter profile set

- `simulation_level_1` (voiceId `QXFI3J7JB0fOlMwKDUxE`)
- `simulation_level_2` (voiceId `KjIBD4QnlzAqKHmoYfdZ`)
- `simulation_level_3` (voiceId `nlPFgtYJ0K18Hij3YdiX`)
- `broca_aphasia_male_elderly_anxious` (placeholder)
- `broca_aphasia_female_elderly_anxious` (placeholder)
- `broca_aphasia_male_young_anxious` (placeholder)

Replace `VOICE_ID_PLACEHOLDER` with a real ElevenLabs voice ID before synthesis.
