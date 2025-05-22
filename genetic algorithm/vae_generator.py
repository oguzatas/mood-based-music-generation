from magenta.models.music_vae import TrainedModel
from magenta.models.music_vae import configs
import tensorflow.compat.v1 as tf
from note_seq.protobuf import music_pb2
import note_seq
import os
import json

tf.disable_v2_behavior()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "models", "music_vae", "hierdec-trio_16bar")
CONFIG_PATH = os.path.join(MODEL_PATH, "config.json")
CHECKPOINT_PATH = os.path.join(MODEL_PATH, "model.ckpt")

def get_vae_model():
    # config.json dosyasını yükle
    with open(CONFIG_PATH, "r") as f:
        config_dict = json.load(f)

    # Config nesnesini elle oluştur (çünkü config_from_checkpoint artık yok)
    config = configs.CONFIG_MAP["hierdec-trio_16bar"]  # Bu kısmı modeline göre değiştir
    return TrainedModel(
        config=config,
        batch_size=4,
        checkpoint_dir_or_path=CHECKPOINT_PATH
    )

def generate_trio(num_steps=1):
    vae = get_vae_model()
    return vae.sample(n=num_steps, length=256, temperature=0.8)

def save_sequence_as_midi(sequence, filename):
    note_seq.sequence_proto_to_midi_file(sequence, filename)
