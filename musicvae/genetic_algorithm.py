from typing import List, Callable
import numpy as np
from pathlib import Path
from latent_vector_individual import LatentVectorIndividual
from musicvae_wrapper import MusicVAEWrapper

class GeneticAlgorithm:
    def __init__(self, population_size: int, latent_dim: int):
        self.population_size = population_size
        self.latent_dim = latent_dim
        self.population: List[LatentVectorIndividual] = [
            LatentVectorIndividual(latent_dim) for _ in range(population_size)
        ]

    def evaluate(self, fitness_fn: Callable[[LatentVectorIndividual], float]):
        for individual in self.population:
            individual.fitness = fitness_fn(individual)

    def select(self) -> List[LatentVectorIndividual]:
        # Select top 50% by fitness
        sorted_pop = sorted(self.population, key=lambda ind: ind.fitness, reverse=True)
        return sorted_pop[:self.population_size // 2]

    def reproduce(self, selected: List[LatentVectorIndividual]):
        children = []
        while len(children) < self.population_size - len(selected):
            parents = np.random.choice(selected, 2, replace=False)
            child = parents[0].crossover(parents[1])
            child.mutate()
            children.append(child)
        self.population = selected + children

class MusicGeneticAlgorithm(GeneticAlgorithm):
    def __init__(self, population_size: int, latent_dim: int, music_generator: MusicVAEWrapper, output_dir: Path):
        super().__init__(population_size, latent_dim)
        self.music_generator = music_generator
        self.output_dir = output_dir
        self.generation = 0

    def fitness_fn(self, individual: LatentVectorIndividual) -> float:
        # Generate music and assign a dummy fitness (e.g., sum of latent vector)
        output_path = self.output_dir / f"music_gen_{self.generation}_{id(individual)}.txt"
        self.music_generator.generate(individual.vector, output_path)
        # Dummy fitness: negative L2 norm (for demo)
        return -np.linalg.norm(individual.vector)

    def run(self, generations: int):
        for gen in range(generations):
            self.generation = gen
            print(f"Generation {gen}")
            self.evaluate(self.fitness_fn)
            best = max(self.population, key=lambda ind: ind.fitness)
            print(f"  Best fitness: {best.fitness:.4f}")
            selected = self.select()
            self.reproduce(selected)

if __name__ == "__main__":
    # Example usage
    latent_dim = 8
    population_size = 6
    generations = 3
    output_dir = Path("./ga_output")
    output_dir.mkdir(exist_ok=True)
    music_generator = MusicVAEWrapper()
    ga = MusicGeneticAlgorithm(population_size, latent_dim, music_generator, output_dir)
    ga.run(generations) 