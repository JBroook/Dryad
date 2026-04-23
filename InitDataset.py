# Run this script to perform 5-fold stratification on the FSC22 Dataset
# As well as to define threat/target audio classes
# Ensure your filepaths match up to your personal project's specifics
import os

import pandas as pd
import torch
import torchaudio
from sklearn.model_selection import StratifiedGroupKFold

threat_classes = [
    "Fire",
    "TreeFalling",
    "Helicopter",
    "VehicleEngine",
    "Axe",
    "Chainsaw",
    "Generator",
    "Handsaw",
    "Gunshot",
    "WoodChop"
]

if __name__=="__main__":
    # set up meta data
    fsc22_audio_dir = "FSC22/Audio Wise V1.0" # Ensure this lines up with your folder structure
    fsc22_meta_path = "FSC22/Metadata/Metadata V1.0 FSC22.csv" # Ensure this lines up with your folder structure

    sgkf = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=67)

    # all other classes are treated as noise

    fsc22_df = pd.read_csv(fsc22_meta_path)
    fsc22_df['Fold'] = -1
    fsc22_df['Threat'] = False
    fsc22_df['Class ID'] -= 1
    fsc22_df['Group'] = fsc22_df['Source File Name'].apply(lambda x: x.split('_')[0])

    x = fsc22_df.index
    y = fsc22_df['Class Name']

    for fold_index, (train_index, test_index) in enumerate(sgkf.split(fsc22_df, fsc22_df['Class ID'], groups=fsc22_df['Group'])):
        fsc22_df.loc[test_index, 'Fold'] = fold_index

    fsc22_df['Threat'] = fsc22_df["Class Name"].isin(threat_classes)

    fsc22_df.to_csv("FSC22/Metadata/Modified_Metadata.csv")

    # resample, pad or trim audio files
    for index, row in fsc22_df.iterrows():
        waveform, sample_rate = torchaudio.load(os.path.join(fsc22_audio_dir, row['Dataset File Name']))

        # resample
        if sample_rate != 32000:
            resampler = torchaudio.transforms.Resample(sample_rate, 32000)
            waveform = resampler(waveform)

        # pad/trim
        max_length = 5 * 32000
        if waveform.size(0) > max_length:
            waveform = waveform[:max_length]
        else:
            pad_size = max_length - waveform.size(0)
            waveform = torch.nn.functional.pad(waveform, (0, pad_size))

        torchaudio.save(os.path.join("FSC22/ModifiedAudio", row['Dataset File Name']), waveform, 32000)