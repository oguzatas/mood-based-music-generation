"""
Localization and internationalization module
"""
from typing import Dict, List, Set, Tuple
import gettext
import logging
from pathlib import Path
from typing import Optional, Callable


class LocalizationManager:
    """Manages application localization and translations"""
    
    def __init__(self, domain: str = 'musicvae', locale_dir: Optional[Path] = None):
        self.domain = domain
        self.locale_dir = locale_dir or Path(__file__).parent / "locales"
        self.current_language = 'en'
        self.translation: Optional[gettext.GNUTranslations] = None
        self.logger = logging.getLogger(__name__)
        
        # Global translation function
        self._translation_func: Callable[[str], str] = lambda text: text
        
    def set_language(self, language_code: str) -> bool:
        """
        Set the current language for the application
        
        Args:
            language_code: Language code (e.g., 'en', 'es', 'fr')
            
        Returns:
            bool: True if language was set successfully, False otherwise
        """
        try:
            if language_code == 'en':
                # English is the default, no translation needed
                self.translation = None
                self._translation_func = lambda text: text
                self.current_language = 'en'
                self.logger.info("Language set to English (default)")
                return True
            
            # Try to load translation for the specified language
            translation = gettext.translation(
                self.domain,
                localedir=self.locale_dir,
                languages=[language_code],
                fallback=False
            )
            
            self.translation = translation
            self._translation_func = translation.gettext
            self.current_language = language_code
            
            self.logger.info(f"Language set to {language_code}")
            return True
            
        except FileNotFoundError:
            self.logger.warning(f"Translation not found for language: {language_code}")
            return False
        except Exception as e:
            self.logger.error(f"Error setting language {language_code}: {e}")
            return False
    
    def get_current_language(self) -> str:
        """Get the current language code"""
        return self.current_language
    
    def translate(self, message: str) -> str:
        """
        Translate a message using the current language
        
        Args:
            message: The message to translate
            
        Returns:
            str: The translated message, or original if no translation available
        """
        try:
            return self._translation_func(message)
        except Exception as e:
            self.logger.error(f"Translation error for '{message}': {e}")
            return message
    
    def get_available_languages(self) -> List[str]:
        """
        Get list of available languages based on locale directory
        
        Returns:
            List[str]: List of available language codes
        """
        available = ['en']  # English is always available as default
        
        try:
            if not self.locale_dir.exists():
                return available
            
            # Look for .mo files in locale subdirectories
            for lang_dir in self.locale_dir.iterdir():
                if lang_dir.is_dir():
                    mo_file = lang_dir / "LC_MESSAGES" / f"{self.domain}.mo"
                    if mo_file.exists():
                        available.append(lang_dir.name)
            
        except Exception as e:
            self.logger.error(f"Error scanning for available languages: {e}")
        
        return sorted(available)
    
    def create_translation_template(self, source_files: List[Path], output_file: Optional[Path] = None) -> bool:
        """
        Create a .pot template file from source files for translation
        
        Args:
            source_files: List of Python source files to extract strings from
            output_file: Output .pot file path (defaults to locales/messages.pot)
            
        Returns:
            bool: True if template was created successfully
        """
        try:
            import subprocess
            
            if output_file is None:
                self.locale_dir.mkdir(exist_ok=True)
                output_file = self.locale_dir / "messages.pot"
            
            # Use xgettext to extract translatable strings
            cmd = [
                'xgettext',
                '--language=Python',
                '--keyword=_',
                '--output=' + str(output_file),
                '--from-code=UTF-8'
            ] + [str(f) for f in source_files]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.logger.info(f"Translation template created: {output_file}")
                return True
            else:
                self.logger.error(f"xgettext failed: {result.stderr}")
                return False
                
        except FileNotFoundError:
            self.logger.error("xgettext not found. Please install gettext tools.")
            return False
        except Exception as e:
            self.logger.error(f"Error creating translation template: {e}")
            return False
    
    def install_global_function(self) -> None:
        """Install the translation function globally as '_' """
        import builtins
        builtins._ = self._translation_func
    
    def get_language_display_names(self) -> Dict[str, str]:
        """
        Get display names for available languages
        
        Returns:
            dict: Mapping of language codes to display names
        """
        language_names = {
            'en': 'English',
            'es': 'Español',
            'fr': 'Français',
            'de': 'Deutsch',
            'it': 'Italiano',
            'pt': 'Português',
            'ru': 'Русский',
            'ja': '日本語',
            'ko': '한국어',
            'zh': '中文',
            'ar': 'العربية'
        }
        
        available_languages = self.get_available_languages()
        return {
            code: language_names.get(code, code.upper()) 
            for code in available_languages
        }


# Global localization manager instance
_localization_manager: Optional[LocalizationManager] = None


def init_localization(language: str = 'en', 
                     domain: str = 'musicvae', 
                     locale_dir: Optional[Path] = None) -> LocalizationManager:
    """
    Initialize the global localization manager
    
    Args:
        language: Initial language code
        domain: Translation domain name
        locale_dir: Directory containing locale files
        
    Returns:
        LocalizationManager: The initialized localization manager
    """
    global _localization_manager
    
    _localization_manager = LocalizationManager(domain, locale_dir)
    _localization_manager.set_language(language)
    _localization_manager.install_global_function()
    
    return _localization_manager


def get_localization_manager() -> Optional[LocalizationManager]:
    """Get the global localization manager instance"""
    return _localization_manager


def _(message: str) -> str:
    """
    Global translation function
    
    Args:
        message: Message to translate
        
    Returns:
        str: Translated message or original if no localization manager
    """
    if _localization_manager:
        return _localization_manager.translate(message)
    return message


def set_language(language_code: str) -> bool:
    """
    Set the global language
    
    Args:
        language_code: Language code to set
        
    Returns:
        bool: True if successful, False otherwise
    """
    if _localization_manager:
        return _localization_manager.set_language(language_code)
    return False