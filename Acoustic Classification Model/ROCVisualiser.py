import os
import random

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F
import torchaudio
import matplotlib.pyplot as plt

from torch.utils.data import Dataset, DataLoader
from sklearn.metrics import roc_curve, auc

from models import Cnn10

fsc22_audio_dir = "FSC22/ModifiedAudio"
fsc22_meta_path = "FSC22/Metadata/Modified_Metadata.csv"

device = "cuda" if torch.cuda.is_available() else "cpu"

CFG = {
    "training_name": "26_class_ac/",
    "all_folds": [0, 1, 2, 3, 4],
    "batch_size": 32,
    "seed": 42,
    "model_name": "Cnn10",
    "checkpoints": {
        "Cnn10": "Cnn10_mAP=0.380.pth",
    },
    "sample_rate": 32000,
    "clip_seconds": 5,
}


class FSC22Dataset(Dataset):
    class_count = 26

    def __init__(self, fsc22_meta, fold):
        self.audio_dir = fsc22_audio_dir
        self.target_len = CFG["sample_rate"] * CFG["clip_seconds"]

        self.meta_df = pd.read_csv(fsc22_meta)
        self.meta_df = self.meta_df[
            self.meta_df["_Fold"] == fold
        ].reset_index(drop=True)

    def __len__(self):
        return len(self.meta_df)

    def _fix_length(self, waveform):
        n = self.target_len
        if waveform.shape[0] < n:
            waveform = F.pad(waveform, (0, n - waveform.shape[0]))
        elif waveform.shape[0] > n:
            waveform = waveform[:n]
        return waveform

    def __getitem__(self, item):
        row = self.meta_df.iloc[item]
        waveform, _ = torchaudio.load(
            os.path.join(self.audio_dir, row["Dataset File Name"])
        )
        waveform = waveform.mean(dim=0)
        waveform = self._fix_length(waveform)

        peak = waveform.abs().max()
        if peak > 1:
            waveform = waveform / peak

        return waveform, int(row["Class ID"])


def set_seed(seed):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def build_model(num_classes):
    name = CFG["model_name"]
    cls = {"Cnn10": Cnn10}.get(name)
    if cls is None:
        raise ValueError(f"Unsupported model: {name}")

    model = cls(
        sample_rate=CFG["sample_rate"],
        window_size=1024,
        hop_size=320,
        mel_bins=64,
        fmin=50,
        fmax=14000,
        classes_num=527,
    )

    in_features = model.fc_audioset.in_features
    model.fc_audioset = nn.Linear(in_features, num_classes, bias=True)
    return model.to(device)


def load_fold_model(fold):
    checkpoint_path = os.path.join(
        f"trainedModels/{CFG['training_name']}",
        f"fold_{fold}",
        "checkpoint_epoch50.pth",
    )

    if not os.path.exists(checkpoint_path):
        raise FileNotFoundError(f"Checkpoint not found: {checkpoint_path}")

    model = build_model(FSC22Dataset.class_count)
    checkpoint = torch.load(checkpoint_path, map_location=device, weights_only=False)
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()

    print(f"Loaded fold {fold} checkpoint (epoch {checkpoint['epoch']})")
    return model


@torch.no_grad()
def evaluate_fold(fold, worker_count=0):
    print(f"\nEvaluating fold {fold}...")
    model = load_fold_model(fold)
    dataset = FSC22Dataset(fsc22_meta_path, fold=fold)

    if len(dataset) == 0:
        raise ValueError(f"No samples found in fold {fold}")

    loader = DataLoader(
        dataset,
        batch_size=CFG["batch_size"],
        shuffle=False,
        num_workers=worker_count,
        pin_memory=device == "cuda",
    )

    all_targets = []
    all_probs = []

    for inputs, labels in loader:
        inputs = inputs.to(device, non_blocking=True)
        logits = model(inputs)["logits"]
        probabilities = torch.softmax(logits, dim=1)

        all_targets.extend(labels.numpy())
        all_probs.extend(probabilities.cpu().numpy())

    all_targets = np.asarray(all_targets, dtype=np.int64)
    all_probs = np.asarray(all_probs, dtype=np.float32)

    del model
    if device == "cuda":
        torch.cuda.empty_cache()

    return all_targets, all_probs


def evaluate_cv_roc(save_path):
    num_classes = FSC22Dataset.class_count
    mean_fpr = np.linspace(0, 1, 100)

    fold_macro_tprs = []
    fold_macro_aucs = []

    # Store all per-class predictions across all folds to plot per-class lines
    all_y_true = []
    all_y_probs = []

    for fold in CFG["all_folds"]:
        targets, probs = evaluate_fold(fold)
        all_y_true.append(targets)
        all_y_probs.append(probs)

        y_true_bin = np.eye(num_classes)[targets]

        # Calculate macro ROC curve for THIS fold independently
        class_tprs = []
        class_aucs = []

        for c in range(num_classes):
            if len(np.unique(y_true_bin[:, c])) < 2:
                continue
            fpr_c, tpr_c, _ = roc_curve(y_true_bin[:, c], probs[:, c])
            interp_tpr = np.interp(mean_fpr, fpr_c, tpr_c)
            interp_tpr[0] = 0.0
            class_tprs.append(interp_tpr)
            class_aucs.append(auc(fpr_c, tpr_c))

        fold_macro_tpr = np.mean(class_tprs, axis=0)
        fold_macro_tpr[-1] = 1.0
        fold_macro_auc = auc(mean_fpr, fold_macro_tpr)

        fold_macro_tprs.append(fold_macro_tpr)
        fold_macro_aucs.append(fold_macro_auc)

        print(f"Fold {fold} Macro-AUC: {fold_macro_auc:.4f}")

    # Plotting
    fig, ax = plt.subplots(figsize=(10, 8))

    # 1. Plot individual per-fold macro curves (faded)
    for i, (tpr, auc_val) in enumerate(zip(fold_macro_tprs, fold_macro_aucs)):
        ax.plot(
            mean_fpr,
            tpr,
            alpha=0.3,
            linestyle="--",
            label=f"Fold {i} (AUC = {auc_val:.4f})",
        )

    # 2. Mean Macro ROC across folds
    mean_tpr = np.mean(fold_macro_tprs, axis=0)
    mean_tpr[-1] = 1.0
    mean_auc = auc(mean_fpr, mean_tpr)
    std_auc = np.std(fold_macro_aucs)

    ax.plot(
        mean_fpr,
        mean_tpr,
        color="b",
        linewidth=2.5,
        label=f"Mean Macro-average (AUC = {mean_auc:.4f} $\\pm$ {std_auc:.4f})",
    )

    # 3. Variance band (+/- 1 std) across folds
    std_tpr = np.std(fold_macro_tprs, axis=0)
    tprs_upper = np.minimum(mean_tpr + std_tpr, 1)
    tprs_lower = np.maximum(mean_tpr - std_tpr, 0)
    ax.fill_between(
        mean_fpr,
        tprs_lower,
        tprs_upper,
        color="grey",
        alpha=0.2,
        label=r"$\pm$ 1 std. dev.",
    )

    ax.plot([0, 1], [0, 1], color="red", linestyle="--", label="Random Classifier")

    ax.set_xlim([0.0, 1.0])
    ax.set_ylim([0.0, 1.05])
    ax.set_xlabel("False Positive Rate", fontsize=12)
    ax.set_ylabel("True Positive Rate", fontsize=12)
    ax.set_title(
        "FSC22 26-Class Cross-Validated Macro ROC Curve", fontsize=14
    )
    ax.legend(loc="lower right", fontsize=10)
    ax.grid(linestyle="--", alpha=0.5)

    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches="tight")
    plt.show()

    print("\n--- Summary Results ---")
    print(f"5-Fold Mean Macro-AUC: {mean_auc:.4f} +/- {std_auc:.4f}")


def main():
    set_seed(CFG["seed"])
    print("Device:", device)
    print("Model:", CFG["model_name"])

    output_dir = os.path.join(f"trainedModels/{CFG['training_name']}", "roc_evaluation")
    os.makedirs(output_dir, exist_ok=True)

    evaluate_cv_roc(
        save_path=os.path.join(output_dir, "fsc22_cv_roc_curve.png")
    )


if __name__ == "__main__":
    main()