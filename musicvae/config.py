"""
Configuration management module for MusicVAE Generator
"""
import configparser
from pathlib import Path
from typing import Dict, Any


class AppConfig:
    """Handles application configuration loading and saving"""
    
    def __init__(self, config_file: str = "config.ini"):
        self.config = configparser.ConfigParser()
        self.config_file = Path(config_file)
        self.load_config()
        
    def load_config(self) -> None:
        """Load configuration from file or create default config"""
        default_config = self._get_default_config()
        
        if not self.config_file.exists():
            self.config.read_dict(default_config)
            self.save_config()
        else:
            self.config.read(self.config_file)
            self._ensure_config_completeness(default_config)
    
    def _get_default_config(self) -> Dict[str, Dict[str, str]]:
        """Return default configuration dictionary"""
        return {
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
    
    def _ensure_config_completeness(self, default_config: Dict[str, Dict[str, str]]) -> None:
        """Ensure all required sections and keys exist in config"""
        config_changed = False
        
        for section, options in default_config.items():
            if not self.config.has_section(section):
                self.config.add_section(section)
                config_changed = True
                
            for key, value in options.items():
                if not self.config.has_option(section, key):
                    self.config.set(section, key, value)
                    config_changed = True
        
        if config_changed:
            self.save_config()
    
    def save_config(self) -> None:
        """Save current configuration to file"""
        with open(self.config_file, 'w') as f:
            self.config.write(f)
    
    def get_value(self, section: str, key: str, fallback: Any = None) -> str:
        """Get a configuration value"""
        return self.config.get(section, key, fallback=fallback)
    
    def set_value(self, section: str, key: str, value: str) -> None:
        """Set a configuration value and save"""
        if not self.config.has_section(section):
            self.config.add_section(section)
        self.config.set(section, key, value)
        self.save_config()
    
    # Properties for easy access to common paths and settings
    @property
    def music_vae_path(self) -> Path:
        return Path(self.get_value('PATHS', 'music_vae_path'))
    
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
        return Path(self.get_value('PATHS', 'fluidsynth_path'))
    
    @property
    def default_outputs(self) -> int:
        return int(self.get_value('SETTINGS', 'default_outputs', '3'))
    
    @property
    def default_volume(self) -> int:
        return int(self.get_value('SETTINGS', 'volume', '70'))
    
    @property
    def language(self) -> str:
        return self.get_value('SETTINGS', 'language', 'en')
    
    def validate_paths(self) -> bool:
        """Validate that all required paths exist"""
        required_paths = [
            self.music_vae_path,
            self.checkpoint_path,
            self.soundfont_path,
            self.fluidsynth_path
        ]
        return all(path.exists() for path in required_paths)
    
    def get_missing_paths(self) -> list[Path]:
        """Get list of missing required paths"""
        required_paths = [
            self.music_vae_path,
            self.checkpoint_path,
            self.soundfont_path,
            self.fluidsynth_path
        ]
        return [path for path in required_paths if not path.exists()]