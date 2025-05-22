# ga_core.py
from vae_generator import generate_trio
from note_analysis import fitness
import random

def generate_initial_population(n=5):
    return [generate_trio() for _ in range(n)]

def select_best(population, bpm):
    scored = [(seq, fitness(seq, bpm)) for seq in population]
    return sorted(scored, key=lambda x: x[1], reverse=True)[:3]

def crossover_and_mutate(selected):
    # VAE latent space crossover gibi gelişmiş işlemler ileride eklenebilir
    return [generate_trio() for _ in range(5)]
