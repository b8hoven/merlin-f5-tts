import subprocess

SEED = 826061564
SPEED = 0.8
NFE = 32
CROSSFADE = 0.15
REF_AUDIO = "audio/john_hurt_trimmed2.wav"
REF_TEXT = ("In this role I've participated in the telling of many stories. "
            "They were set in many different cultures, and involved many people "
            "from all races, religions and political beliefs.")
GEN_TEXT = "Good afternoon Mark. It's twenty degrees and sunny today. Enjoy the weather."
OUTPUT_DIR = "outputs_vocos"

cmd = [
    "f5-tts_infer-cli",
    "--model", "F5TTS_v1_Base",
    "--ref_audio", REF_AUDIO,
    "--ref_text", REF_TEXT,
    "--gen_text", GEN_TEXT,
    "--output_dir", OUTPUT_DIR,
    "--speed", str(SPEED),
    "--cross_fade_duration", str(CROSSFADE),
    "--nfe_step", str(NFE),
    "--seed", str(SEED)
]

subprocess.run(cmd)
