"""
Reusable UI components for the MusicVAE Generator application
"""
from typing import Dict, Set, Tuple
import tkinter as tk
from tkinter import ttk
from pathlib import Path
from typing import Callable, Optional, List
from datetime import datetime

from localization import _


class TooltipMixin:
    """Mixin class to add tooltip functionality to widgets"""
    
    def create_tooltip(self, widget: tk.Widget, text: str) -> None:
        """Create a tooltip for a widget"""
        tooltip = ttk.Label(
            widget.winfo_toplevel(), 
            text=text, 
            background="#ffffe0", 
            relief="solid", 
            borderwidth=1,
            font=("TkDefaultFont", "8", "normal")
        )
        
        def show_tooltip(event):
            x = widget.winfo_rootx() + widget.winfo_width() + 5
            y = widget.winfo_rooty()
            tooltip.place(x=x, y=y)
        
        def hide_tooltip(event):
            tooltip.place_forget()
        
        widget.bind('<Enter>', show_tooltip)
        widget.bind('<Leave>', hide_tooltip)


class LogTextWidget(tk.Text):
    """Enhanced text widget for logging with automatic scrolling and timestamping"""
    
    def __init__(self, parent, **kwargs):
        # Set default values
        default_kwargs = {
            'state': 'disabled',
            'bg': "#f8f8f8",
            'wrap': tk.WORD,
            'height': 10,
            'width': 70,
            'font': ('Consolas', 9)
        }
        default_kwargs.update(kwargs)
        
        super().__init__(parent, **default_kwargs)
        
        # Add scrollbar
        self.scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=self.yview)
        self.config(yscrollcommand=self.scrollbar.set)
        
        # Configure tags for different log levels
        self.tag_configure("INFO", foreground="black")
        self.tag_configure("WARNING", foreground="orange")
        self.tag_configure("ERROR", foreground="red")
        self.tag_configure("SUCCESS", foreground="green")
        
        self.max_lines = 1000  # Maximum number of lines to keep
    
    def log_message(self, message: str, level: str = "INFO") -> None:
        """Add a timestamped message to the log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        full_message = f"[{timestamp}] {message}\n"
        
        self.config(state=tk.NORMAL)
        self.insert(tk.END, full_message, level)
        self._trim_log()
        self.see(tk.END)
        self.config(state=tk.DISABLED)
    
    def _trim_log(self) -> None:
        """Trim log to maximum number of lines"""
        lines = int(self.index('end-1c').split('.')[0])
        if lines > self.max_lines:
            lines_to_delete = lines - self.max_lines
            self.delete(1.0, f"{lines_to_delete}.0")
    
    def clear_log(self) -> None:
        """Clear all log messages"""
        self.config(state=tk.NORMAL)
        self.delete(1.0, tk.END)
        self.config(state=tk.DISABLED)
    
    def save_log(self, file_path: Path) -> bool:
        """Save log contents to file"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(self.get(1.0, tk.END))
            return True
        except Exception:
            return False


class FileListWidget(tk.Frame):
    """Widget for displaying and managing a list of files"""
    
    def __init__(self, parent, title: str = "Files", **kwargs):
        super().__init__(parent, **kwargs)
        
        # Create label frame
        self.label_frame = ttk.LabelFrame(self, text=title, padding="10")
        self.label_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create listbox with scrollbar
        self.listbox = tk.Listbox(
            self.label_frame,
            selectmode=tk.SINGLE,
            width=60,
            height=8
        )
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.scrollbar = ttk.Scrollbar(self.label_frame, orient=tk.VERTICAL)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.listbox.config(yscrollcommand=self.scrollbar.set)
        self.scrollbar.config(command=self.listbox.yview)
        
        # Store file paths
        self.file_paths: List[Path] = []
        self.selection_callback: Optional[Callable[[Optional[Path]], None]] = None
        
        # Bind selection event
        self.listbox.bind('<<ListboxSelect>>', self._on_selection)
    
    def _on_selection(self, event) -> None:
        """Handle listbox selection"""
        selection = self.listbox.curselection()
        selected_file = None
        
        if selection and self.file_paths:
            try:
                selected_file = self.file_paths[selection[0]]
            except IndexError:
                pass
        
        if self.selection_callback:
            self.selection_callback(selected_file)
    
    def set_selection_callback(self, callback: Callable[[Optional[Path]], None]) -> None:
        """Set callback for selection changes"""
        self.selection_callback = callback
    
    def update_files(self, file_paths: List[Path]) -> None:
        """Update the file list"""
        self.file_paths = file_paths
        self.listbox.delete(0, tk.END)
        
        if not file_paths:
            self.listbox.insert(tk.END, _("No files found"))
        else:
            for file_path in file_paths:
                self.listbox.insert(tk.END, file_path.name)
    
    def get_selected_file(self) -> Optional[Path]:
        """Get the currently selected file"""
        selection = self.listbox.curselection()
        if selection and self.file_paths:
            try:
                return self.file_paths[selection[0]]
            except IndexError:
                pass
        return None
    
    def clear_selection(self) -> None:
        """Clear the current selection"""
        self.listbox.selection_clear(0, tk.END)


class ProgressFrame(tk.Frame):
    """Frame containing progress bar and status label"""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        
        # Progress bar
        self.progress_bar = ttk.Progressbar(
            self,
            mode='determinate',
            maximum=100
        )
        self.progress_bar.pack(fill=tk.X, pady=(0, 5))
        
        # Status label
        self.status_var = tk.StringVar(value=_("Ready"))
        self.status_label = ttk.Label(
            self,
            textvariable=self.status_var,
            relief=tk.SUNKEN,
            anchor=tk.W,
            padding=3
        )
        self.status_label.pack(fill=tk.X)
    
    def set_progress(self, value: float) -> None:
        """Set progress bar value (0-100)"""
        self.progress_bar['value'] = max(0, min(100, value))
    
    def set_status(self, status: str) -> None:
        """Set status text"""
        self.status_var.set(status)
    
    def reset(self) -> None:
        """Reset progress and status"""
        self.progress_bar['value'] = 0
        self.status_var.set(_("Ready"))


class SettingsFrame(ttk.LabelFrame, TooltipMixin):
    """Frame for application settings"""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, text=_("Settings"), padding="10", **kwargs)
        
        self.setup_widgets()
    
    def setup_widgets(self) -> None:
        """Set up the settings widgets"""
        # Number of outputs
        ttk.Label(self, text=_("Number of outputs:")).grid(row=0, column=0, sticky="w", pady=2)
        self.num_outputs_var = tk.IntVar(value=3)
        self.outputs_entry = ttk.Entry(self, textvariable=self.num_outputs_var, width=8)
        self.outputs_entry.grid(row=0, column=1, sticky="w", padx=(5, 0), pady=2)
        self.create_tooltip(self.outputs_entry, _("How many music pieces to generate (1-10)"))
        
        # GA parameters
        ttk.Label(self, text=_("GA Population Size:")).grid(row=2, column=0, sticky="w", pady=2)
        self.ga_population_var = tk.IntVar(value=6)
        self.ga_population_entry = ttk.Entry(self, textvariable=self.ga_population_var, width=8)
        self.ga_population_entry.grid(row=2, column=1, sticky="w", padx=(5, 0), pady=2)
        self.create_tooltip(self.ga_population_entry, _("Number of individuals in GA population"))

        ttk.Label(self, text=_("GA Generations:")).grid(row=3, column=0, sticky="w", pady=2)
        self.ga_generations_var = tk.IntVar(value=3)
        self.ga_generations_entry = ttk.Entry(self, textvariable=self.ga_generations_var, width=8)
        self.ga_generations_entry.grid(row=3, column=1, sticky="w", padx=(5, 0), pady=2)
        self.create_tooltip(self.ga_generations_entry, _("Number of generations for GA"))

        ttk.Label(self, text=_("GA Latent Dim:")).grid(row=4, column=0, sticky="w", pady=2)
        self.ga_latent_dim_var = tk.IntVar(value=512)
        self.ga_latent_dim_entry = ttk.Entry(self, textvariable=self.ga_latent_dim_var, width=8, state='readonly')
        self.ga_latent_dim_entry.grid(row=4, column=1, sticky="w", padx=(5, 0), pady=2)
        self.create_tooltip(self.ga_latent_dim_entry, _( "Latent vector dimension for GA (fixed at 512 for this model)"))

        # Mood selection dropdown
        ttk.Label(self, text=_("Target Mood:")).grid(row=5, column=0, sticky="w", pady=2)
        self.mood_var = tk.StringVar(value='calm')
        self.mood_dropdown = ttk.OptionMenu(
            self,
            self.mood_var,
            'calm',
            'calm', 'excited', 'tense', 'neutral'
        )
        self.mood_dropdown.grid(row=5, column=1, sticky="w", padx=(5, 0), pady=2)
        self.create_tooltip(self.mood_dropdown, _("Select the target mood for music generation"))
        
        # Target BPM input
        ttk.Label(self, text=_("Target BPM:")).grid(row=6, column=0, sticky="w", pady=2)
        self.target_bpm_var = tk.DoubleVar(value=70)
        self.target_bpm_entry = ttk.Entry(self, textvariable=self.target_bpm_var, width=8)
        self.target_bpm_entry.grid(row=6, column=1, sticky="w", padx=(5, 0), pady=2)
        self.create_tooltip(self.target_bpm_entry, _( "Set the target BPM (beats per minute) for music generation"))

        # Heartbeat simulation section
        self.sim_heartbeat_frame = ttk.Frame(self)
        self.sim_heartbeat_frame.grid(row=6, column=2, sticky="w", padx=(5, 0), pady=2)
        self.sim_heartbeat_label = ttk.Label(self.sim_heartbeat_frame, text=_("Simulate Heartbeat:"))
        self.sim_heartbeat_label.pack(side=tk.LEFT)
        self.sim_heartbeat_button = ttk.Button(self.sim_heartbeat_frame, text=_("Tap"), command=self._on_heartbeat_tap)
        self.sim_heartbeat_button.pack(side=tk.LEFT, padx=(2, 0))
        self.sim_heartbeat_reset = ttk.Button(self.sim_heartbeat_frame, text=_("Reset"), command=self._reset_heartbeat_taps)
        self.sim_heartbeat_reset.pack(side=tk.LEFT, padx=(2, 0))
        self.create_tooltip(self.sim_heartbeat_button, _( "Click repeatedly to simulate your heartbeat rhythm. BPM will be calculated."))

        # Manual RR interval input (advanced)
        ttk.Label(self, text=_("Manual RR Intervals (ms):")).grid(row=8, column=0, sticky="nw", pady=2)
        self.heartbeat_text = tk.Text(self, height=3, width=30)
        self.heartbeat_text.grid(row=8, column=1, sticky="w", padx=(5, 0), pady=2)
        self.create_tooltip(self.heartbeat_text, _( "Paste or enter RR intervals (ms), comma-separated or one per line (advanced)"))

        # Internal state for heartbeat tap simulation
        self._heartbeat_tap_times = []
        
        # Volume control
        ttk.Label(self, text=_("Volume:")).grid(row=1, column=0, sticky="w", pady=2)
        self.volume_var = tk.DoubleVar(value=70)
        self.volume_scale = ttk.Scale(
            self,
            from_=0,
            to=100,
            orient=tk.HORIZONTAL,
            variable=self.volume_var,
            length=150
        )
        self.volume_scale.grid(row=1, column=1, sticky="ew", padx=(5, 0), pady=2)
        
        # Volume label
        self.volume_label = ttk.Label(self, text="70%")
        self.volume_label.grid(row=1, column=2, padx=(5, 0), pady=2)
        
        # Bind volume change
        self.volume_var.trace('w', self._on_volume_change)
        
        # Evaluator selection combobox
        ttk.Label(self, text=_("Evaluator:")).grid(row=9, column=0, sticky="w", pady=2)
        self.evaluator_var = tk.StringVar(value='music21')
        # The list of evaluators will be set externally (from main_app)
        self.evaluator_combobox = ttk.Combobox(
            self,
            textvariable=self.evaluator_var,
            state='readonly',
            width=20
        )
        self.evaluator_combobox['values'] = ['music21']  # Will be updated in main_app
        self.evaluator_combobox.grid(row=9, column=1, sticky="w", padx=(5, 0), pady=2)
        self.create_tooltip(self.evaluator_combobox, _( "Select the evaluator for fitness (music21 or LLM)"))
        
        # Configure column weights
        self.columnconfigure(1, weight=1)
    
    def _on_volume_change(self, *args) -> None:
        """Handle volume scale change"""
        volume = int(self.volume_var.get())
        self.volume_label.config(text=f"{volume}%")
    
    def get_num_outputs(self) -> int:
        """Get the number of outputs setting"""
        return self.num_outputs_var.get()
    
    def get_volume(self) -> float:
        """Get the volume setting (0.0-1.0)"""
        return self.volume_var.get() / 100.0
    
    def set_num_outputs(self, value: int) -> None:
        """Set the number of outputs"""
        self.num_outputs_var.set(max(1, min(10, value)))
    
    def set_volume(self, value: float) -> None:
        """Set the volume (0.0-1.0)"""
        volume_percent = max(0, min(100, value * 100))
        self.volume_var.set(volume_percent)

    def get_population_size(self) -> int:
        return self.ga_population_var.get()

    def get_generations(self) -> int:
        return self.ga_generations_var.get()

    def get_latent_dim(self) -> int:
        return self.ga_latent_dim_var.get()

    def get_mood(self) -> str:
        return self.mood_var.get()

    def _on_heartbeat_tap(self):
        import time
        now = time.time()
        self._heartbeat_tap_times.append(now)
        if len(self._heartbeat_tap_times) > 1:
            intervals = [int(1000 * (self._heartbeat_tap_times[i] - self._heartbeat_tap_times[i-1])) for i in range(1, len(self._heartbeat_tap_times))]
            if intervals:
                mean_rr = sum(intervals) / len(intervals)
                bpm = 60000 / mean_rr if mean_rr > 0 else 0
                self.target_bpm_var.set(round(bpm, 2))
                # Also update the interval text for transparency
                self.heartbeat_text.delete('1.0', tk.END)
                self.heartbeat_text.insert(tk.END, ', '.join(str(int(rr)) for rr in intervals))

    def _reset_heartbeat_taps(self):
        self._heartbeat_tap_times = []
        self.target_bpm_var.set(70)
        self.heartbeat_text.delete('1.0', tk.END)

    def get_target_bpm(self) -> float:
        return self.target_bpm_var.get()

    def get_evaluator(self) -> str:
        """Get the selected evaluator (music21 or LLM name)"""
        return self.evaluator_var.get()


class PlaybackControlsFrame(tk.Frame):
    """Frame containing playback control buttons"""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.play_callback: Optional[Callable[[], None]] = None
        self.stop_callback: Optional[Callable[[], None]] = None
        self.pause_callback: Optional[Callable[[], None]] = None
        
        self.setup_widgets()
    
    def setup_widgets(self) -> None:
        """Set up the playback control widgets"""
        self.play_button = ttk.Button(
            self,
            text=_("Play"),
            command=self._on_play,
            state=tk.DISABLED
        )
        self.play_button.pack(side=tk.LEFT, padx=2)
        
        self.stop_button = ttk.Button(
            self,
            text=_("Stop"),
            command=self._on_stop,
            state=tk.DISABLED
        )
        self.stop_button.pack(side=tk.LEFT, padx=2)
        
        # Optional pause button (commented out for now)
        # self.pause_button = ttk.Button(
        #     self,
        #     text=_("Pause"),
        #     command=self._on_pause,
        #     state=tk.DISABLED
        # )
        # self.pause_button.pack(side=tk.LEFT, padx=2)
    
    def _on_play(self) -> None:
        """Handle play button click"""
        if self.play_callback:
            self.play_callback()
    
    def _on_stop(self) -> None:
        """Handle stop button click"""
        if self.stop_callback:
            self.stop_callback()
    
    def _on_pause(self) -> None:
        """Handle pause button click"""
        if self.pause_callback:
            self.pause_callback()
    
    def set_play_callback(self, callback: Callable[[], None]) -> None:
        """Set the play button callback"""
        self.play_callback = callback
    
    def set_stop_callback(self, callback: Callable[[], None]) -> None:
        """Set the stop button callback"""
        self.stop_callback = callback
    
    def set_pause_callback(self, callback: Callable[[], None]) -> None:
        """Set the pause button callback"""
        self.pause_callback = callback
    
    def enable_play(self, enabled: bool = True) -> None:
        """Enable/disable the play button"""
        self.play_button.config(state=tk.NORMAL if enabled else tk.DISABLED)
    
    def enable_stop(self, enabled: bool = True) -> None:
        """Enable/disable the stop button"""
        self.stop_button.config(state=tk.NORMAL if enabled else tk.DISABLED)
    
    def set_playback_state(self, playing: bool) -> None:
        """Update button states based on playback state"""
        if playing:
            self.enable_play(False)
            self.enable_stop(True)
        else:
            self.enable_play(True)
            self.enable_stop(False)