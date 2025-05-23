from typing import List, Callable
import numpy as np
from pathlib import Path
from latent_vector_individual import LatentVectorIndividual
from musicvae_wrapper import MusicVAEWrapper
import pretty_midi

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

def mood_to_target_tempo(mood: str) -> float:
    return {
        'calm': 70,
        'excited': 120,
        'tense': 100,
        'neutral': 90
    }.get(mood, 90)

class MusicGeneticAlgorithm(GeneticAlgorithm):
    def __init__(self, population_size: int, latent_dim: int, music_generator: MusicVAEWrapper, output_dir: Path, target_mood: str = 'calm'):
        super().__init__(population_size, latent_dim)
        self.music_generator = music_generator
        self.output_dir = output_dir
        self.generation = 0
        self.target_mood = target_mood
        self.target_tempo = mood_to_target_tempo(target_mood)

    def fitness_fn(self, individual: LatentVectorIndividual) -> float:
        output_path = self.output_dir / f"music_gen_{self.generation}_{id(individual)}.mid"
        try:
            self.music_generator.logger.info(f"GA: Generating for individual {id(individual)}")
            result = self.music_generator.generate(individual.vector, output_path)
            self.music_generator.logger.info(f"GA: Generation result: {result}")
            midi_path = result.get('midi_path') or result.get('output_path')
            if not midi_path or not Path(midi_path).exists():
                self.music_generator.logger.error("GA: MIDI file not created.")
                return -9999  # Penalize
            try:
                self.music_generator.logger.info(f"GA: Analyzing MIDI {midi_path}")
                midi = pretty_midi.PrettyMIDI(str(midi_path))
                tempo = midi.estimate_tempo()
                self.music_generator.logger.info(f"GA: Estimated tempo: {tempo}")
            except Exception as e:
                self.music_generator.logger.error(f"GA: pretty_midi failed: {e}")
                tempo = 0
            fitness = -abs(tempo - self.target_tempo)
            self.music_generator.logger.info(f"GA: Fitness for individual {id(individual)}: {fitness}")
            return fitness
        except Exception as e:
            self.music_generator.logger.error(f"GA: Exception in fitness_fn: {e}")
            return -9999

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