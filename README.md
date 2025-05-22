# 🎵 MusicVAE Generator

A desktop application for generating music using Google's MusicVAE (Variational Autoencoder for Music) with GPU acceleration. This application provides an intuitive GUI for creating AI-generated music and converting it to playable audio formats.

## Features

- **AI Music Generation**: Generate music using pre-trained MusicVAE models
- **GPU Acceleration**: Leverages CUDA-enabled GPUs for faster generation
- **Audio Conversion**: Automatic MIDI to WAV conversion using FluidSynth
- **Built-in Playback**: Play generated music directly in the application
- **Configurable Settings**: Customize generation parameters and audio settings
- **Multi-language Support**: Internationalization ready (i18n)
- **Comprehensive Logging**: Detailed activity logs for debugging and monitoring

## Prerequisites

### System Requirements

- **Python**: 3.8 or higher
- **Operating System**: Windows 10+, macOS 10.14+, or Linux
- **Memory**: At least 4GB RAM (8GB+ recommended)
- **Storage**: 2GB+ free space for models and generated files
- **GPU** (Optional): NVIDIA GPU with CUDA support for acceleration

### Required Software

1. **FluidSynth**: For MIDI to audio conversion
   - **Windows**: Download from [FluidSynth website](https://www.fluidsynth.org/)
   - **macOS**: `brew install fluidsynth`
   - **Ubuntu/Debian**: `sudo apt-get install fluidsynth libfluidsynth-dev`

2. **MusicVAE Models**: Download pre-trained models from [Magenta](https://github.com/magenta/magenta/tree/main/magenta/models/music_vae)

3. **SoundFont Files**: Required for audio synthesis (e.g., FluidR3_GM.sf2)

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/musicvae-generator.git
cd musicvae-generator
```

### 2. Create Virtual Environment (Recommended)

```bash
python -m venv musicvae-env
source musicvae-env/bin/activate  # On Windows: musicvae-env\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure the Application

1. Copy the example configuration:
   ```bash
   cp config.ini.example config.ini
   ```

2. Edit `config.ini` with your system paths:
   ```ini
   [PATHS]
   music_vae_path = /path/to/your/magenta_musicgen
   fluidsynth_path = /path/to/fluidsynth/executable
   
   [SETTINGS]
   default_outputs = 3
   volume = 70
   language = en
   ```

## Usage

### Running the Application

```bash
python main.py
```

Or directly:

```bash
python -m main_app
```

### Basic Workflow

1. **Configure Settings**: Set the number of outputs and audio volume
2. **Generate Music**: Click "Generate Music" to start AI music generation
3. **Wait for Conversion**: The app automatically converts MIDI to WAV
4. **Play Music**: Select generated files from the list and click "Play"

### Keyboard Shortcuts

- `Ctrl+G`: Start generation
- `F5`: Refresh file list
- `Space`: Toggle playback
- `Escape`: Stop playback
- `Ctrl+Q`: Quit application

## File Structure

```
musicvae-generator/
├── main.py                 # Application entry point
├── main_app.py            # Main application class
├── config.py              # Configuration management
├── music_generator.py     # Music generation logic
├── audio_player.py        # Audio playback management
├── localization.py        # Internationalization support
├── ui_components.py       # Reusable UI components
├── requirements.txt       # Python dependencies
├── config.ini            # Application configuration
├── README.md             # This file
└── locales/              # Translation files
    ├── en/
    ├── es/
    └── fr/
```

## Configuration

### Application Settings

The `config.ini` file contains all application settings:

```ini
[PATHS]
# Path to MusicVAE installation directory
music_vae_path = C:/Users/username/magenta_musicgen

# Path to FluidSynth executable
fluidsynth_path = C:/tools/fluidsynth/bin/fluidsynth.exe

[SETTINGS]
# Default number of music pieces to generate
default_outputs = 3

# Default audio volume (0-100)
volume = 70

# Interface language
language = en
```

### Model Configuration

Ensure your MusicVAE installation has the following structure:

```
magenta_musicgen/
├── models/
│   └── hierdec-trio_16bar.tar
├── soundfonts/
│   └── FluidR3_GM.sf2
└── musicvae/
    └── generated/  # Output directory
```

## Troubleshooting

### Common Issues

1. **"Configuration Error" on startup**
   - Check that all paths in `config.ini` are correct
   - Ensure MusicVAE models and FluidSynth are properly installed

2. **"No CUDA devices found" warning**
   - This is normal if you don't have an NVIDIA GPU
   - The application will fall back to CPU generation (slower)

3. **Audio playback issues**
   - Verify that pygame can access your audio system
   - Check system audio settings and permissions

4. **Generation fails immediately**
   - Ensure MusicVAE is properly installed
   - Check that the checkpoint file exists and is valid
   - Review the application logs for detailed error messages

### Logging

The application creates detailed logs in:
- Console output during runtime
- `musicvae_generator.log` file in the application directory
- Built-in log viewer in the application

## Development

### Adding New Features

The application uses a modular architecture:

- **config.py**: Add new configuration options
- **music_generator.py**: Extend music generation capabilities
- **audio_player.py**: Enhance audio playback features
- **ui_components.py**: Create new UI widgets
- **localization.py**: Add new language support

### Adding Translations

1. Create translation template:
   ```bash
   xgettext --language=Python --keyword=_ --output=locales/messages.pot *.py
   ```

2. Create language-specific translations:
   ```bash
   mkdir -p locales/es/LC_MESSAGES
   msginit --input=locales/messages.pot --locale=es --output=locales/es/LC_MESSAGES/musicvae.po
   ```

3. Compile translations:
   ```bash
   msgfmt locales/es/LC_MESSAGES/musicvae.po -o locales/es/LC_MESSAGES/musicvae.mo
   ```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- **Google Magenta Team**: For the MusicVAE model and research
- **FluidSynth Project**: For the audio synthesis engine
- **Python Community**: For the excellent libraries and tools

## Support

If you encounter issues or have questions:

1. Check the [troubleshooting section](#troubleshooting)
2. Review the application logs
3. Search existing [GitHub Issues](https://github.com/your-username/musicvae-generator/issues)
4. Create a new issue with detailed information

---

**Happy Music Making! 🎵**