
import numpy as np
from sklearn.metrics import (
    accuracy_score,
    roc_auc_score,
    classification_report
)

data = np.load(
    "trainedModels/26_class_ac/roc_evaluation/roc_predictions.npz"
)

y_true = data["y_true"]
y_probs = data["y_probs"]
y_pred = np.argmax(y_probs, axis=1)

num_classes = y_probs.shape[1]

print("Prediction diagnostics")
print("======================")
print(f"Samples: {len(y_true)}")
print(f"Classes: {num_classes}")
print(f"Accuracy: {accuracy_score(y_true, y_pred) * 100:.2f}%")
print(f"Probability sums: {y_probs.sum(axis=1).min():.6f} - {y_probs.sum(axis=1).max():.6f}")
print(f"Probability range: {y_probs.min():.6f} - {y_probs.max():.6f}")

y_true_bin = np.eye(num_classes)[y_true]

micro_auc = roc_auc_score(
    y_true_bin.ravel(),
    y_probs.ravel()
)

macro_auc = roc_auc_score(
    y_true,
    y_probs,
    multi_class="ovr",
    average="macro"
)

print("\nROC AUC")
print("=======")
print(f"Micro AUC: {micro_auc:.6f}")
print(f"Macro AUC: {macro_auc:.6f}")

print("\nPer-class ROC AUC")
print("=================")

class_aucs = []

for c in range(num_classes):

    binary_targets = (y_true == c).astype(int)

    if len(np.unique(binary_targets)) < 2:
        print(f"Class {c}: Missing positive or negative samples")
        continue

    auc = roc_auc_score(
        binary_targets,
        y_probs[:, c]
    )

    class_aucs.append(auc)

    print(
        f"Class {c:02d}: "
        f"AUC = {auc:.4f} | "
        f"Samples = {binary_targets.sum()}"
    )

print("\nMean per-class AUC:", np.mean(class_aucs))

print("\nClassification report")
print("=====================")

print(classification_report(
    y_true,
    y_pred,
    zero_division=0
))
