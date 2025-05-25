from music21 import converter
from pathlib import Path
from typing import List
import numpy as np

def midi_to_symbolic_text(midi_path: Path) -> str:
    """
    Convert a MIDI file to a symbolic text representation using music21.
    Each line is a note, chord, or rest with its duration.
    """
    score = converter.parse(str(midi_path))
    symbolic = []
    for el in score.flat.notesAndRests:
        if el.isNote:
            symbolic.append(f"{el.nameWithOctave} {el.quarterLength}")
        elif el.isChord:
            symbolic.append(f"{'-'.join(n.nameWithOctave for n in el.notes)} {el.quarterLength}")
        elif el.isRest:
            symbolic.append(f"Rest {el.quarterLength}")
    return '\n'.join(symbolic)

def prepare_llm_prompt_from_midi(midi_path: Path, target_mood: str, target_bpm: float, target_variability: float = None) -> str:
    symbolic_text = midi_to_symbolic_text(midi_path)
    prompt = (
        f"Here is a symbolic representation of a generated song:\n"
        f"{symbolic_text}\n"
        f"The target mood was '{target_mood}'. "
        f"The target tempo was {target_bpm:.1f} BPM.\n"
        f"The target rhythmic variability was {target_variability if target_variability is not None else 'N/A'}.\n"
        f"Please analyze this music. Does it match the intended mood and tempo? Why or why not? "
        f"Give a score from 1 (not matching) to 10 (perfect match), and provide suggestions for improvement."
    )
    return prompt

def analyze_midi_with_music21(midi_path: Path) -> dict:
    """
    Analyze a MIDI file using music21 and return a dict of features.
    Features: tempo, note_density, key, mode, time_signature, etc.
    """
    from music21 import converter, tempo, meter, key
    score = converter.parse(str(midi_path))
    features = {}
    # Tempo
    tempos = [t.number for t in score.flat.getElementsByClass(tempo.MetronomeMark)]
    features['tempo'] = float(np.mean(tempos)) if tempos else None
    # Note density
    notes = list(score.flat.notes)
    duration = score.highestTime if score.highestTime > 0 else 1
    features['note_density'] = len(notes) / duration
    # Key and mode
    k = score.analyze('key')
    features['key'] = k.tonic.name if k else None
    features['mode'] = k.mode if k else None
    # Time signature
    ts = score.recurse().getElementsByClass(meter.TimeSignature)
    features['time_signature'] = ts[0].ratioString if ts else None
    return features

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python music_analysis.py <midi_file>")
    else:
        midi_path = Path(sys.argv[1])
        print(midi_to_symbolic_text(midi_path)) 