import os
import subprocess
import random
from datetime import datetime

from midi2audio import FluidSynth

# === Paths ===
MODEL_DIR = "C:/Users/oguzh/magenta_musicgen/models"
OUTPUT_DIR = "C:/Users/oguzh/magenta_musicgen/output"
SOUNDFONT_PATH = "C:/Users/oguzh/fluidsynth-2.4.6-win10-x64/bin/FluidR3_GM.sf2"

os.makedirs(OUTPUT_DIR, exist_ok=True)

# === Mood Settings ===
MOOD_SETTINGS = {
    "happy": {
        "mode": "major",
        "primer": [64, 66, 68, 71],  # E major
        "temperature": 1.1
    },
    "sad": {
        "mode": "minor",
        "primer": [60, 62, 63, 67],  # C minor
        "temperature": 1.3
    },
    "angry": {
        "mode": "phrygian",
        "primer": [60, 61, 63, 65],
        "temperature": 1.5
    },
    "relaxed": {
        "mode": "major",
        "primer": [60, 62, 64, 65],  # C major
        "temperature": 0.9
    },
    "mysterious": {
        "mode": "locrian",
        "primer": [60, 61, 63, 66],  # Locrian feel
        "temperature": 1.4
    }
}

def generate_music(mood: str, heartbeat_bpm: int):
    if mood not in MOOD_SETTINGS:
        raise ValueError(f"Unsupported mood: {mood}")

    settings = MOOD_SETTINGS[mood]
    primer = settings["primer"]
    temperature = settings["temperature"]

    bpm = max(40, min(heartbeat_bpm, 200))  # Clamp for safety
    num_steps = 256

    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    melody_filename = f"melody_{mood}_{timestamp}.mid"
    wav_filename = f"final_{mood}_{timestamp}.wav"

    # === 1. Melody Generation ===
    melody_cmd = [
        "melody_rnn_generate",
        "--config=attention_rnn",
        f"--bundle_file={MODEL_DIR}/attention_rnn.mag",
        f"--output_dir={OUTPUT_DIR}",
        "--num_outputs=1",
        f"--num_steps={num_steps}",
        f"--primer_melody={primer}",
        f"--temperature={temperature}",
        f"--bpm={bpm}",
        f"--output_file={melody_filename}"
    ]
    subprocess.run(melody_cmd, check=True)

    melody_path = os.path.join(OUTPUT_DIR, melody_filename)
    wav_path = os.path.join(OUTPUT_DIR, wav_filename)

    # === 2. Convert to Audio ===
    fs = FluidSynth(SOUNDFONT_PATH)
    fs.midi_to_audio(melody_path, wav_path)

    print(f"\n🎵 Mood: {mood} | BPM: {bpm} | Temperature: {temperature}")
    print(f"✅ Output WAV: {wav_path}")

# === Example Usage ===
if __name__ == "__main__":
    generate_music(mood="mysterious", heartbeat_bpm=75)
