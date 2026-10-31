import os

import numpy as np
import pandas as pd
import torch

df = pd.read_csv("../FSC22/Metadata/SED_Metadata.csv")

og_df = pd.read_csv("../FSC22/Metadata/Modified_Metadata.csv")
og_df = og_df.drop_duplicates(subset=['Class Name'])
name_to_id = dict(zip(og_df['Class Name'], og_df['Class ID']))
label_matrix = np.zeros((344, 27), dtype=np.float32)

df["Label Tensor Path"] = ""

for index, row in df.iterrows():
    with open(
            os.path.join(
                "FSC22/SyntheticSoundscapes" + f"/Fold{row['Fold']}", row['Label File Path']
            ), "r", encoding="utf-8") as file:
        for line in file:
            t = str(line.strip())
            if t!="":
                info = t.split("	")
                start_frame = int(float(info[0])/0.08)
                end_frame = int(float(info[1])/0.08)
                target_class = name_to_id[info[2]]

                label_matrix[start_frame:end_frame, target_class] = 1

    new_path = row['Label File Path'].replace(".txt", "_label_matrix.pt")
    df.loc[index, "Label Tensor Path"] = new_path
    tensor = torch.from_numpy(label_matrix)
    torch.save(tensor, os.path.join(
                "FSC22/SyntheticSoundscapes" + f"/Fold{row['Fold']}", new_path
            ))

df.to_csv("FSC22/Metadata/SED_Metadata.csv", index=False)
print("Label tensors generated successfully")