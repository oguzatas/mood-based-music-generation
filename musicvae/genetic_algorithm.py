from typing import List, Callable
import numpy as np
from pathlib import Path
from latent_vector_individual import LatentVectorIndividual
from musicvae_wrapper import MusicVAEWrapper
import pretty_midi
from music_analysis import midi_to_symbolic_text, prepare_llm_prompt_from_midi, analyze_midi_with_music21
import json
import requests
from llm_config import get_llm_config
import os

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
    def __init__(self, population_size: int, latent_dim: int, music_generator: MusicVAEWrapper, output_dir: Path, target_mood: str = 'calm', target_bpm: float = None, target_variability: float = None, llm_names: list = None, llm_feedback_dir: Path = None):
        super().__init__(population_size, latent_dim)
        self.music_generator = music_generator
        self.output_dir = output_dir
        self.generation = 0
        self.target_mood = target_mood
        self.target_tempo = mood_to_target_tempo(target_mood)
        self.target_bpm = target_bpm
        self.target_variability = target_variability
        self.llm_names = llm_names or ['openai', 'gemini']
        self.llm_feedback_dir = llm_feedback_dir or (output_dir / 'llm_feedbacks')
        self.llm_feedback_dir.mkdir(exist_ok=True, parents=True)
        self.llm_feedbacks = {}  # {(gen, individual_id): {llm_name: feedback_dict}}

    def prepare_llm_prompt(self, midi_path: Path) -> str:
        return prepare_llm_prompt_from_midi(
            midi_path,
            self.target_mood,
            self.target_bpm or self.target_tempo,
            self.target_variability
        )

    def get_llm_feedback(self, prompt: str, llm_name: str, midi_path: Path = None) -> dict:
        """
        Get feedback from an LLM or music21 analysis. For 'music21', return symbolic analysis as feedback.
        For real LLMs, use the config and make an API call.
        """
        if llm_name == 'music21':
            # Use music21 analysis as a baseline feedback
            if midi_path is None:
                return {'score': 5, 'suggestions': 'No MIDI path provided for music21 analysis.'}
            features = analyze_midi_with_music21(midi_path)
            # Simple scoring: closer to target tempo and density is better
            tempo = features.get('tempo', 0)
            density = features.get('note_density', 0)
            target_bpm = self.target_bpm if self.target_bpm is not None else self.target_tempo
            target_var = self.target_variability if self.target_variability is not None else density
            tempo_score = -abs(tempo - target_bpm)
            density_score = -abs(density - target_var)
            score = 5 + 0.5 * (tempo_score + 0.5 * density_score) / 10  # Normalize to ~1-10
            suggestions = f"music21 analysis: tempo={tempo}, note_density={density}, key={features.get('key')}, mode={features.get('mode')}, time_signature={features.get('time_signature')}"
            return {'score': max(1, min(10, score)), 'suggestions': suggestions, 'features': features}
        # --- LLM API call builder ---
        config = get_llm_config(llm_name)
        if not config:
            return {'score': 5, 'suggestions': f'No config for {llm_name}.'}
        try:
            if llm_name == 'openai':
                headers = {
                    'Authorization': f"Bearer {config['api_key']}",
                    'Content-Type': 'application/json',
                }
                data = {
                    'model': config['model'],
                    'messages': [
                        {'role': 'system', 'content': 'You are a music analysis assistant.'},
                        {'role': 'user', 'content': prompt},
                    ],
                    'max_tokens': 256,
                }
                resp = requests.post(config['endpoint'], headers=headers, json=data, timeout=30)
                resp.raise_for_status()
                text = resp.json()['choices'][0]['message']['content']
            elif llm_name == 'gemini':
                headers = {
                    'Content-Type': 'application/json',
                }
                params = {'key': config['api_key']}
                data = {
                    'contents': [
                        {'parts': [{'text': prompt}]}
                    ]
                }
                resp = requests.post(config['endpoint'], headers=headers, params=params, json=data, timeout=30)
                resp.raise_for_status()
                text = resp.json()['candidates'][0]['content']['parts'][0]['text']
            elif llm_name == 'ollama':
                data = {
                    'model': config['model'],
                    'prompt': prompt,
                    'stream': False
                }
                resp = requests.post(config['endpoint'], json=data, timeout=30)
                resp.raise_for_status()
                text = resp.json().get('response', '')
            else:
                return {'score': 5, 'suggestions': f'No API logic for {llm_name}.'}
            # Parse text for score/suggestions (simple heuristic, can be improved)
            import re
            score_match = re.search(r'score\s*[:=\-]?\s*(\d+(?:\.\d+)?)', text, re.IGNORECASE)
            score = float(score_match.group(1)) if score_match else 5
            return {'score': max(1, min(10, score)), 'suggestions': text}
        except Exception as e:
            return {'score': 5, 'suggestions': f'LLM API error for {llm_name}: {e}'}

    def store_llm_feedback(self, gen: int, individual_id: int, llm_name: str, feedback: dict):
        key = (gen, individual_id)
        if key not in self.llm_feedbacks:
            self.llm_feedbacks[key] = {}
        self.llm_feedbacks[key][llm_name] = feedback
        # Also store to disk for later analysis
        out_path = self.llm_feedback_dir / f'gen{gen}_ind{individual_id}_{llm_name}.json'
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(feedback, f, ensure_ascii=False, indent=2)

    def aggregate_llm_scores(self, feedbacks: dict) -> float:
        """
        Aggregate LLM scores (e.g., mean) for use in fitness.
        """
        scores = [fb.get('score', 5) for fb in feedbacks.values()]
        if not scores:
            return 0
        return sum(scores) / len(scores)

    def fitness_fn(self, individual: LatentVectorIndividual) -> float:
        output_path = self.output_dir / f"music_gen_{self.generation}_{id(individual)}.mid"
        try:
            self.music_generator.logger.info(f"GA: Generating for individual {id(individual)}")
            result = self.music_generator.generate(individual.vector, output_path)
            self.music_generator.logger.info(f"GA: Generation result: {result}")
            midi_path = result.get('midi_path') or result.get('output_path')
            if not midi_path or not Path(midi_path).exists():
                self.music_generator.logger.error("GA: MIDI file not created")
                individual.fitness = 0
                return 0

            evaluator = self.llm_names[0] if self.llm_names else 'music21'
            if evaluator == 'music21':
                # Use music21 analysis for fitness
                features = analyze_midi_with_music21(midi_path)
                # Feature extraction
                tempo = features.get('tempo')
                note_density = features.get('note_density')
                interval_variety = features.get('interval_variety', 0)
                chord_complexity = features.get('chord_complexity', 0)
                # Target values
                target_bpm = self.target_bpm or self.target_tempo
                mood = self.target_mood
                # Scoring
                # Tempo score (closer to target is better)
                tempo_score = max(0, 1 - abs((tempo or 0) - (target_bpm or 0)) / (target_bpm or 1))
                # Interval variety: calm prefers low, tense prefers high, neutral in between
                if mood == 'calm':
                    interval_score = max(0, 1 - (interval_variety / 12))  # prefer stepwise
                    chord_score = max(0, 1 - (chord_complexity / 8))  # prefer simple chords
                elif mood == 'tense':
                    interval_score = min(1, interval_variety / 12)  # prefer more leaps
                    chord_score = min(1, chord_complexity / 8)  # prefer complex chords
                elif mood == 'excited':
                    interval_score = min(1, interval_variety / 8)  # prefer moderate variety
                    chord_score = min(1, chord_complexity / 6)
                else:  # neutral
                    interval_score = 1 - abs(interval_variety - 6) / 6  # prefer moderate
                    chord_score = 1 - abs(chord_complexity - 4) / 4
                # Weighted sum
                fitness = 0.5 * tempo_score + 0.2 * interval_score + 0.3 * chord_score
                individual.fitness = fitness
                individual.suggestions = f"Tempo: {tempo}, IntervalVariety: {interval_variety}, ChordComplexity: {chord_complexity}"
                return fitness
            else:
                # Use LLM or other evaluator
                prompt = self.prepare_llm_prompt(midi_path)
                feedback = self.get_llm_feedback(prompt, evaluator, midi_path)
                score = feedback.get('score', 5)
                individual.fitness = score
                individual.suggestions = feedback.get('suggestions', '')
                return score
        except Exception as e:
            self.music_generator.logger.error(f"GA: Fitness function error: {e}")
            individual.fitness = 0
            individual.suggestions = str(e)
            return 0

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