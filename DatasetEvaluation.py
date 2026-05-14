import os
import matplotlib.pyplot as plt
import pandas as pd

fsc22_meta_path = "FSC22/Metadata/Modified_Metadata.csv"
df = pd.read_csv(fsc22_meta_path)

# shows proportion of clips per fold
def clip_per_fold():
    fold_count = df['Fold'].value_counts()

    plt.bar([0, 1, 2, 3, 4], fold_count, label="Unfiltered")

    fold_count_filtered = df[df['Threat']]['Fold'].value_counts()

    plt.bar([0, 1, 2, 3, 4], fold_count_filtered, label="Non-threat classes filtered out")
    plt.xlabel('Fold')
    plt.ylabel('Number of Clips')
    plt.legend()

# shows proportion of class per fold
def class_per_fold():
    classes_per_fold = df.groupby('Fold')['Class Name'].nunique()

    plt.bar([0, 1, 2, 3, 4], classes_per_fold, label="Unfiltered")

    # fold_count_filtered = df[df['Threat']]['Fold'].value_counts()
    #
    # plt.bar([0, 1, 2, 3, 4], fold_count_filtered, label="Non-threat classes filtered out")
    plt.xlabel('Fold')
    plt.ylabel('Number of Clips')
    plt.legend()

# shows amount of clips per class
def clips_per_class():
    for fold in range(5):
        df = pd.read_csv(fsc22_meta_path)
        df = df[df['Threat']]
        df = df[df['Fold'] == fold]

        counts = df['Class Name'].value_counts().sort_index()
        plt.plot(counts.values, label=f"Fold {fold}")

    plt.legend()
    plt.ylabel("Clip count per class (sorted index)")

clip_per_fold()
plt.show()