import os
import json
import subprocess
import random

PHRASE_FILE = 'text/question-text.txt'
OUTPUT_DIR = 'output_wavs/question-test6'
FILENAME_PREFIX = 'merlin'
METADATA_FILENAME = 'metadata_multi_ref.txt'
DRY_RUN = False
START_INDEX = 1
F5_TTS_CLI = 'f5-tts_infer-cli'
MODEL = 'F5TTS_v1_Base'
SPEED = 0.8
NFE_STEP = 32
CROSS_FADE = 0.15
SEED = None #1025718871 #None #826061564  # or None for random
REF_JSON = 'config/ref_audio.json'

os.makedirs(OUTPUT_DIR, exist_ok=True)
with open(PHRASE_FILE, 'r', encoding='utf-8') as f:
    phrases = [line.strip() for line in f if line.strip()]
with open(REF_JSON, 'r', encoding='utf-8') as f:
    ref_map = json.load(f)

metadata = []

for ref_audio, info in ref_map.items():
    ref_base = os.path.splitext(os.path.basename(ref_audio))[0]
    ref_text = info['text']
    speaker = info.get('speaker', '')
    notes = info.get('notes', '')
    for idx, phrase in enumerate(phrases, start=START_INDEX):
        wav_filename = f"{ref_base}_{FILENAME_PREFIX}_{idx:02d}.wav"
        # Use global SEED if set, else random per phrase
        seed = SEED if SEED is not None else random.randint(0, 2**31-1)
        cmd = [
            F5_TTS_CLI,
            '--model', MODEL,
            '--ref_audio', ref_audio,
            '--ref_text', ref_text,
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
            subprocess.run(cmd, check=True)
        metadata.append(f"{wav_filename}|{phrase}|{seed}|{SPEED}|{NFE_STEP}|{CROSS_FADE}|{ref_audio}|{speaker}|{notes}")

with open(os.path.join(OUTPUT_DIR, METADATA_FILENAME), 'w', encoding='utf-8') as f:
    f.write("filename|phrase|seed|speed|nfe_step|cross_fade|ref_audio|speaker|notes\n")
    for line in metadata:
        f.write(line + '\n')

print("Multi-ref batch complete!")
