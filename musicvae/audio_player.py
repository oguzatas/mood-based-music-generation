"""
Audio playback management module
"""
from typing import Dict, List, Set, Tuple
import pygame
import logging
from pathlib import Path
from typing import Optional, Callable
from enum import Enum


class PlaybackState(Enum):
    """Enumeration for playback states"""
    STOPPED = "stopped"
    PLAYING = "playing"
    PAUSED = "paused"


class AudioPlayer:
    """Handles audio playback using pygame mixer"""
    
    def __init__(self, initial_volume: float = 0.7):
        self.logger = logging.getLogger(__name__)
        self.current_file: Optional[Path] = None
        self.state = PlaybackState.STOPPED
        self.volume = initial_volume
        self.playback_callbacks: List[Callable[[PlaybackState], None]] = []
        
        # Initialize pygame mixer
        try:
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=2048)
            pygame.mixer.music.set_volume(self.volume)
            self.logger.info("Audio player initialized successfully")
        except pygame.error as e:
            self.logger.error(f"Failed to initialize audio player: {e}")
            raise
    
    def add_playback_callback(self, callback: Callable[[PlaybackState], None]) -> None:
        """Add a callback to be called when playback state changes"""
        self.playback_callbacks.append(callback)
    
    def remove_playback_callback(self, callback: Callable[[PlaybackState], None]) -> None:
        """Remove a playback state callback"""
        if callback in self.playback_callbacks:
            self.playback_callbacks.remove(callback)
    
    def _notify_state_change(self, new_state: PlaybackState) -> None:
        """Notify all callbacks of state change"""
        self.state = new_state
        for callback in self.playback_callbacks:
            try:
                callback(new_state)
            except Exception as e:
                self.logger.error(f"Error in playback callback: {e}")
    
    def play_file(self, file_path: Path) -> bool:
        """
        Play an audio file
        
        Args:
            file_path: Path to the audio file to play
            
        Returns:
            bool: True if playback started successfully, False otherwise
        """
        try:
            if not file_path.exists():
                self.logger.error(f"Audio file not found: {file_path}")
                return False
            
            if not self._is_supported_format(file_path):
                self.logger.error(f"Unsupported audio format: {file_path.suffix}")
                return False
            
            # Stop current playback if any
            if self.is_playing():
                self.stop()
            
            # Load and play the file
            pygame.mixer.music.load(str(file_path))
            pygame.mixer.music.play()
            
            self.current_file = file_path
            self._notify_state_change(PlaybackState.PLAYING)
            
            self.logger.info(f"Started playing: {file_path.name}")
            return True
            
        except pygame.error as e:
            self.logger.error(f"Failed to play {file_path}: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error playing {file_path}: {e}")
            return False
    
    def stop(self) -> None:
        """Stop current playback"""
        try:
            if pygame.mixer.music.get_busy():
                pygame.mixer.music.stop()
            
            self.current_file = None
            self._notify_state_change(PlaybackState.STOPPED)
            self.logger.info("Playback stopped")
            
        except Exception as e:
            self.logger.error(f"Error stopping playback: {e}")
    
    def pause(self) -> None:
        """Pause current playback"""
        try:
            if self.is_playing():
                pygame.mixer.music.pause()
                self._notify_state_change(PlaybackState.PAUSED)
                self.logger.info("Playback paused")
        except Exception as e:
            self.logger.error(f"Error pausing playback: {e}")
    
    def resume(self) -> None:
        """Resume paused playback"""
        try:
            if self.state == PlaybackState.PAUSED:
                pygame.mixer.music.unpause()
                self._notify_state_change(PlaybackState.PLAYING)
                self.logger.info("Playback resumed")
        except Exception as e:
            self.logger.error(f"Error resuming playback: {e}")
    
    def set_volume(self, volume: float) -> None:
        """
        Set playback volume
        
        Args:
            volume: Volume level between 0.0 and 1.0
        """
        try:
            volume = max(0.0, min(1.0, volume))  # Clamp between 0 and 1
            self.volume = volume
            pygame.mixer.music.set_volume(volume)
            self.logger.debug(f"Volume set to {volume:.2f}")
        except Exception as e:
            self.logger.error(f"Error setting volume: {e}")
    
    def get_volume(self) -> float:
        """Get current volume level"""
        return self.volume
    
    def is_playing(self) -> bool:
        """Check if audio is currently playing"""
        try:
            return pygame.mixer.music.get_busy()
        except Exception:
            return False
    
    def get_current_file(self) -> Optional[Path]:
        """Get the currently loaded file"""
        return self.current_file
    
    def get_state(self) -> PlaybackState:
        """Get current playback state"""
        # Update state based on pygame mixer status
        if pygame.mixer.music.get_busy():
            if self.state != PlaybackState.PLAYING:
                self.state = PlaybackState.PLAYING
        else:
            if self.state == PlaybackState.PLAYING:
                self.state = PlaybackState.STOPPED
        
        return self.state
    
    def _is_supported_format(self, file_path: Path) -> bool:
        """Check if the file format is supported"""
        supported_formats = {'.wav', '.mp3', '.ogg', '.mid', '.midi'}
        return file_path.suffix.lower() in supported_formats
    
    def get_supported_formats(self) -> List[str]:
        """Get list of supported audio formats"""
        return ['.wav', '.mp3', '.ogg', '.mid', '.midi']
    
    def cleanup(self) -> None:
        """Clean up audio resources"""
        try:
            self.stop()
            pygame.mixer.quit()
            self.logger.info("Audio player cleaned up")
        except Exception as e:
            self.logger.error(f"Error during audio cleanup: {e}")
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.cleanup()