import os

import pandas as pd
import torch
import torchaudio
from torchlibrosa.stft import Spectrogram, LogmelFilterBank

df = pd.read_csv("FSC22/Metadata/SED_Metadata.csv")
audio_dir = "FSC22/SyntheticSoundscapes"

sample_rate=32000
window_size=1024
hop_size=320
mel_bins=64
fmin=50
fmax=14000
window = 'hann'
center = True
pad_mode = 'reflect'
ref = 1.0
amin = 1e-10
top_db = None

spectrogram_extractor = Spectrogram(n_fft=window_size, hop_length=hop_size,
            win_length=window_size, window=window, center=center, pad_mode=pad_mode,
            freeze_parameters=True)

logmel_extractor = LogmelFilterBank(sr=sample_rate, n_fft=window_size,
    n_mels=mel_bins, fmin=fmin, fmax=fmax, ref=ref, amin=amin, top_db=top_db,
    freeze_parameters=True)

df["Audio Tensor Path"] = ""

for index, row in df.iterrows():
    waveform, sample_rate = torchaudio.load(
        os.path.join(audio_dir + f"/Fold{row['Fold']}", row['Audio File Path'])
    )

    waveform = waveform.mean(dim=0)

    if waveform.abs().max() > 1:
        waveform = waveform / waveform.abs().max()

    waveform = waveform.unsqueeze(0)

    waveform = spectrogram_extractor(waveform)
    waveform = logmel_extractor(waveform)

    waveform = waveform.squeeze(0)


    new_path = row['Label File Path'].replace(".txt", "_tensor.pt")
    df.loc[index, "Audio Tensor Path"] = new_path
    torch.save(waveform, os.path.join(
        "FSC22/SyntheticSoundscapes" + f"/Fold{row['Fold']}", new_path
    ))


df.to_csv("FSC22/Metadata/SED_Metadata.csv", index=False)
print("Audio file tensors generated successfully")