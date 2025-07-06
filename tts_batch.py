import os
import subprocess
import random

# ===== USER-ADJUSTABLE VARIABLES =====
PHRASE_FILE = 'text/merlin-set1.txt'
OUTPUT_DIR = 'output_wavs'
FILENAME_PREFIX = 'merlin'
METADATA_FILENAME = 'metadata.txt'  # will be written in OUTPUT_DIR
DRY_RUN = False
START_INDEX = 1
F5_TTS_CLI = 'f5-tts_infer-cli'
MODEL = 'F5TTS_v1_Base'
REF_AUDIO = 'audio/john_hurt_trimmed2.wav'
REF_TEXT = ("In this role I've participated in the telling of many stories. "
            "They were set in many different cultures, and involved many people "
            "from all races, religions and political beliefs.")

SPEED = 0.8
NFE_STEP = 32
CROSS_FADE = 0.15

SEED = None  # Set to an int for deterministic runs, or None for random seeds per phrase

# ======== SCRIPT STARTS HERE =========
os.makedirs(OUTPUT_DIR, exist_ok=True)

with open(PHRASE_FILE, 'r', encoding='utf-8') as f:
    phrases = [line.strip() for line in f if line.strip()]

metadata = []

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
        '--output_dir', OUTPUT_DIR,
        '--output_file', wav_filename,
        '--seed', str(seed),
        '--speed', str(SPEED),
        '--nfe_step', str(NFE_STEP),
        '--cross_fade_duration', str(CROSS_FADE),
    ]
    if DRY_RUN:
        print(" ".join(f'"{c}"' if ' ' in c else c for c in cmd))
    else:
        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error processing phrase {idx}: {phrase}\n{e}")
            continue  # skip to next

    # Log everything you want to track, in a pipe-delimited file
    # filename|phrase|seed|speed|nfe_step|cross_fade
    metadata.append(f"{wav_filename}|{phrase}|{seed}|{SPEED}|{NFE_STEP}|{CROSS_FADE}")

# Write metadata (pipe-delimited, with a header for easy review)
with open(os.path.join(OUTPUT_DIR, METADATA_FILENAME), 'w', encoding='utf-8') as f:
    f.write("filename|phrase|seed|speed|nfe_step|cross_fade\n")
    for line in metadata:
        f.write(line + '\n')

print(f"Done! {len(phrases)} files and metadata written to {OUTPUT_DIR}")
