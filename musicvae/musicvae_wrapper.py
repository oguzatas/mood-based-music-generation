import numpy as np
from pathlib import Path
from typing import Any
import subprocess
import logging

class MusicVAEWrapper:
    """Encapsulates music generation from a latent vector using Magenta Python API and converts to WAV."""
    def __init__(self, checkpoint_path: str = None, config_name: str = 'hierdec-trio_16bar', fluidsynth_path: str = None, soundfont_path: str = None):
        self.checkpoint_path = checkpoint_path or 'C:/Users/oguzh/magenta_musicgen/models/hierdec-trio_16bar/hierdec-trio_16bar.ckpt'
        self.config_name = config_name
        self.fluidsynth_path = fluidsynth_path or 'fluidsynth'
        self.soundfont_path = soundfont_path or 'soundfonts/FluidR3_GM.sf2'
        self.logger = logging.getLogger(__name__)
        # Import Magenta model and note_seq
        from magenta.models.music_vae.trained_model import TrainedModel
        from magenta.models.music_vae import configs
        import note_seq
        self.note_seq = note_seq
        config = configs.CONFIG_MAP[self.config_name]
        self.model = TrainedModel(
            config,
            batch_size=1,
            checkpoint_dir_or_path=self.checkpoint_path
        )

    def generate(self, latent_vector: np.ndarray, output_path: Path) -> Any:
        """
        Generate music from a latent vector and save to output_path (.mid and .wav).
        Uses the Magenta Python API to decode the latent vector, then FluidSynth to convert to WAV.
        """
        midi_path = output_path.with_suffix('.mid')
        wav_path = output_path.with_suffix('.wav')
        try:
            # Decode latent vector to NoteSequence
            sequences = self.model.decode([latent_vector], length=256, temperature=0.5)
            # Save as MIDI
            self.note_seq.sequence_proto_to_midi_file(sequences[0], str(midi_path))
            self.logger.info(f"Generated MIDI: {midi_path}")
        except Exception as e:
            self.logger.error(f"MusicVAE decoding failed: {e}")
            return {'output_path': None, 'error': str(e)}
        # Convert MIDI to WAV using FluidSynth
        fs_cmd = [
            self.fluidsynth_path,
            '-ni', str(self.soundfont_path),
            str(midi_path),
            '-F', str(wav_path),
            '-r', '44100',
            '-q'
        ]
        try:
            self.logger.info(f"GA: Converting MIDI to WAV with FluidSynth: {' '.join(map(str, fs_cmd))}")
            subprocess.run(fs_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
            self.logger.info(f"GA: FluidSynth conversion complete: {wav_path}")
        except subprocess.TimeoutExpired:
            self.logger.error("GA: FluidSynth conversion timed out!")
            return {'midi_path': str(midi_path), 'wav_path': None, 'error': 'FluidSynth timeout'}
        except subprocess.CalledProcessError as e:
            self.logger.error(f"GA: FluidSynth conversion failed: {e.stderr.decode() if e.stderr else e}")
            return {'midi_path': str(midi_path), 'wav_path': None, 'error': str(e)}
        return {'midi_path': str(midi_path), 'wav_path': str(wav_path)} 