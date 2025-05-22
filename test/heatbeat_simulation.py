# -*- coding: utf-8 -*-
"""
Created on Thu May 15 05:23:19 2025

@author: oguzh
"""

import os
import subprocess
import datetime
from magenta.music import midi_io, sequences_lib
from midi2audio import FluidSynth

# === CONFIG ===
PRIMER = "[60, 62, 64, 65]"  # Simple melody seed
MODEL_PATH = "C:/Users/oguzh/magenta_musicgen/models/attention_rnn.mag"
OUTPUT_DIR = "C:/Users/oguzh/magenta_musicgen/output"
SOUNDFONT_PATH = "C:/Users/oguzh/fluidsynth-2.4.6-win10-x64/bin/FluidR3_GM.sf2"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# === Simulate heartbeat BPM variation ===
def heartbeat_bpm_sequence(base=70, variation=20, steps=4):
    """Yield simulated BPMs like a heart rate fluctuating."""
    for i in range(steps):
        yield base + variation * ((-1) ** i)

# === Generate melody MIDIs ===
generated_midis = []

for idx, bpm in enumerate(heartbeat_bpm_sequence(70, 20, 4)):
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    midi_name = f"heartbeat_{idx}_{bpm}bpm_{timestamp}.mid"
    midi_path = os.path.join(OUTPUT_DIR, midi_name)

    melody_cmd = [
        "melody_rnn_generate",
        "--config=attention_rnn",
        f"--bundle_file={MODEL_PATH}",
        f"--output_dir={OUTPUT_DIR}",
        "--num_outputs=1",
        "--num_steps=64",
        f"--primer_melody={PRIMER}",
        f"--bpm={bpm}"
    ]
    print(f"🎵 Generating melody at {bpm} BPM...")
    subprocess.run(melody_cmd, check=True)

    latest_file = sorted(
        [f for f in os.listdir(OUTPUT_DIR) if f.endswith(".mid")],
        key=lambda x: os.path.getmtime(os.path.join(OUTPUT_DIR, x))
    )[-1]
    latest_path = os.path.join(OUTPUT_DIR, latest_file)

    os.rename(latest_path, midi_path)
    generated_midis.append(midi_path)

# === Merge all generated MIDIs ===
print("🎼 Merging generated MIDI sequences...")
sequences = [midi_io.midi_file_to_note_sequence(path) for path in generated_midis]
merged_seq = sequences_lib.concatenate_sequences(sequences)

merged_mid_path = os.path.join(OUTPUT_DIR, "heartbeat_combined.mid")
midi_io.sequence_proto_to_midi_file(merged_seq, merged_mid_path)
print(f" Merged MIDI created: {merged_mid_path}")

# === Convert to WAV ===
print("🔊 Converting MIDI to WAV...")
fs = FluidSynth(SOUNDFONT_PATH)
wav_path = merged_mid_path.replace(".mid", ".wav")
fs.midi_to_audio(merged_mid_path, wav_path)

print(f"\n Done! Final audio file: {wav_path}")
