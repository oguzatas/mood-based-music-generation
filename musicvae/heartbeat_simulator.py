"""
Heartbeat Simulator Module
-------------------------
Simulates heartbeat RR interval data for different moods.
Designed for easy extension and integration with real data sources.

Author: MusicVAE Generator Team
License: MIT
"""
from typing import List
import numpy as np

class HeartbeatSimulator:
    """Simulates heartbeat RR intervals for different moods."""
    def __init__(self, seed: int = None):
        self.rng = np.random.default_rng(seed)

    def simulate(self, mood: str, length: int = 60) -> List[float]:
        """
        Generate simulated RR intervals (ms) for a given mood.
        Args:
            mood: 'calm', 'excited', 'tense', 'neutral'
            length: number of heartbeats
        Returns:
            List of RR intervals in milliseconds
        """
        params = self._get_mood_params(mood)
        rr_intervals = self.rng.normal(loc=params['mean_rr'], scale=params['std_rr'], size=length)
        rr_intervals = np.clip(rr_intervals, 400, 2000)  # physiological limits
        return rr_intervals.tolist()

    def _get_mood_params(self, mood: str) -> dict:
        """Return mean and std RR interval for a given mood."""
        mood_map = {
            'calm':    {'mean_rr': 900, 'std_rr': 30},   # ~67 BPM
            'excited': {'mean_rr': 600, 'std_rr': 60},   # ~100 BPM
            'tense':   {'mean_rr': 700, 'std_rr': 120},  # ~85 BPM
            'neutral': {'mean_rr': 800, 'std_rr': 50},   # ~75 BPM
        }
        if mood not in mood_map:
            raise ValueError(f"Unsupported mood: {mood}")
        return mood_map[mood]

if __name__ == "__main__":
    simulator = HeartbeatSimulator(seed=42)
    for mood in ['calm', 'excited', 'tense', 'neutral']:
        rr = simulator.simulate(mood, length=10)
        print(f"Mood: {mood}, RR intervals (ms): {rr}") 