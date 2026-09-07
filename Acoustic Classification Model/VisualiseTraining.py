import json
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

with(open('trainedModels/100epoch_SNR_50chance/training_stats.json')) as f:
    data = json.load(f)

grouped_by_fold = {}
for item in data:
    grouped_by_fold.setdefault(item['fold'], []).append(item)

for fold in grouped_by_fold:
    fold_epochs = grouped_by_fold[fold]
    acc = [d['accuracy'] for d in fold_epochs]
    loss = [d['loss'] for d in fold_epochs]
    epochs = [d['epoch'] for d in fold_epochs]

    plt.plot(epochs, acc, label=f"Fold {fold+1}")

plt.legend()
plt.xlabel("Epoch")
plt.ylabel("Accuracy")

plt.show()