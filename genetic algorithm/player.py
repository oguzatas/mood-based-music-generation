import fluidsynth
import os

soundfont_path = "soundfonts/FluidR3_GM.sf2"

def midi_to_wav(midi_path, wav_path):
    fs = fluidsynth.Synth()
    fs.start(driver="file", filename=wav_path)
    sfid = fs.sfload(soundfont_path)
    fs.program_select(0, sfid, 0, 0)
    fs.midi_player_add(midi_path)
    fs.midi_player_play()
    while fs.get_status() == fluidsynth.FLUID_PLAYER_PLAYING:
        pass
    fs.delete()
