# app.py
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import os

from heart_simulator import HeartbeatSimulator
from ga_core import generate_initial_population, select_best, crossover_and_mutate
from player import midi_to_wav
from vae_generator import generate_trio, save_sequence_as_midi


import note_seq
import random

app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Global durum
simulator = HeartbeatSimulator()
generation = 0
population = generate_initial_population()
current_wav = None

OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/status")
def status():
    global current_wav, generation
    return {
        "bpm": simulator.read_bpm(),
        "generation": generation,
        "wav_url": f"/output/{os.path.basename(current_wav)}" if current_wav else None
    }

@app.post("/generate")
def generate():
    global generation, current_wav, population

    bpm = simulator.read_bpm()
    selected = select_best(population, bpm)
    best_seq = selected[0][0]

    midi_path = os.path.join(OUTPUT_DIR, f"gen_{generation}.mid")
    wav_path = os.path.join(OUTPUT_DIR, f"gen_{generation}.wav")

    save_sequence_as_midi(best_seq, midi_path)
    midi_to_wav(midi_path, wav_path)

    current_wav = wav_path
    generation += 1

    population = crossover_and_mutate([s[0] for s in selected])
    return {"status": "ok"}

@app.get("/output/{file_name}")
def get_output(file_name: str):
    return FileResponse(os.path.join(OUTPUT_DIR, file_name))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
