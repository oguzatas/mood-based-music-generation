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
        self.