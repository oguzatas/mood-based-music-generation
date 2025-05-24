"""
Main application class for MusicVAE Generator
"""
from typing import Dict, Set, Tuple
import tkinter as tk
from tkinter import messagebox, ttk
import logging
from pathlib import Path
from typing import Optional, List
import glob
import os

from config import AppConfig
from music_generator import MusicVAEGenerator
from audio_player import AudioPlayer, PlaybackState
from localization import init_localization, _
from ui_components import (
    LogTextWidget, FileListWidget, ProgressFrame, 
    SettingsFrame, PlaybackControlsFrame
)


class MusicGeneratorApp:
    """Main application class for the MusicVAE Generator"""
    
    def __init__(self, root: tk.Tk):
        self.root = root
        
        # Initialize configuration
        self.config = AppConfig()
        
        # Initialize localization
        init_localization(self.config.language)
        
        # Initialize core components
        self.generator = MusicVAEGenerator(self.config)
        self.audio_player = AudioPlayer(self.config.default_volume / 100)
        
        # Set up logging
        self.setup_logging()
        
        # Initialize UI
        self.setup_ui()
        
        # Set up audio player callbacks
        self.setup_audio_callbacks()
        
        # Validate configuration
        self.validate_configuration()
        
        # Set up keyboard shortcuts
        self.setup_keyboard_shortcuts()
        
        # Initialize file list
        self.refresh_file_list()
    
    def setup_logging(self) -> None:
        """Set up application logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def setup_ui(self) -> None:
        """Initialize the user interface"""
        self.root.title(_("🎵 MusicVAE Generator (GPU) 🎵"))
        self.root.geometry("800x900")
        self.root.minsize(600, 700)
        
        # Main container with padding
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Settings section
        self.settings_frame = SettingsFrame(main_frame)
        self.settings_frame.pack(fill=tk.X, pady=(0, 10))
        self.settings_frame.set_num_outputs(self.config.default_outputs)
        self.settings_frame.set_volume(self.config.default_volume / 100)
        
        # Control buttons section
        self.setup_control_buttons(main_frame)
        
        # Progress section
        self.progress_frame = ProgressFrame(main_frame)
        self.progress_frame.pack(fill=tk.X, pady=(0, 10))
        
        # File list section
        self.file_list_widget = FileListWidget(main_frame, _("Generated Files"))
        self.file_list_widget.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        self.file_list_widget.set_selection_callback(self.on_file_selected)
        
        # Playback controls section
        self.playback_controls = PlaybackControlsFrame(main_frame)
        self.playback_controls.pack(fill=tk.X, pady=(0, 10))
        self.playback_controls.set_play_callback(self.play_selected_file)
        self.playback_controls.set_stop_callback(self.stop_playback)
        
        # Log section
        self.setup_log_section(main_frame)
    
    def setup_control_buttons(self, parent: tk.Widget) -> None:
        """Set up the main control buttons"""
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.generate_button = ttk.Button(
            button_frame,
            text=_("Generate Music"),
            command=self.start_generation
        )
        self.generate_button.pack(side=tk.LEFT, padx=(0, 5))
        
        # Add GA generate button
        self.ga_generate_button = ttk.Button(
            button_frame,
            text=_("Generate with GA"),
            command=self.start_ga_generation
        )
        self.ga_generate_button.pack(side=tk.LEFT, padx=(0, 5))
        
        self.stop_generation_button = ttk.Button(
            button_frame,
            text=_("Stop Generation"),
            command=self.stop_generation,
            state=tk.DISABLED
        )
        self.stop_generation_button.pack(side=tk.LEFT, padx=(0, 5))
        
        self.refresh_button = ttk.Button(
            button_frame,
            text=_("Refresh Files"),
            command=self.refresh_file_list
        )
        self.refresh_button.pack(side=tk.RIGHT)
    
    def setup_log_section(self, parent: tk.Widget) -> None:
        """Set up the log section"""
        log_frame = ttk.LabelFrame(parent, text=_("Activity Log"), padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create log widget
        self.log_widget = LogTextWidget(log_frame)
        self.log_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.log_widget.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Log controls
        log_controls = ttk.Frame(log_frame)
        log_controls.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Button(
            log_controls,
            text=_("Clear Log"),
            command=self.log_widget.clear_log
        ).pack(side=tk.LEFT)
        
        ttk.Button(
            log_controls,
            text=_("Save Log"),
            command=self.save_log
        ).pack(side=tk.LEFT, padx=(5, 0))
    
    def setup_audio_callbacks(self) -> None:
        """Set up audio player callbacks"""
        def on_playback_state_change(state: PlaybackState):
            is_playing = state == PlaybackState.PLAYING
            self.playback_controls.set_playback_state(is_playing)
            
            if state == PlaybackState.PLAYING:
                current_file = self.audio_player.get_current_file()
                if current_file:
                    self.progress_frame.set_status(
                        _("Playing: {filename}").format(filename=current_file.name)
                    )
            elif state == PlaybackState.STOPPED:
                self.progress_frame.set_status(_("Playback stopped"))
        
        self.audio_player.add_playback_callback(on_playback_state_change)
        
        # Set up volume change callback
        def on_volume_change(*args):
            volume = self.settings_frame.get_volume()
            self.audio_player.set_volume(volume)
            # Save volume to config
            self.config.set_value('SETTINGS', 'volume', str(int(volume * 100)))
        
        self.settings_frame.volume_var.trace('w', on_volume_change)
    
    def setup_keyboard_shortcuts(self) -> None:
        """Set up keyboard shortcuts"""
        self.root.bind('<Escape>', lambda e: self.stop_playback())
        self.root.bind('<Control-q>', lambda e: self.quit_application())
        self.root.bind('<F5>', lambda e: self.refresh_file_list())
        self.root.bind('<Control-g>', lambda e: self.start_generation())
        self.root.bind('<space>', lambda e: self.toggle_playback())
    
    def validate_configuration(self) -> None:
        """Validate application configuration"""
        if not self.config.validate_paths():
            missing_paths = self.config.get_missing_paths()
            error_msg = _("Configuration Error: Missing paths:\n") + \
                       "\n".join(str(p) for p in missing_paths) + \
                       _("\n\nPlease check config.ini file.")
            
            messagebox.showerror(_("Configuration Error"), error_msg)
            self.log_widget.log_message(error_msg, "ERROR")
        else:
            self.log_widget.log_message(_("Configuration validated successfully"), "SUCCESS")
    
    def start_generation(self) -> None:
        """Start music generation process"""
        num_outputs = self.settings_frame.get_num_outputs()
        
        # Validate input
        if not (1 <= num_outputs <= 10):
            messagebox.showerror(
                _("Invalid Input"),
                _("Number of outputs must be between 1 and 10")
            )
            return
        
        # Clean output directory before generation
        for ext in ("*.mid", "*.wav"):
            for f in self.config.output_dir.glob(ext):
                try:
                    f.unlink()
                except Exception as e:
                    self.log_widget.log_message(f"Failed to delete {f}: {e}", "WARNING")
        
        # Update UI state
        self.set_generation_state(True)
        self.progress_frame.reset()
        self.progress_frame.set_status(_("Starting generation..."))
        self.log_widget.clear_log()
        self.log_widget.log_message(_("Starting music generation..."))
        
        # Start generation
        self.generator.generate_music_vae(
            num_outputs,
            self.on_generation_finished,
            self.on_generation_log
        )
    
    def stop_generation(self) -> None:
        """Stop current generation process"""
        self.generator.stop_generation()
        self.progress_frame.set_status(_("Stopping generation..."))
        self.log_widget.log_message(_("Generation stop requested"), "WARNING")
    
    def on_generation_finished(self, success: bool, error: Optional[str]) -> None:
        """Callback when generation finishes"""
        def update_ui():
            if success:
                self.progress_frame.set_status(_("Generation complete. Starting conversion..."))
                self.log_widget.log_message(_("Music generation completed successfully"), "SUCCESS")
                self.start_conversion()
            else:
                error_msg = error or _("Unknown error occurred")
                self.progress_frame.set_status(_("Generation failed"))
                self.log_widget.log_message(f"Generation failed: {error_msg}", "ERROR")
                messagebox.showerror(_("Generation Error"), error_msg)
                self.set_generation_state(False)
        self.root.after(0, update_ui)
    
    def on_generation_log(self, message: str) -> None:
        """Callback for generation log messages"""
        self.root.after(0, lambda: self.log_widget.log_message(message))
    
    def start_conversion(self) -> None:
        """Start MIDI to WAV conversion process"""
        def on_progress(current: int, total: int):
            def update_progress():
                progress = (current / total) * 100 if total > 0 else 0
                self.progress_frame.set_progress(progress)
                self.progress_frame.set_status(
                    _(f"Converting {current}/{total}...")
                )
            self.root.after(0, update_progress)
        
        def on_completion(converted_files: List[Path]):
            def update_completion():
                count = len(converted_files)
                if count > 0:
                    self.progress_frame.set_status(
                        _(f"Conversion complete! {count} files ready")
                    )
                    self.log_widget.log_message(
                        f"Successfully converted {count} files to WAV format", "SUCCESS"
                    )
                else:
                    self.progress_frame.set_status(_("No files were converted"))
                    self.log_widget.log_message("No MIDI files found for conversion", "WARNING")
                self.refresh_file_list()
                self.set_generation_state(False)
            self.root.after(0, update_completion)
        self.generator.start_conversion_worker(on_progress, on_completion)
    
    def refresh_file_list(self) -> None:
        """Refresh the list of generated files"""
        _, wav_files = self.generator.get_generated_files()
        self.file_list_widget.update_files(wav_files)
        
        # Update playback controls
        has_files = len(wav_files) > 0
        self.playback_controls.enable_play(has_files)
        
        count = len(wav_files)
        self.log_widget.log_message(f"Found {count} WAV files in output directory")
    
    def on_file_selected(self, file_path: Optional[Path]) -> None:
        """Handle file selection in the file list"""
        has_selection = file_path is not None
        self.playback_controls.enable_play(has_selection and not self.audio_player.is_playing())
    
    def play_selected_file(self) -> None:
        """Play the selected audio file"""
        selected_file = self.file_list_widget.get_selected_file()
        
        if not selected_file:
            messagebox.showwarning(_("No Selection"), _("Please select a file to play"))
            return
        
        if not selected_file.exists():
            messagebox.showerror(_("File Error"), _("Selected file does not exist"))
            self.refresh_file_list()
            return
        
        if self.audio_player.play_file(selected_file):
            self.log_widget.log_message(f"Started playing: {selected_file.name}")
        else:
            messagebox.showerror(_("Playback Error"), _("Failed to play the selected file"))
    
    def stop_playback(self) -> None:
        """Stop current audio playback"""
        self.audio_player.stop()
        self.log_widget.log_message("Playback stopped")
    
    def toggle_playback(self) -> None:
        """Toggle playback (play/stop)"""
        if self.audio_player.is_playing():
            self.stop_playback()
        else:
            self.play_selected_file()
    
    def set_generation_state(self, generating: bool) -> None:
        """Update UI state based on generation status"""
        # Update button states
        self.generate_button.config(state=tk.DISABLED if generating else tk.NORMAL)
        self.stop_generation_button.config(state=tk.NORMAL if generating else tk.DISABLED)
        self.refresh_button.config(state=tk.DISABLED if generating else tk.NORMAL)
        
        # Update cursor
        cursor = "watch" if generating else ""
        self.root.config(cursor=cursor)
        
        # Update progress bar
        if not generating:
            self.progress_frame.set_progress(0)
        
        self.root.update()
    
    def save_log(self) -> None:
        """Save log contents to file"""
        from tkinter import filedialog
        
        file_path = filedialog.asksaveasfilename(
            title=_("Save Log File"),
            defaultextension=".txt",
            filetypes=[(_("Text files"), "*.txt"), (_("All files"), "*.*")]
        )
        
        if file_path:
            if self.log_widget.save_log(Path(file_path)):
                messagebox.showinfo(_("Success"), _("Log saved successfully"))
            else:
                messagebox.showerror(_("Error"), _("Failed to save log file"))
    
    def quit_application(self) -> None:
        """Clean up and quit the application"""
        try:
            self.cleanup()
            self.root.quit()
        except Exception as e:
            self.logger.error(f"Error during application quit: {e}")
            self.root.quit()
    
    def cleanup(self) -> None:
        """Clean up application resources"""
        try:
            self.log_widget.log_message("Shutting down application...")
            
            # Stop any ongoing processes
            self.generator.stop_generation()
            self.audio_player.stop()
            
            # Clean up components
            self.generator.cleanup()
            self.audio_player.cleanup()
            
            self.log_widget.log_message("Cleanup completed", "SUCCESS")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
    
    def start_ga_generation(self) -> None:
        """Start music generation using a genetic algorithm"""
        from genetic_algorithm import MusicGeneticAlgorithm
        from musicvae_wrapper import MusicVAEWrapper
        import threading

        # Get GA parameters from UI
        population_size = self.settings_frame.get_population_size()
        generations = self.settings_frame.get_generations()
        latent_dim = self.settings_frame.get_latent_dim()
        output_dir = self.config.output_dir
        output_dir.mkdir(exist_ok=True)

        # Clean output directory before generation
        for ext in ("*.mid", "*.wav", "*.txt"):
            for f in output_dir.glob(ext):
                try:
                    f.unlink()
                except Exception as e:
                    self.log_widget.log_message(f"Failed to delete {f}: {e}", "WARNING")

        def ga_worker():
            self.log_widget.log_message("Starting Genetic Algorithm music generation...")
            music_generator = MusicVAEWrapper()
            ga = MusicGeneticAlgorithm(population_size, latent_dim, music_generator, output_dir)
            for gen in range(generations):
                ga.generation = gen
                self.root.after(0, lambda g=gen: self.log_widget.log_message(f"GA Generation {g+1}/{generations}"))
                ga.evaluate(ga.fitness_fn)
                best = max(ga.population, key=lambda ind: ind.fitness)
                self.root.after(0, lambda b=best: self.log_widget.log_message(f"  Best fitness: {b.fitness:.4f}"))
                selected = ga.select()
                ga.reproduce(selected)
            self.root.after(0, lambda: self.log_widget.log_message("GA music generation complete."))
            self.root.after(0, self.refresh_file_list)
            self.root.after(0, lambda: self.set_generation_state(False))

        self.set_generation_state(True)
        threading.Thread(target=ga_worker, daemon=True).start()


def main():
    """Main entry point for the application"""
    try:
        root = tk.Tk()
        app = MusicGeneratorApp(root)
        
        # Set up proper cleanup on window close
        def on_closing():
            app.quit_application()
        
        root.protocol("WM_DELETE_WINDOW", on_closing)
        
        # Start the application
        root.mainloop()
        
    except Exception as e:
        logging.error(f"Fatal error in main application: {e}")
        if 'root' in locals():
            try:
                messagebox.showerror("Fatal Error", f"Application error: {e}")
            except:
                pass
        raise


if __name__ == "__main__":
    main()