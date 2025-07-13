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
REF_AUDIO_JSON = ROOT / "data" / "audio" / "ref_audio" / "final" / "ref_audio.json"
OUTPUT_BASE = ROOT / "outputs"
F5_TTS_CLI = ROOT / "f5_tts" / ".venv" / "Scripts" / "f5-tts_infer-cli.exe"

def clean_text(text):
    return re.sub(r"[^\w\s]", "", text.lower().strip())

def run_batch(config_path: Path):
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    # Config values
    ref_key = config["ref_key"]
    phrase_file = ROOT / "phrases" / config["phrase_file"]
    filename_prefix = config["filename_prefix"]
    model = config["model"]
    speed = config["speed"]
    nfe_step = config["nfe_step"]
    cross_fade = config["cross_fade"]
    remove_silence = config["remove_silence"]
    dry_run = config["dry_run"]
    start_index = config["start_index"]
    seed_setting = config["seed"]

    # Lookup ref
    with open(REF_AUDIO_JSON, "r", encoding="utf-8") as f:
        ref_map = json.load(f)
    if ref_key not in ref_map:
        raise KeyError(f"Ref key '{ref_key}' not found in {REF_AUDIO_JSON}")
    ref_entry = ref_map[ref_key]
    ref_audio = ROOT / ref_entry["relative_path"]
    ref_text = ref_entry["text"]

    # Output structure
    now_str = datetime.now().strftime("%Y-%m-%d_%H%M")
    refkey_prefix = Path(ref_key).stem
    run_name = f"{now_str}_{refkey_prefix}_v1"
    output_dir = OUTPUT_BASE / run_name
    audio_dir = output_dir / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)

    # Load phrases
    with open(phrase_file, "r", encoding="utf-8") as f:
        phrases = [line.strip() for line in f if line.strip()]

    metadata_rows = []

    for idx, phrase in enumerate(phrases, start=start_index):
        wav_filename = f"{filename_prefix}_{idx:02d}.wav"
        seed = seed_setting if seed_setting is not None else random.randint(0, 2**31 - 1)

        cmd = [
            str(F5_TTS_CLI),
            '--model', model,
            '--ref_audio', str(ref_audio),
            '--ref_text', ref_text,
            '--gen_text', phrase,
            '--output_dir', str(audio_dir),
            '--output_file', wav_filename,
            '--seed', str(seed),
            '--speed', str(speed),
            '--nfe_step', str(nfe_step),
            '--cross_fade_duration', str(cross_fade),
        ]
        if remove_silence:
            cmd.append('--remove_silence')

        if dry_run:
            print(" ".join(f'"{str(c)}"' if " " in str(c) else str(c) for c in cmd))
        else:
            try:
                subprocess.run(cmd, check=True)
            except subprocess.CalledProcessError as e:
                print(f"Error processing phrase {idx}: {phrase}\n{e}")
                continue

        metadata_rows.append({
            "filename": wav_filename,
            "text": phrase,
            "text_clean": clean_text(phrase),
            "speaker": ref_entry.get("speaker", ""),
            "style": ref_entry.get("intonation", ""),
            "speed": speed,
            "seed": seed,
            "ref_key": ref_key,
            "notes": ref_entry.get("notes", ""),
            "ref_audio": str(ref_audio),
            "gen_text_index": idx,
        })

    # Write metadata.csv
    csv_path = output_dir / "metadata.csv"
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=metadata_rows[0].keys())
        writer.writeheader()
        writer.writerows(metadata_rows)

    # Write ref_key.json
    with open(output_dir / "ref_key.json", "w", encoding="utf-8") as f:
        json.dump(ref_entry, f, indent=2)

    # Write README.md
    readme_text = f"""\
# Merlin TTS Batch Run

- 📅 Date: {now_str}
- 🔑 Reference Key: {ref_key}
- 🧾 Reference Text: "{ref_text}"
- 🗣️ Speaker: {ref_entry.get("speaker", "")}
- 🎭 Intonation: {ref_entry.get("intonation", "")}
- 📝 Notes: {ref_entry.get("notes", "")}
- 📂 Phrase File: {phrase_file.name}
- 🚀 Speed: {speed}
- 🎛️ Cross-Fade: {cross_fade}
- 🌀 NFE Step: {nfe_step}
- 🔧 Remove Silence: {remove_silence}
- 🎧 Samples Generated: {len(metadata_rows)}

Generated using `tts_batch.py` and F5-TTS CLI.
"""
    with open(output_dir / "README.md", "w", encoding="utf-8") as f:
        f.write(readme_text)

    # Write log.txt
    with open(output_dir / "log.txt", "w", encoding="utf-8") as f:
        for row in metadata_rows:
            cli_cmd = [
                str(F5_TTS_CLI),
                "--model", model,
                "--ref_audio", str(ref_audio),
                "--ref_text", ref_text,
                "--gen_text", row["text"],
                "--output_dir", str(audio_dir),
                "--output_file", row["filename"],
                "--seed", str(row["seed"]),
                "--speed", str(speed),
                "--nfe_step", str(nfe_step),
                "--cross_fade_duration", str(cross_fade),
            ]
            if remove_silence:
                cli_cmd.append('--remove_silence')
            f.write(" ".join(f'"{str(c)}"' if " " in str(c) else str(c) for c in cli_cmd) + "\n")

    if dry_run:
        print(f"[DRY RUN] Would have generated {len(metadata_rows)} samples in {output_dir}")
    else:
        print(f"✅ Done! {len(metadata_rows)} samples and metadata written to {output_dir}")

# === CLI entrypoint ===
if __name__ == "__main__":
    config_path = ROOT / "f5_tts" / "config" / "tts_batch_config.json"
    run_batch(config_path)
