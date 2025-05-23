"""
Music generation module using MusicVAE
"""
from typing import Dict, Set, Tuple
import os
import subprocess
import threading
import queue
import logging
from pathlib import Path
from typing import Optional, Callable, List

from config import AppConfig


class MusicVAEGenerator:
    """Handles MusicVAE music generation and MIDI to WAV conversion"""
    
    def __init__(self, config: AppConfig):
        self.config = config
        self.conversion_queue = queue.Queue()
        self.stop_event = threading.Event()
        self.current_process: Optional[subprocess.Popen] = None
        
        # Set up logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Ensure output directory exists
        self.config.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_music_vae(self, 
                         num_outputs: int, 
                         callback: Callable[[bool, Optional[str]], None],
                         log_callback: Callable[[str], None]) -> None:
        """Generate music asynchronously using MusicVAE"""
        
        def generation_worker():
            try:
                self._reset_stop_event()
                
                # Set up environment
                env = os.environ.copy()
                env["CUDA_VISIBLE_DEVICES"] = "0"
                
                # Build command
                command = self._build_generation_command(num_outputs)
                log_callback(f"Executing: {' '.join(command)}")
                
                # Start process
                self.current_process = subprocess.Popen(
                    command, 
                    env=env, 
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.STDOUT, 
                    text=True,
                    bufsize=1,
                    universal_newlines=True
                )
                
                # Stream output
                self._stream_process_output(log_callback)
                
                # Wait for completion and handle result
                self.current_process.wait()
                self._handle_generation_result(callback)
                    
            except Exception as e:
                self.logger.error(f"Generation failed: {e}")
                callback(False, str(e))
            finally:
                self.current_process = None
        
        threading.Thread(target=generation_worker, daemon=True).start()
    
    def _reset_stop_event(self) -> None:
        """Reset the stop event for new generation"""
        if self.stop_event.is_set():
            self.stop_event.clear()
    
    def _build_generation_command(self, num_outputs: int) -> List[str]:
        """Build the MusicVAE generation command"""
        return [
            "music_vae_generate",
            "--config=hierdec-trio_16bar",
            f"--checkpoint_file={self.config.checkpoint_path}",
            "--mode=sample",
            f"--num_outputs={num_outputs}",
            f"--output_dir={self.config.output_dir}"
        ]
    
    def _stream_process_output(self, log_callback: Callable[[str], None]) -> None:
        """Stream process output to log callback"""
        if not self.current_process or not self.current_process.stdout:
            return
            
        for line in self.current_process.stdout:
            if self.stop_event.is_set():
                break
            log_callback(line.strip())
    
    def _handle_generation_result(self, callback: Callable[[bool, Optional[str]], None]) -> None:
        """Handle the result of the generation process"""
        if self.stop_event.is_set():
            callback(False, "Generation cancelled")
        elif self.current_process and self.current_process.returncode != 0:
            callback(False, f"Generation failed with return code {self.current_process.returncode}")
        else:
            callback(True, None)
    
    def stop_generation(self) -> None:
        """Stop the current generation process"""
        if self.current_process:
            self.stop_event.set()
            try:
                self.current_process.terminate()
                # Give it a moment to terminate gracefully
                self.current_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                # Force kill if it doesn't terminate
                self.current_process.kill()
            except Exception as e:
                self.logger.error(f"Error stopping generation: {e}")
    
    def convert_midi_to_wav(self, midi_path: Path, wav_path: Path) -> bool:
        """Convert a single MIDI file to WAV using FluidSynth"""
        try:
            command = [
                str(self.config.fluidsynth_path),
                "-ni", str(self.config.soundfont_path),
                str(midi_path),
                "-F", str(wav_path),
                "-r", "44100",
                "-q"
            ]
            
            result = subprocess.run(
                command, 
                check=True, 
                stdout=subprocess.DEVNULL, 
                stderr=subprocess.PIPE,
                text=True
            )
            
            self.logger.info(f"Successfully converted {midi_path.name} to WAV")
            return True
            
        except subprocess.CalledProcessError as e:
            error_msg = f"Failed to convert {midi_path.name}: {e}"
            if e.stderr:
                error_msg += f" - {e.stderr}"
            self.logger.error(error_msg)
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error converting {midi_path.name}: {e}")
            return False
    
    def start_conversion_worker(self, 
                             progress_callback: Callable[[int, int], None],
                             completion_callback: Callable[[List[Path]], None]) -> None:
        """Start a background worker for MIDI to WAV conversion"""
        
        def conversion_worker():
            converted_files = []
            midi_files = list(self.config.output_dir.glob("*.mid"))
            total = len(midi_files)
            
            if total == 0:
                self.logger.warning("No MIDI files found for conversion")
                completion_callback([])
                return
            
            self.logger.info(f"Starting conversion of {total} MIDI files")
            
            for idx, midi_file in enumerate(midi_files, 1):
                if self.stop_event.is_set():
                    self.logger.info("Conversion cancelled")
                    break
                    
                wav_file = midi_file.with_suffix(".wav")
                progress_callback(idx, total)
                
                # Skip if WAV already exists
                if wav_file.exists():
                    self.logger.info(f"WAV file already exists: {wav_file.name}")
                    converted_files.append(wav_file)
                    continue
                
                # Convert MIDI to WAV
                if self.convert_midi_to_wav(midi_file, wav_file):
                    converted_files.append(wav_file)
            
            if not self.stop_event.is_set():
                self.logger.info(f"Conversion completed. {len(converted_files)} files converted")
                completion_callback(converted_files)
        
        threading.Thread(target=conversion_worker, daemon=True).start()
    
    def get_generated_files(self) -> Tuple[List[Path], List[Path]]:
        """Get lists of generated MIDI and WAV files"""
        midi_files = sorted(self.config.output_dir.glob("*.mid"))
        wav_files = sorted(self.config.output_dir.glob("*.wav"))
        return midi_files, wav_files
    
    def cleanup(self) -> None:
        """Clean up resources and stop any running processes"""
        self.stop_generation()
        if self.current_process:
            try:
                self.current_process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.current_process.kill()