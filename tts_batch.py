import os
import subprocess
import random
import json
import re
import csv
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent  # Project root

# ===== USER-ADJUSTABLE VARIABLES =====
REF_KEY = "jh_inthisrole-9s.wav"
REF_AUDIO_JSON = ROOT / "data" / "audio" / "ref_audio" / "final" / "ref_audio.json"
with open(REF_AUDIO_JSON, "r", encoding="utf-8") as f:
    ref_map = json.load(f)

if REF_KEY not in ref_map:
    raise KeyError(f"Ref key '{REF_KEY}' not found in {REF_AUDIO_JSON}")
ref_entry = ref_map[REF_KEY]
REF_AUDIO = ROOT / ref_entry["relative_path"]
REF_TEXT = ref_entry["text"]

PHRASE_FILE = ROOT / "phrases" / "merlin-set2.txt"


OUTPUT_BASE = ROOT / "outputs"
now_str = datetime.now().strftime("%Y-%m-%d_%H%M")
refkey_prefix = Path(REF_KEY).stem
run_name = f"{now_str}_{refkey_prefix}_v1"

OUTPUT_DIR = OUTPUT_BASE / run_name
AUDIO_DIR = OUTPUT_DIR / "audio"

# Make sure directories exist
AUDIO_DIR.mkdir(parents=True, exist_ok=True)


FILENAME_PREFIX = 'merlin'
DRY_RUN = False
START_INDEX = 1
F5_TTS_CLI = ROOT / "f5_tts" / ".venv" / "Scripts" / "f5-tts_infer-cli.exe"
MODEL = 'F5TTS_v1_Base'
SPEED = 0.8
NFE_STEP = 32
CROSS_FADE = 0.15
REMOVE_SILENCE = False


SEED = None  # Set to an int for deterministic runs, or None for random seeds per phrase

# ======== SCRIPT STARTS HERE =========

def clean_text(text):
    return re.sub(r"[^\w\s]", "", text.lower().strip())


os.makedirs(OUTPUT_DIR, exist_ok=True)

with open(PHRASE_FILE, 'r', encoding='utf-8') as f:
    phrases = [line.strip() for line in f if line.strip()]

metadata_rows = []

for idx, phrase in enumerate(phrases, start=START_INDEX):
    wav_filename = f"{FILENAME_PREFIX}_{idx:02d}.wav"
    # Use global SEED if set, else random per phrase
    seed = SEED if SEED is not None else random.randint(0, 2**31-1)

    cmd = [
        F5_TTS_CLI,
        '--model', MODEL,
        '--ref_audio', REF_AUDIO,
        '--ref_text', REF_TEXT,
        '--gen_text', phrase,
        '--output_dir', str(AUDIO_DIR),
        '--output_file', wav_filename,
        '--seed', str(seed),
        '--speed', str(SPEED),
        '--nfe_step', str(NFE_STEP),
        '--cross_fade_duration', str(CROSS_FADE),
    ]

    if REMOVE_SILENCE:
        cmd.append('--remove_silence')

    if DRY_RUN:
        print(" ".join(f'"{c}"' if ' ' in c else c for c in cmd))
    else:
        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error processing phrase {idx}: {phrase}\n{e}")
            continue  # skip to next

    # Log everything you want to track, in a pipe-delimited file
    metadata_rows.append({
        "filename": wav_filename,
        "text": phrase,
        "text_clean": clean_text(phrase),
        "speaker": ref_entry.get("speaker", ""),
        "style": ref_entry.get("intonation", ""),
        "speed": SPEED,
        "seed": seed,
        "ref_key": REF_KEY,
        "notes": ref_entry.get("notes", ""),
        "ref_audio": str(REF_AUDIO),
        "gen_text_index": idx,
    })

# Write metadata (pipe-delimited, with a header for easy review)
csv_path = OUTPUT_DIR / "metadata.csv"
with open(csv_path, "w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=metadata_rows[0].keys())
    writer.writeheader()
    writer.writerows(metadata_rows)


with open(OUTPUT_DIR / "ref_key.json", "w", encoding="utf-8") as f:
    json.dump(ref_entry, f, indent=2)


readme_text = f"""\
# Merlin TTS Batch Run

- 📅 Date: {now_str}
- 🔑 Reference Key: {REF_KEY}
- 🧾 Reference Text: "{REF_TEXT}"
- 🗣️ Speaker: {ref_entry.get("speaker", "")}
- 🎭 Intonation: {ref_entry.get("intonation", "")}
- 📝 Notes: {ref_entry.get("notes", "")}
- 📂 Phrase File: {PHRASE_FILE.name}
- 🚀 Speed: {SPEED}
- 🎛️ Cross-Fade: {CROSS_FADE}
- 🌀 NFE Step: {NFE_STEP}
- 🔧 Remove Silence: {False}
- 🎧 Samples Generated: {len(metadata_rows)}

Generated using `tts_batch.py` and F5-TTS CLI.
"""

with open(OUTPUT_DIR / "README.md", "w", encoding="utf-8") as f:
    f.write(readme_text)


with open(OUTPUT_DIR / "log.txt", "w", encoding="utf-8") as f:
    for row in metadata_rows:
        cli_cmd = [
            F5_TTS_CLI,
            "--model", MODEL,
            "--ref_audio", str(REF_AUDIO),
            "--ref_text", REF_TEXT,
            "--gen_text", row["text"],
            "--output_dir", str(AUDIO_DIR),
            "--output_file", row["filename"],
            "--seed", str(row["seed"]),
            "--speed", str(SPEED),
            "--nfe_step", str(NFE_STEP),
            "--cross_fade_duration", str(CROSS_FADE),
        ]
        f.write(" ".join(f'"{str(c)}"' if " " in c else c for c in cli_cmd) + "\n")



if DRY_RUN:
    print(f"[DRY RUN] Would have generated {len(metadata_rows)} samples in {OUTPUT_DIR}")
else:
    print(f"✅ Done! {len(metadata_rows)} samples and metadata written to {OUTPUT_DIR}")

