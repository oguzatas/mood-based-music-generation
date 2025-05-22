from magenta.models.music_vae import configs
import json
import os

model_name = "hierdec-trio_16bar"
config = configs.CONFIG_MAP[model_name]

# Minimal config json - sadece model adı yeterlidir
config_dict = {
    "name": model_name
}

# Model klasörünü ayarla
model_dir = os.path.join("models", "music_vae", model_name)

# config.json dosyasını yaz
config_path = os.path.join(model_dir, "config.json")
with open(config_path, "w") as f:
    json.dump(config_dict, f, indent=2)

print(f"config.json created at: {config_path}")
