import time
from heart_simulator import HeartbeatSimulator
from ga_core import generate_initial_population, select_best, crossover_and_mutate
from player import play_midi

def main_loop():
    simulator = HeartbeatSimulator(min_bpm=60, max_bpm=130, variation=3, update_interval=5)
    population = generate_initial_population()

    generation = 1
    while True:
        bpm = simulator.read_bpm()
        print(f"\n🎵 [GENERATION {generation}] Simulated BPM: {bpm}")

        # En uygun melodileri seç
        selected = select_best(population, bpm)
        best_midi = selected[0][0]

        print(f"[INFO] Playing best candidate MIDI: {best_midi}")
        play_midi(best_midi)

        # Yeni jenerasyon oluştur
        population = crossover_and_mutate([m for m, _ in selected])
        generation += 1

        time.sleep(10)  # her döngüde 10 saniye bekleyerek gerçek zamanlı simülasyon gibi

if __name__ == "__main__":
    main_loop()
