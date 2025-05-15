# 🎵 Mood & Heartbeat Based Music Generator

This project generates dynamic music based on **user mood** and **heartbeat** data. It uses Google's [Magenta](https://magenta.tensorflow.org/) models (`melody_rnn`) to create melodies that reflect the emotional and physiological state of a user.

## 🧠 Core Idea

- **Mood** affects:
  - The musical **scale** (e.g., Minor, Major, Locrian, etc.)
  - The **primer melody** (starting notes)
  - The **temperature** parameter (creativity/randomness in generation)
  
- **Heartbeat (BPM)** affects:
  - The **tempo** of the music

## 🛠 Technologies Used

- Python 3
- [Magenta](https://github.com/magenta/magenta) (Melody RNN)
- TensorFlow 1.x (via Magenta)
- FluidSynth + `midi2audio` for MIDI to WAV rendering
- `note_seq` and `magenta.music` for MIDI processing

## 📁 Folder Structure

