#!/usr/bin/env python3
"""
MusicVAE Generator - Main Entry Point

A GUI application for generating music using Google's MusicVAE model.
This application generates MIDI files using AI and converts them to WAV format for playback.

Features:
- GPU-accelerated music generation using MusicVAE
- MIDI to WAV conversion using FluidSynth
- Built-in audio playback
- Configurable settings
- Internationalization support
- Comprehensive logging

Requirements:
- Python 3.8+
- TensorFlow with GPU support
- MusicVAE model and checkpoint files
- FluidSynth for audio conversion
- SoundFont files for audio synthesis

Author: MusicVAE Generator Team
License: MIT
"""

import sys
import os
import logging
from pathlib import Path

# Add the current directory to Python path to ensure imports work
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

def setup_environment():
    """Set up the application environment"""
    # Set up basic logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('musicvae_generator.log', encoding='utf-8')
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info("Starting MusicVAE Generator application")
    
    # Check Python version
    if sys.version_info < (3, 8):
        logger.error("Python