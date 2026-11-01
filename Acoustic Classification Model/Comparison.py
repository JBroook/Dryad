import pandas as pd

fsc22_meta_path = "FSC22/Metadata/Modified_Metadata.csv"
esc50_meta_path = "ESC-50/meta/esc50.csv"

fsc22_df = pd.read_csv(fsc22_meta_path)
fsc22_df = fsc22_df.drop_duplicates(subset=['Class Name'])
esc50_df = pd.read_csv(esc50_meta_path)

print(fsc22_df[["Class ID", "Class Name"]])

print("-")

print(esc50_df["category"].drop_duplicates().to_list())