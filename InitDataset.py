# Run this script to perform 5-fold stratification on the FSC22 Dataset
# As well as to define threat/target audio classes
# Ensure your filepaths match up to your personal project's specifics

import pandas as pd
from sklearn.model_selection import StratifiedKFold

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
    fsc22_audio_dir = "FSC22/Audio Wise V1.0" # Ensure this lines up with your folder structure
    fsc22_meta_path = "FSC22/Metadata/Metadata V1.0 FSC22.csv" # Ensure this lines up with your folder structure

    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=67)

    # all other classes are treated as noise

    fsc22_df = pd.read_csv(fsc22_meta_path)
    fsc22_df['Fold'] = -1
    fsc22_df['Threat'] = False
    fsc22_df['Class ID'] -= 1

    x = fsc22_df.index
    y = fsc22_df['Class Name']

    for fold_index, (train_index, test_index) in enumerate(skf.split(x, y)):
        fsc22_df.loc[test_index, 'Fold'] = fold_index

    fsc22_df['Threat'] = fsc22_df["Class Name"].isin(threat_classes)

    fsc22_df.to_csv("FSC22/Metadata/Modified_Metadata.csv")