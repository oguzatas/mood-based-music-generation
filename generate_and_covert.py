import os
import subprocess
import threading
import queue
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, ttk
import pygame
import time
from datetime import datetime
import configparser
import gettext
import logging
from typing import Optional, Callable, List, Dict

# === Configuration Setup ===
class AppConfig:
    def __init__(self):
        self.config = configparser.ConfigParser()
        self.config_file = Path("config.ini")
        self.load_config()
        
    def load_config(self):
        default_config = {
            'PATHS': {
                'music_vae_path': "C:/Users/oguzh/magenta_musicgen",
                'fluidsynth_path': "C:/tools/fluidsynth/bin/fluidsynth.exe",
            },
            'SETTINGS': {
                'default_outputs': "3",
                'volume': "70",
                'language': "en"
            }
        }
        
        if not self.config_file.exists():
            self.config.read_dict(default_config)
            self.save_config()
        else:
            self.config.read(self.config_file)
            # Ensure all required sections/keys exist
            for section, options in default_config.items():
                if not self.config.has_section(section):
                    self.config.add_section(section)
                for key, value in options.items():
                    if not self.config.has_option(section, key):
                        self.config.set(section, key, value)
            self.save_config()
    
    def save_config(self):
        with open(self.config_file, 'w') as f:
            self.config.write(f)
    
    @property
    def music_vae_path(self) -> Path:
        return Path(self.config.get('PATHS', 'music_vae_path'))
    
    @property
    def checkpoint_path(self) -> Path:
        return self.music_vae_path / "models/hierdec-trio_16bar.tar"
    
    @property
    def output_dir(self) -> Path:
        return self.music_vae_path / "musicvae/generated"
    
    @property
    def soundfont_path(self) -> Path:
        return self.music_vae_path / "soundfonts/FluidR3_GM.sf2"
    
    @property
    def fluidsynth_path(self) -> Path:
        return Path(self.config.get('PATHS', 'fluidsynth_path'))
    
    @property
    def default_outputs(self) -> int:
        return int(self.config.get('SETTINGS', 'default_outputs'))
    
    @property
    def default_volume(self) -> int:
        return int(self.config.get('SETTINGS', 'volume'))
    
    def validate_paths(self) -> bool:
        paths = [
            self.music_vae_path,
            self.checkpoint_path,
            self.soundfont_path,
            self.fluidsynth_path
        ]
        return all(p.exists() for p in paths)

# === Music Generation Core ===
class MusicVAEGenerator:
    def __init__(self, config: AppConfig):
        self.config = config
        self.conversion_queue = queue.Queue()
        self.stop_event = threading.Event()
        self.current_process: Optional[subprocess.Popen] = None
        
    def generate_music_vae(self, num_outputs: int, 
                         callback: Callable[[bool, Optional[str]], None],
                         log_callback: Callable[[str], None]) -> None:
        """Generate music asynchronously using MusicVAE"""
        def run():
            try:
                env = os.environ.copy()
                env["CUDA_VISIBLE_DEVICES"] = "0"
                
                command = [
                    "music_vae_generate",
                    "--config=hierdec-trio_16bar",
                    f"--checkpoint_file={self.config.checkpoint_path}",
                    "--mode=sample",
                    f"--num_outputs={num_outputs}",
                    f"--output_dir={self.config.output_dir}"
                ]
                
                self.current_process = subprocess.Popen(
                    command, 
                    env=env, 
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.STDOUT, 
                    text=True,
                    bufsize=1,
                    universal_newlines=True
                )
                
                for line in self.current_process.stdout:
                    if self.stop_event.is_set():
                        break
                    log_callback(line.strip())
                
                self.current_process.wait()
                if self.stop_event.is_set():
                    callback(False, "Generation cancelled")
                elif self.current_process.returncode != 0:
                    raise subprocess.CalledProcessError(
                        self.current_process.returncode, command)
                else:
                    callback(True, None)
                    
            except Exception as e:
                callback(False, str(e))
            finally:
                self.current_process = None
        
        threading.Thread(target=run, daemon=True).start()
    
    def stop_generation(self):
        """Stop the current generation process"""
        if self.current_process:
            self.stop_event.set()
            self.current_process.terminate()
    
    def convert_midi_to_wav(self, midi_path: Path, wav_path: Path) -> bool:
        """Convert a single MIDI file to WAV"""
        try:
            subprocess.run([
                str(self.config.fluidsynth_path),
                "-ni", str(self.config.soundfont_path),
                str(midi_path),
                "-F", str(wav_path),
                "-r", "44100",
                "-q"
            ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to convert {midi_path}: {e}")
            return False
    
    def start_conversion_worker(self, 
                             progress_callback: Callable[[int, int], None],
                             completion_callback: Callable[[List[Path]], None]):
        """Start a background worker for MIDI to WAV conversion"""
        def worker():
            converted_files = []
            midi_files = list(self.config.output_dir.glob("*.mid"))
            total = len(midi_files)
            
            for idx, midi_file in enumerate(midi_files, 1):
                if self.stop_event.is_set():
                    break
                    
                wav_file = midi_file.with_suffix(".wav")
                if not wav_file.exists():
                    progress_callback(idx, total)
                    if self.convert_midi_to_wav(midi_file, wav_file):
                        converted_files.append(wav_file)
            
            if not self.stop_event.is_set():
                completion_callback(converted_files)
        
        threading.Thread(target=worker, daemon=True).start()

# === GUI Application ===
class MusicGeneratorApp:
    def __init__(self, root):
        self.root = root
        self.config = AppConfig()
        self.generator = MusicVAEGenerator(self.config)
        
        # Initialize localization
        self.setup_localization()
        
        # Initialize pygame mixer
        pygame.mixer.init()
        self.current_volume = self.config.default_volume / 100
        pygame.mixer.music.set_volume(self.current_volume)
        
        # Setup UI
        self.setup_ui()
        
        # Validate paths
        if not self.config.validate_paths():
            messagebox.showerror(
                _("Configuration Error"),
                _("One or more required paths are invalid. Please check config.ini")
            )
    
    def setup_localization(self):
        """Initialize internationalization"""
        try:
            locale_dir = Path(__file__).parent / "locales"
            lang = gettext.translation(
                'musicvae', 
                localedir=locale_dir, 
                languages=[self.config.language]
            )
            lang.install()
            global _
            _ = lang.gettext
        except:
            # Fallback if translation files aren't found
            def _(text): return text
    
    def setup_ui(self):
        """Initialize all UI components"""
        self.root.title(_("🎵 MusicVAE Generator (GPU) 🎵"))
        
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Settings Frame
        settings_frame = ttk.LabelFrame(main_frame, text=_("Settings"), padding="10")
        settings_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(settings_frame, text=_("Number of outputs:")).grid(row=0, column=0, sticky="w")
        self.num_outputs_var = tk.IntVar(value=self.config.default_outputs)
        outputs_entry = ttk.Entry(settings_frame, textvariable=self.num_outputs_var, width=5)
        outputs_entry.grid(row=0, column=1, sticky="w", padx=5)
        self.create_tooltip(outputs_entry, _("How many music pieces to generate at once"))
        
        # Volume control
        ttk.Label(settings_frame, text=_("Volume:")).grid(row=1, column=0, sticky="w")
        self.volume_slider = ttk.Scale(
            settings_frame, 
            from_=0, 
            to=100, 
            orient=tk.HORIZONTAL,
            command=lambda v: self.set_volume(round(float(v))),
        )
        self.volume_slider.set(self.config.default_volume)
        self.volume_slider.grid(row=1, column=1, sticky="ew", padx=5)
        
        # Control Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=5)
        
        self.generate_button = ttk.Button(
            button_frame, 
            text=_("Generate"), 
            command=self.on_generate_clicked
        )
        self.generate_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = ttk.Button(
            button_frame,
            text=_("Stop"),
            command=self.on_stop_clicked,
            state=tk.DISABLED
        )
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        # Progress Bar
        self.progress_bar = ttk.Progressbar(
            main_frame, 
            mode='determinate',
            maximum=100
        )
        self.progress_bar.pack(fill=tk.X, pady=5)
        
        # Status Label
        self.status_var = tk.StringVar(value=_("Ready"))
        ttk.Label(
            main_frame, 
            textvariable=self.status_var,
            relief=tk.SUNKEN,
            anchor=tk.W,
            padding=3
        ).pack(fill=tk.X, pady=5)
        
        # File List
        list_frame = ttk.LabelFrame(main_frame, text=_("Generated Files"), padding="10")
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.file_listbox = tk.Listbox(
            list_frame, 
            width=60,
            selectmode=tk.SINGLE
        )
        self.file_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.file_listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.file_listbox.yview)
        
        # Playback Controls
        playback_frame = ttk.Frame(main_frame)
        playback_frame.pack(fill=tk.X, pady=5)
        
        self.play_button = ttk.Button(
            playback_frame,
            text=_("Play"),
            command=self.play_selected,
            state=tk.DISABLED
        )
        self.play_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_playback_button = ttk.Button(
            playback_frame,
            text=_("Stop Playback"),
            command=self.stop_playback,
            state=tk.DISABLED
        )
        self.stop_playback_button.pack(side=tk.LEFT, padx=5)
        
        # Log Area
        log_frame = ttk.LabelFrame(main_frame, text=_("Log"), padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.log_text = tk.Text(
            log_frame, 
            height=10, 
            width=70, 
            state='disabled', 
            bg="#f0f0f0",
            wrap=tk.WORD
        )
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        log_scroll = ttk.Scrollbar(log_frame, orient=tk.VERTICAL)
        log_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=log_scroll.set)
        log_scroll.config(command=self.log_text.yview)
        
        # Initialize file list
        self.refresh_list()
        
        # Set up keyboard shortcuts
        self.root.bind('<Escape>', lambda e: self.stop_playback())
        self.root.bind('<Control-q>', lambda e: self.root.quit())
        
        # Ensure output directory exists
        self.config.output_dir.mkdir(parents=True, exist_ok=True)
    
    def create_tooltip(self, widget, text):
        """Create a tooltip for a widget"""
        tooltip = ttk.Label(self.root, text=text, background="#ffffe0", 
                          relief="solid", borderwidth=1)
        
        def enter(event):
            x = widget.winfo_rootx() + widget.winfo_width()
            y = widget.winfo_rooty()
            tooltip.place(x=x, y=y)
        
        def leave(event):
            tooltip.place_forget()
        
        widget.bind('<Enter>', enter)
        widget.bind('<Leave>', leave)
    
        def set_volume(self, val):
    
            try:
                # Convert the string value to float first, then round it
                volume = round(float(val))
                self.current_volume = volume / 100
                pygame.mixer.music.set_volume(self.current_volume)
                # Save as string to avoid decimal places
                self.config.config.set('SETTINGS', 'volume', str(volume))
                self.config.save_config()
            except ValueError as e:
                self.log_message(f"Volume setting error: {e}")
    
    def on_generate_clicked(self):
        """Handle generate button click"""
        num_outputs = self.num_outputs_var.get()
        if num_outputs < 1 or num_outputs > 10:
            messagebox.showerror(
                _("Invalid Input"),
                _("Please enter a number between 1 and 10")
            )
            return
        
        self.set_ui_state(generating=True)
        self.progress_bar['value'] = 0
        self.status_var.set(_("Generating music..."))
        self.log_clear()
        self.log_message(_("Starting generation..."))
        
        self.generator.generate_music_vae(
            num_outputs,
            self.on_generation_finished,
            self.log_message
        )
    
    def on_stop_clicked(self):
        """Handle stop button click"""
        self.generator.stop_generation()
        self.status_var.set(_("Stopping..."))
    
    def on_generation_finished(self, success: bool, error: Optional[str]):
        """Callback when generation completes"""
        if success:
            self.status_var.set(_("Conversion started..."))
            self.log_message(_("Generation complete. Starting conversion..."))
            
            def progress_callback(current, total):
                percent = (current / total) * 100
                self.progress_bar['value'] = percent
                self.status_var.set(
                    _("Converting {current}/{total}...").format(
                        current=current, total=total
                    )
                )
            
            def completion_callback(converted_files):
                if converted_files:
                    self.status_var.set(
                        _("Done! Generated {count} files").format(
                            count=len(converted_files)
                        )
                    )
                    self.log_message(_("Conversion completed successfully"))
                else:
                    self.status_var.set(_("No files were converted"))
                self.refresh_list()
                self.set_ui_state(generating=False)
            
            self.generator.start_conversion_worker(
                progress_callback,
                completion_callback
            )
        else:
            messagebox.showerror(_("Generation Error"), error)
            self.set_ui_state(generating=False)
            self.status_var.set(_("Generation failed"))
    
    def play_selected(self):
        """Play the selected audio file"""
        selection = self.file_listbox.curselection()
        if not selection:
            messagebox.showwarning(_("Warning"), _("Please select a file first"))
            return
        
        filename = self.file_listbox.get(selection[0])
        filepath = self.config.output_dir / filename
        
        try:
            if pygame.mixer.music.get_busy():
                pygame.mixer.music.stop()
            
            pygame.mixer.music.load(str(filepath))
            pygame.mixer.music.play()
            self.status_var.set(_("Playing: {filename}").format(filename=filename))
            self.play_button.config(state=tk.DISABLED)
            self.stop_playback_button.config(state=tk.NORMAL)
            
            # Set up end of playback detection
            self.check_playback_status()
            
        except pygame.error as e:
            messagebox.showerror(_("Playback Error"), str(e))
    
    def check_playback_status(self):
        """Check if playback has finished"""
        if pygame.mixer.music.get_busy():
            self.root.after(100, self.check_playback_status)
        else:
            self.stop_playback_button.config(state=tk.DISABLED)
            self.play_button.config(state=tk.NORMAL)
            self.status_var.set(_("Playback finished"))
    
    def stop_playback(self):
        """Stop current playback"""
        pygame.mixer.music.stop()
        self.stop_playback_button.config(state=tk.DISABLED)
        self.play_button.config(state=tk.NORMAL)
        self.status_var.set(_("Playback stopped"))
    
    def refresh_list(self):
        """Refresh the file listbox"""
        self.file_listbox.delete(0, tk.END)
        wav_files = sorted(self.config.output_dir.glob("*.wav"))
        
        if not wav_files:
            self.file_listbox.insert(tk.END, _("No generated files found"))
            self.play_button.config(state=tk.DISABLED)
        else:
            for f in wav_files:
                self.file_listbox.insert(tk.END, f.name)
            self.play_button.config(state=tk.NORMAL)
    
    def set_ui_state(self, generating: bool):
        """Enable/disable UI elements based on state"""
        state = tk.DISABLED if generating else tk.NORMAL
        self.generate_button.config(state=state)
        self.stop_button.config(state=tk.DISABLED if not generating else tk.NORMAL)
        self.num_outputs_var.set(self.config.default_outputs)
        self.root.config(cursor="watch" if generating else "")
        self.root.update()
    
    def log_message(self, message: str):
        """Add a message to the log with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        full_message = f"[{timestamp}] {message}"
        
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, full_message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
    
    def log_clear(self):
        """Clear the log"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)
    
    def cleanup(self):
        """Clean up resources"""
        pygame.mixer.quit()
        pygame.quit()

if __name__ == "__main__":
    root = tk.Tk()
    app = MusicGeneratorApp(root)
    
    try:
        root.mainloop()
    finally:
        app.cleanup()