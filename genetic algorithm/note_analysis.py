# note_analysis.py
def analyze_sequence(seq):
    pitches = [n.pitch for n in seq.notes]
    total_duration = sum([n.end_time - n.start_time for n in seq.notes])
    unique_pitches = len(set(pitches))
    intervals = [abs(pitches[i+1] - pitches[i]) for i in range(len(pitches)-1)]

    return {
        "note_count": len(seq.notes),
        "unique_pitches": unique_pitches,
        "avg_interval": sum(intervals)/len(intervals) if intervals else 0,
        "duration": total_duration,
    }

def fitness(seq, target_bpm):
    qpm = seq.tempos[0].qpm if seq.tempos else 120
    bpm_score = 1 - abs(qpm - target_bpm) / max(target_bpm, 1)
    features = analyze_sequence(seq)
    return bpm_score + features["unique_pitches"] * 0.1
