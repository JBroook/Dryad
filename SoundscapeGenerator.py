import math
import shutil

import scaper
import numpy as np
import os
from pathlib import Path
import pandas as pd
import torchaudio

import warnings
warnings.filterwarnings("ignore")

# Separate modified audio into background and foreground
modified_audio = Path("FSC22/CategorisedAudio")

bg_sounds = ["Rain", "Thunderstorm", "Wind", "Silence"]
fg_sounds = [
    "Axe", "BirdChirping", "Chainsaw", "Clapping",
    "Fire","Firework", "Footsteps", "Frog",
    "Generator", "Gunshot","Handsaw", "Helicopter",
    "Insect", "Lion", "Speaking", "Squirrel",
    "TreeFalling",   "VehicleEngine",  "WaterDrops", "Whistling",
    "WingFlaping", "WolfHowl", "WoodChop"
]

if not modified_audio.is_dir():
    Path("FSC22/CategorisedAudio").mkdir(parents=True, exist_ok=True)
    fsc22_audio_dir = "FSC22/Audio Wise V1.0"
    fsc22_meta_path = "FSC22/Metadata/Modified_Metadata.csv"

    df = pd.read_csv(fsc22_meta_path)

    for index, row in df.iterrows():
        section = "Background" if row['Class Name'] in bg_sounds else "Foreground"
        path_string = "FSC22/CategorisedAudio/"+"Fold"+str(row['Fold'])+"/"

        if not Path(path_string+row['Class Name']).is_dir():
            Path(path_string+section+"/"+row['Class Name']).mkdir(parents=True, exist_ok=True)
            path_string += section+"/"+row['Class Name']

        waveform, sample_rate = torchaudio.load(os.path.join(fsc22_audio_dir, row['Dataset File Name']))

        # resamples all audio clips to same sample rate
        if sample_rate != 32000:
            resampler = torchaudio.transforms.Resample(sample_rate, 32000)
            waveform = resampler(waveform)

        max_length = 10 * 32000
        if waveform.size(1) >= max_length:  # trim
            waveform = waveform[:, :max_length]
        elif section=="Background":  # pad background audio by repeating
            repeat_count = int(math.ceil(max_length / waveform.size(1)))
            waveform = waveform.repeat(1, repeat_count)
            waveform = waveform[:, :max_length]

        torchaudio.save(os.path.join(path_string,
                                     row['Dataset File Name']), waveform, 32000)

    print("Separated audio into 5 folds...")
    print("Resampled, trimmed, and padded audio...")

# SCAPER SETTINGS
ref_db = -50
duration = 10.0

min_events = 1
max_events = 9

event_time_dist = 'truncnorm'
event_time_mean = 5.0
event_time_std = 2.0
event_time_min = 0.0
event_time_max = 10.0

source_time_dist = 'const'
source_time = 0.0

event_duration_dist = 'uniform'
event_duration_min = 0.5
event_duration_max = 4.0

snr_dist = 'uniform'
snr_min = 6
snr_max = 30

pitch_dist = 'uniform'
pitch_min = -3.0
pitch_max = 3.0

time_stretch_dist = 'uniform'
time_stretch_min = 0.8
time_stretch_max = 1.2

def generate(fold, amount, seed=123, repeat=False):
    if fold==0:
        fg_sounds.remove("Fire")

    # OUTPUT FOLDER
    outfolder = f'FSC22/SyntheticSoundscapes/Fold{fold}'
    # INPUT FOLDERS
    fg_folder = f'FSC22/CategorisedAudio/Fold{fold}/Foreground/'
    bg_folder = f'FSC22/CategorisedAudio/Fold{fold}/Background/'
    # create a scaper that will be used below
    sc = scaper.Scaper(duration, fg_folder, bg_folder, random_state=seed)
    sc.protected_labels = []
    sc.ref_db = ref_db

    # Generate 1000 soundscapes using a truncated normal distribution of start times
    keep_index = False
    if Path("FSC22/Metadata/SED_Metadata.csv").exists():
        soundscape_df = pd.read_csv("FSC22/Metadata/SED_Metadata.csv")
    else:
        keep_index = True
        soundscape_df = pd.DataFrame(columns=["Audio File Path", "JAMS File Path", "Label File Path", "Fold"])

    for n in range(amount):

        print('Generating soundscape: {:d}/{:d}'.format(n+1, amount))

        # reset the event specifications for foreground and background at the
        # beginning of each loop to clear all previously added events
        sc.reset_bg_event_spec()
        sc.reset_fg_event_spec()

        # add background
        sc.add_background(label=('choose', bg_sounds),
                          source_file=('choose', []),
                          source_time=('const', 0))

        # add random number of foreground events
        n_events = np.random.randint(min_events, max_events+1)
        for _ in range(n_events):
            sc.add_event(label=('choose', fg_sounds),
                         source_file=('choose', []),
                         source_time=(source_time_dist, source_time),
                         event_time=(event_time_dist, event_time_mean, event_time_std, event_time_min, event_time_max),
                         event_duration=(event_duration_dist, event_duration_min, event_duration_max),
                         snr=(snr_dist, snr_min, snr_max),
                         pitch_shift=(pitch_dist, pitch_min, pitch_max),
                         time_stretch=(time_stretch_dist, time_stretch_min, time_stretch_max))

        # generate
        if not Path("FSC22/SyntheticSoundscapes").is_dir():
            Path("FSC22/SyntheticSoundscapes").mkdir(parents=True, exist_ok=True)

        if not Path(outfolder).is_dir():
            Path(outfolder).mkdir(parents=True, exist_ok=True)

        audiofile = os.path.join(outfolder+"/", "soundscape_unimodal{:d}.wav".format(n))
        jamsfile = os.path.join(outfolder+"/", "soundscape_unimodal{:d}.jams".format(n))
        txtfile = os.path.join(outfolder+"/", "soundscape_unimodal{:d}.txt".format(n))

        soundscape_df.loc[len(soundscape_df)] = {
            "Audio File Path" : "soundscape_unimodal{:d}.wav".format(n),
            "JAMS File Path" : "soundscape_unimodal{:d}.jams".format(n),
            "Label File Path" : "soundscape_unimodal{:d}.txt".format(n),
            "Fold" : fold
        }

        sc.generate(audiofile, jamsfile,
                    allow_repeated_label=True,
                    allow_repeated_source=repeat,
                    reverb=0.1,
                    disable_sox_warnings=True,
                    no_audio=False,
                    txt_path=txtfile)

    soundscape_df.to_csv("FSC22/Metadata/SED_Metadata.csv", index=keep_index)

if __name__=='__main__':
    i = 2
    repeat = False
    while i<5:
        try:
            generate(i, 400, repeat=repeat)
            i += 1
            repeat = False
        except Exception as e:
            print(e)
            print("Retrying by repeating sample clips")
            repeat = True
            shutil.rmtree(f'FSC22/SyntheticSoundscapes/Fold{i}')