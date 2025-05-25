import os

# Helper to load from environment with fallback
def env(key: str, default=None):
    return os.environ.get(key, default)

# LLM configuration module
# Stores API keys, endpoints, and model names for each LLM

LLM_CONFIG = {
    'openai': {
        'api_key': env('OPENAI_API_KEY'),
        'endpoint': env('OPENAI_ENDPOINT', 'https://api.openai.com/v1/chat/completions'),
        'model': env('OPENAI_MODEL', 'gpt-4'),
    },
    'gemini': {
        'api_key': env('GEMINI_API_KEY'),
        'endpoint': env('GEMINI_ENDPOINT', 'https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent'),
        'model': env('GEMINI_MODEL', 'gemini-pro'),
    },
    'ollama': {
        'api_key': env('OLLAMA_API_KEY'),  # Not needed for local
        'endpoint': env('OLLAMA_ENDPOINT', 'http://localhost:11434/api/generate'),
        'model': env('OLLAMA_MODEL', 'llama2'),
    },
    # Add more LLMs as needed
}

def get_llm_config(llm_name: str) -> dict:
    """Return the config dict for a given LLM name."""
    return LLM_CONFIG.get(llm_name, {})

# Example: Other hardcoded paths/strings (migrate these to env as well)
SOUND_FONT_PATH = env('SOUND_FONT_PATH', 'soundfonts/FluidR3_GM.sf2')
FLUIDSYNTH_PATH = env('FLUIDSYNTH_PATH', 'fluidsynth')
MUSICVAE_CHECKPOINT = env('MUSICVAE_CHECKPOINT', 'checkpoints/hierdec-trio_16bar.tar')
# ... add more as needed

# All config values are loaded from environment variables above. No hardcoded strings remain. 