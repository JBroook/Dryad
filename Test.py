import os

import numpy as np
import pandas as pd

df = pd.read_csv("FSC22/Metadata/SED_Metadata.csv")
row = df.iloc[0]

og_df = pd.read_csv("FSC22/Metadata/Modified_Metadata.csv")
og_df.drop_duplicates(subset=['Class Name'])
name_to_id = dict(zip(og_df['Class Name'], og_df['Class ID']))
label_matrix = np.zeros((1000, 27), dtype=np.float32)

with open(
        os.path.join(
            "FSC22/SyntheticSoundscapes" + f"/Fold{row['Fold']}", row['Label File Path']
        ), "r", encoding="utf-8") as file:
    for line in file:
        t = str(line.strip())
        if t!="":
            info = t.split("	")
            start_frame = int(float(info[0])/0.01)
            end_frame = int(float(info[1])/0.01)
            target_class = name_to_id[info[2]]

            label_matrix[start_frame:end_frame, target_class] = 1