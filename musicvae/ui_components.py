"""
Reusable UI components for the MusicVAE Generator application
"""
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