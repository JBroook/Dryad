import tkinter as tk
import threading
import queue
from tkinter import ttk

import numpy as np
import sounddevice as sd
import torch
import pandas as pd
import torch.nn as nn
from models import Cnn10

# ==============================
# EDIT HERE
# ==============================

MODEL_PATH = "trainedModels/100epoch_SNR_50chance/fold0_checkpoint_epoch200.pth"

# extract class names

df = pd.read_csv("FSC22/Metadata/Modified_Metadata.csv")

# filter out non-threat classes
df = df[df['Threat']].reset_index(drop=True)
# reset class IDs to be in continuous range
df['Class ID'] = pd.factorize(df['Class Name'])[0]

unique_pairs = df.drop_duplicates(subset=["Class ID"])


CLASS_NAMES = [None]*10

for _, row in unique_pairs.iterrows():
    idx = int(row['Class ID'])
    if 0 <= idx <= 10:
        CLASS_NAMES[idx] = row['Class Name']

SAMPLE_RATE = 32000
WINDOW_SECONDS = 5

# ==============================


# Load model
model = Cnn10(
        sample_rate=32000,
        window_size=1024,
        hop_size=320,
        mel_bins=64,
        fmin=50,
        fmax=14000,
        classes_num=50
    )
model.fc_audioset = nn.Linear(512, 10, bias=True)
checkpoint = torch.load(MODEL_PATH, map_location="cpu")
model.load_state_dict(checkpoint["model_state_dict"])
model.eval()

torch.set_num_threads(1)

# Queues
audio_queue = queue.Queue()
result_queue = queue.Queue()
volume_queue = queue.Queue()

# ==============================
# AUDIO CALLBACK
# ==============================

def audio_callback(indata, frames, time, status):
    if status:
        print(status)

    audio_queue.put(indata.copy())

    # calculate volume
    volume = np.sqrt(np.mean(indata**2))

    volume_queue.put(volume)


# ==============================
# MODEL PREDICTION
# ==============================

def predict(audio):

    waveform = torch.tensor(audio).float()

    # PANN expects shape: [batch, samples]
    if waveform.abs().max() > 1:
        waveform = waveform / waveform.abs().max()
    waveform = waveform.unsqueeze(0)

    # waveform = waveform - waveform.mean()
    # waveform = waveform / (waveform.std() + 1e-6)

    with torch.no_grad():
        output = model(waveform)

    output = output["clipwise_output"]

    conf, pred = torch.max(output, dim=1)

    return pred.item(), conf.item(), output.squeeze().tolist()

# ==============================
# BACKGROUND INFERENCE LOOP
# ==============================

def inference_loop():

    buffer = np.zeros(SAMPLE_RATE * WINDOW_SECONDS)

    while True:

        audio = audio_queue.get().flatten()

        buffer = np.concatenate((buffer, audio))
        buffer = buffer[-SAMPLE_RATE * WINDOW_SECONDS:]

        pred, conf, probs = predict(buffer)

        result_queue.put((pred, conf, probs))


# ==============================
# TKINTER UI
# ==============================

root = tk.Tk()
root.title("Real-Time Audio Classifier")
root.geometry("350x250")

title = tk.Label(
    root,
    text="Listening...",
    font=("Arial", 18)
)

title.pack(pady=20)

prediction_label = tk.Label(
    root,
    text="Prediction: -",
    font=("Arial", 16)
)

prediction_label.pack()

confidence_label = tk.Label(
    root,
    text="Confidence: -",
    font=("Arial", 14)
)

confidence_label.pack(pady=10)

volume_bar = ttk.Progressbar(
    root,
    orient="horizontal",
    length=200,
    mode="determinate"
)

volume_bar.pack(pady=10)

bars = []

for name in CLASS_NAMES:
    lbl = tk.Label(root, text=f"{name}: 0.00")
    lbl.pack()
    bars.append(lbl)


# ==============================
# UI UPDATE LOOP
# ==============================

def update_ui():

    try:
        pred, conf, probs = result_queue.get_nowait()

        prediction_label.config(
            text=f"Prediction: {CLASS_NAMES[pred]}"
        )

        confidence_label.config(
            text=f"Confidence: {conf:.2f}"
        )

    except queue.Empty:
        pass

    try:
        volume = volume_queue.get_nowait()

        # scale value for progress bar
        volume_bar["value"] = min(volume * 500, 100)

    except queue.Empty:
        pass

    root.after(50, update_ui)


# ==============================
# START AUDIO STREAM
# ==============================

stream = sd.InputStream(
    device=3,
    samplerate=SAMPLE_RATE,
    channels=1,
    blocksize=SAMPLE_RATE//4,
    callback=audio_callback
)

print(sd.query_devices())
stream.start()

# Start inference thread
threading.Thread(
    target=inference_loop,
    daemon=True
).start()

# Start UI updates
update_ui()

root.mainloop()