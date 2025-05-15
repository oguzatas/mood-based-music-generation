import os
import subprocess
from magenta.music import midi_io, sequences_lib
from midi2audio import FluidSynth

# === Settings ===
BPM = 90
NUM_STEPS = 256
PRIMER = "[60, 62, 64, 65]"
MODEL_DIR = "C:/Users/oguzh/magenta_musicgen/models"
OUTPUT_DIR = "C:/Users/oguzh/magenta_musicgen/output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# === 1. MELODY GENERATION ===
melody_cmd = [
    "melody_rnn_generate",
    "--config=attention_rnn",
    f"--bundle_file={MODEL_DIR}/attention_rnn.mag",
    f"--output_dir={OUTPUT_DIR}",
    "--num_outputs=1",
    f"--num_steps={NUM_STEPS}",
    f"--primer_melody={PRIMER}",
    f"--bpm={BPM}"
]
subprocess.run(melody_cmd, check=True)

# === 2. DRUMS GENERATION ===
drum_cmd = [
    "drums_rnn_generate",
    "--config=drum_kit_rnn",
    f"--bundle_file={MODEL_DIR}/drum_kit_rnn.mag",
    f"--output_dir={OUTPUT_DIR}",
    "--num_outputs=1",
    f"--num_steps={NUM_STEPS}",
    "--primer_drums=[36]",
    f"--bpm={BPM}"
]
subprocess.run(drum_cmd, check=True)

# === 3. Find the generated MIDI files ===
melody_mid = sorted([f for f in os.listdir(OUTPUT_DIR) if f.endswith(".mid") and "melody" in f])[-1]
drum_mid = sorted([f for f in os.listdir(OUTPUT_DIR) if f.endswith(".mid") and "drums" in f])[-1]

melody_path = os.path.join(OUTPUT_DIR, melody_mid)
drum_path = os.path.join(OUTPUT_DIR, drum_mid)

print(f" Melody file: {melody_path}")
# print(f" Drum file:   {drum_path}")

# === 4. Convert MIDI files to NoteSequence objects ===
melody_seq = midi_io.midi_file_to_note_sequence(melody_path)
drum_seq = midi_io.midi_file_to_note_sequence(drum_path)

# === 5. Merge the NoteSequence objects ===
#merged = sequences_lib.concatenate_sequences([melody_seq, drum_seq])
#merged_path = os.path.join(OUTPUT_DIR, "final_combined.mid")
#midi_io.sequence_proto_to_midi_file(merged, merged_path)

# === 6. Convert merged MIDI to WAV using FluidSynth with full executable path ===
soundfont = "C:/Users/oguzh/soundfonts/FluidR3_GM.sf2"
fluidsynth_path = "C:/Users/oguzh/fluidsynth-2.4.6-win10-x64/bin/fluidsynth.exe"

#fs = FluidSynth(sound_font=soundfont, executable=fluidsynth_path)
#wav_path = os.path.join(OUTPUT_DIR, "final_output.wav")
#fs.midi_to_audio(merged_path, wav_path)

#print(f"\n Generation completed! File: {wav_path}")
