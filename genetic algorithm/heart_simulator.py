import random
import time

class HeartbeatSimulator:
    def __init__(self, min_bpm=60, max_bpm=140, variation=5, update_interval=5):
        """
        :param min_bpm: minimum BPM
        :param max_bpm: maksimum BPM
        :param variation: bir önceki BPM'e göre olası sapma miktarı
        :param update_interval: yeni BPM oluşturma süresi (saniye)
        """
        self.min_bpm = min_bpm
        self.max_bpm = max_bpm
        self.variation = variation
        self.update_interval = update_interval
        self.current_bpm = random.randint(min_bpm, max_bpm)
        self.last_update_time = time.time()

    def read_bpm(self):
        now = time.time()
        if now - self.last_update_time >= self.update_interval:
            change = random.randint(-self.variation, self.variation)
            self.current_bpm = max(self.min_bpm, min(self.max_bpm, self.current_bpm + change))
            self.last_update_time = now
        return self.current_bpm
