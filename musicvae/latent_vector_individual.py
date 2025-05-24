import numpy as np
from typing import Any

class LatentVectorIndividual:
    """Represents an individual (latent vector) for genetic algorithm evolution."""
    def __init__(self, latent_dim: int, vector: np.ndarray = None):
        self.latent_dim = latent_dim
        self.vector = vector if vector is not None else np.random.randn(latent_dim)
        self.fitness: float = None
        self.metadata: Any = None  # For storing extra info (e.g., generated file path)

    def mutate(self, mutation_rate: float = 0.1):
        noise = np.random.randn(self.latent_dim) * mutation_rate
        self.vector += noise

    def crossover(self, other: 'LatentVectorIndividual') -> 'LatentVectorIndividual':
        mask = np.random.rand(self.latent_dim) > 0.5
        child_vector = np.where(mask, self.vector, other.vector)
        return LatentVectorIndividual(self.latent_dim, child_vector) 