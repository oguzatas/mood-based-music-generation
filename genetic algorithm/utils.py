import pretty_midi

def extract_notes(midi_path):
    midi = pretty_midi.PrettyMIDI(midi_path)
    notes = []
    for instrument in midi.instruments:
        for note in instrument.notes:
            notes.append((note.pitch, note.end - note.start))
    return notes

def estimate_bpm(midi_path):
    midi = pretty_midi.PrettyMIDI(midi_path)
    tempos = midi.get_tempo_changes()[1]
    if len(tempos) > 0:
        return sum(tempos) / len(tempos)
    return 120  # default fallback
