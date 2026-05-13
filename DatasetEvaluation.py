import os
import matplotlib.pyplot as plt
import pandas as pd

fsc22_meta_path = "FSC22/Metadata/Modified_Metadata.csv"
df = pd.read_csv(fsc22_meta_path)

fold_count = df['Fold'].value_counts()

plt.bar([0, 1, 2, 3, 4], fold_count, label="Unfiltered")

fold_count_filtered = df[df['Threat']]['Fold'].value_counts()

plt.bar([0, 1, 2, 3, 4], fold_count_filtered, label="Non-threat classes filtered out")
plt.xlabel('Fold')
plt.ylabel('Number of Clips')
plt.legend()

plt.show()