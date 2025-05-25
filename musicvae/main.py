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

from typing import Dict, List, Set, Tuple
import sys
import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env before anything else
load_dotenv()

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
        logger.error("Python 3.8 or higher is required")
        sys.exit(1)
    
    # Check for required directories
    required_dirs = ['locales']
    for dir_name in required_dirs:
        dir_path = current_dir / dir_name
        if not dir_path.exists():
            logger.warning(f"Creating missing directory: {dir_path}")
            dir_path.mkdir(parents=True, exist_ok=True)
    
    return logger


def check_dependencies():
    """Check for required dependencies"""
    logger = logging.getLogger(__name__)
    missing_deps = []
    
    # Required packages
    required_packages = [
        ('tkinter', 'tkinter'),
        ('pygame', 'pygame'),
        ('configparser', 'configparser'),
        ('pathlib', 'pathlib')
    ]
    
    for package_name, import_name in required_packages:
        try:
            __import__(import_name)
            logger.debug(f"✓ {package_name} available")
        except ImportError:
            missing_deps.append(package_name)
            logger.error(f"✗ {package_name} not available")
    
    # Optional but recommended packages
    optional_packages = [
        ('tensorflow', 'tensorflow'),
        ('magenta', 'magenta')
    ]
    
    for package_name, import_name in optional_packages:
        try:
            __import__(import_name)
            logger.info(f"✓ {package_name} available")
        except ImportError:
            logger.warning(f"! {package_name} not available (required for music generation)")
    
    if missing_deps:
        logger.error(f"Missing required dependencies: {', '.join(missing_deps)}")
        print("\nMissing required dependencies:")
        for dep in missing_deps:
            print(f"  - {dep}")
        print("\nPlease install missing dependencies and try again.")
        return False
    
    return True


def main():
    """Main entry point"""
    try:
        # Set up environment
        logger = setup_environment()
        
        # Check dependencies
        if not check_dependencies():
            sys.exit(1)
        
        # Import and run the main application
        logger.info("Loading main application...")
        
        try:
            from main_app import main as run_app
            logger.info("Starting GUI application...")
            run_app()
            
        except ImportError as e:
            logger.error(f"Failed to import main application: {e}")
            print(f"Error: Could not load main application: {e}")
            print("Please ensure all application files are present.")
            sys.exit(1)
            
        except Exception as e:
            logger.error(f"Application error: {e}", exc_info=True)
            print(f"Application error: {e}")
            sys.exit(1)
    
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        print("\nApplication interrupted by user.")
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        print(f"Fatal error: {e}")
        sys.exit(1)
    
    finally:
        logger.info("Application shutdown complete")


if __name__ == "__main__":
    main()