import os
import random
import inspect
from pathlib import Path

import seaborn
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F
import torchaudio

from sklearn.manifold import TSNE
from sklearn.preprocessing import normalize
from torch.utils.data import DataLoader, Dataset

from models import Cnn10


CFG = {
    "audio_dir": "FSC22/ModifiedAudio",
    "metadata_path": "FSC22/Metadata/Modified_Metadata.csv",
    "training_dir": "trainedModels/26_class_ac",
    "pretrained_checkpoint": "Cnn10_mAP=0.380.pth",
    "output_dir": "tsne_visualisations",
    "folds": [0, 1, 2, 3, 4],
    "num_classes": 26,
    "sample_rate": 32000,
    "clip_seconds": 5,
    "batch_size": 32,
    "num_workers": 0,
    "perplexity": 30,
    "iterations": 1500,
    "random_state": 42,
    "normalise_embeddings": True,
    "mark_misclassified": True,
}

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


def set_seed(seed):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


class FSC22EvaluationDataset(Dataset):
    def __init__(self, metadata_path, audio_dir, fold):
        self.audio_dir = Path(audio_dir)
        self.target_length = CFG["sample_rate"] * CFG["clip_seconds"]

        metadata = pd.read_csv(metadata_path)
        self.metadata = metadata[metadata["Fold"] == fold].reset_index(drop=True)

        if self.metadata.empty:
            raise ValueError(f"No metadata rows found for Fold={fold}.")

    def __len__(self):
        return len(self.metadata)

    def __getitem__(self, index):
        row = self.metadata.iloc[index]
        audio_path = self.audio_dir / str(row["Dataset File Name"])

        waveform, _ = torchaudio.load(str(audio_path))
        waveform = waveform.mean(dim=0)

        if waveform.numel() < self.target_length:
            waveform = F.pad(waveform, (0, self.target_length - waveform.numel()))
        elif waveform.numel() > self.target_length:
            waveform = waveform[:self.target_length]

        peak = waveform.abs().max()
        if peak > 1:
            waveform = waveform / peak

        label = int(row["Class ID"])
        file_name = str(row["Dataset File Name"])

        return waveform, label, file_name


def build_model(checkpoint_path):
    model = Cnn10(
        sample_rate=CFG["sample_rate"],
        window_size=1024,
        hop_size=320,
        mel_bins=64,
        fmin=50,
        fmax=14000,
        classes_num=527,
    )

    pretrained = torch.load(
        CFG["pretrained_checkpoint"],
        map_location=DEVICE,
        weights_only=False,
    )
    model.load_state_dict(pretrained["model"])

    in_features = model.fc_audioset.in_features
    model.fc_audioset = nn.Linear(
        in_features,
        CFG["num_classes"],
        bias=True,
    )

    checkpoint = torch.load(
        checkpoint_path,
        map_location=DEVICE,
        weights_only=False,
    )

    if "model_state_dict" not in checkpoint:
        raise KeyError(f"{checkpoint_path} does not contain 'model_state_dict'.")

    model.load_state_dict(checkpoint["model_state_dict"], strict=True)
    model.to(DEVICE)
    model.eval()

    return model


@torch.no_grad()
def extract_embeddings(model, loader):
    captured_embeddings = []

    def capture_classifier_input(module, inputs):
        captured_embeddings.append(inputs[0].detach())

    hook = model.fc_audioset.register_forward_pre_hook(capture_classifier_input)

    all_embeddings = []
    all_logits = []
    all_labels = []
    all_files = []

    try:
        for batch_index, (waveforms, labels, file_names) in enumerate(loader):
            waveforms = waveforms.to(DEVICE, non_blocking=True)

            captured_embeddings.clear()
            output = model(waveforms)

            if not isinstance(output, dict) or "logits" not in output:
                raise RuntimeError("The model forward pass did not return 'logits'.")

            if len(captured_embeddings) != 1:
                raise RuntimeError("Expected fc_audioset to be called exactly once.")

            embeddings = captured_embeddings[0]
            logits = output["logits"]

            embeddings = embeddings.reshape(embeddings.shape[0], -1)

            all_embeddings.append(embeddings.cpu().numpy())
            all_logits.append(logits.cpu().numpy())
            all_labels.append(labels.numpy())
            all_files.extend(list(file_names))

            if (batch_index + 1) % 10 == 0:
                print(f"    Processed {batch_index + 1}/{len(loader)} batches")

    finally:
        hook.remove()

    return (
        np.concatenate(all_embeddings, axis=0),
        np.concatenate(all_logits, axis=0),
        np.concatenate(all_labels, axis=0),
        all_files,
    )


def get_class_names(metadata_path):
    metadata = pd.read_csv(metadata_path)

    for column in ("Class Name", "Class_Name", "Class"):
        if column in metadata.columns:
            mapping = (
                metadata.drop_duplicates("Class ID")
                .set_index("Class ID")[column]
                .to_dict()
            )
            return [
                str(mapping.get(class_id, class_id))
                for class_id in range(CFG["num_classes"])
            ]

    return [str(i) for i in range(CFG["num_classes"])]


from scipy.spatial import ConvexHull


def create_tsne_plot(
    embeddings,
    logits,
    labels,
    file_names,
    class_names,
    fold,
    output_dir,
):
    sample_count = len(labels)

    if sample_count < 4:
        raise ValueError(f"Fold {fold} only contains {sample_count} samples.")

    if embeddings.ndim != 2:
        raise ValueError(f"Expected a 2D embedding array, got {embeddings.shape}.")

    if CFG["normalise_embeddings"]:
        embeddings_for_tsne = normalize(embeddings, norm="l2")
    else:
        embeddings_for_tsne = embeddings

    perplexity = min(
        CFG["perplexity"],
        max(2, (sample_count - 1) // 3),
    )

    print(
        f"    Running t-SNE on {sample_count} samples "
        f"({embeddings.shape[1]}-dimensional embeddings), "
        f"perplexity={perplexity}..."
    )

    tsne_args = {
        "n_components": 2,
        "perplexity": perplexity,
        "init": "pca",
        "learning_rate": "auto",
        "random_state": CFG["random_state"],
        "metric": "euclidean",
    }

    if "max_iter" in inspect.signature(TSNE).parameters:
        tsne_args["max_iter"] = CFG["iterations"]
    else:
        tsne_args["n_iter"] = CFG["iterations"]

    tsne = TSNE(**tsne_args)

    coordinates = tsne.fit_transform(embeddings_for_tsne)
    predictions = np.argmax(logits, axis=1)
    correct = predictions == labels

    results = pd.DataFrame({
        "file_name": file_names,
        "true_class_id": labels,
        "true_class": [class_names[int(label)] for label in labels],
        "predicted_class_id": predictions,
        "predicted_class": [class_names[int(p)] for p in predictions],
        "correct": correct,
        "tsne_x": coordinates[:, 0],
        "tsne_y": coordinates[:, 1],
    })

    csv_path = output_dir / f"tsne_fold_{fold}.csv"
    results.to_csv(csv_path, index=False)

    plt.style.use("default")
    fig, ax = plt.subplots(figsize=(18, 14))

    markers = ["o", "s", "^", "D", "v", "P", "X", "*", "<", ">", "h", "8"]
    base_cmap = plt.get_cmap("tab10")

    unique_classes = sorted(np.unique(labels))

    for idx, class_id in enumerate(unique_classes):
        mask = labels == class_id
        class_pts = coordinates[mask]
        class_name = class_names[int(class_id)]

        color = base_cmap(idx % 10)
        marker = markers[idx % len(markers)]

        centroid_x = np.mean(class_pts[:, 0])
        centroid_y = np.mean(class_pts[:, 1])

        for pt in class_pts:
            ax.plot(
                [pt[0], centroid_x],
                [pt[1], centroid_y],
                color=color,
                alpha=0.15,
                linewidth=0.8,
                zorder=1,
            )

        ax.scatter(
            class_pts[:, 0],
            class_pts[:, 1],
            color=color,
            marker=marker,
            label=f"[{class_id}] {class_name}",
            s=80,
            alpha=0.85,
            edgecolors="black",
            linewidths=0.5,
            zorder=3,
        )

        ax.scatter(
            centroid_x,
            centroid_y,
            color=color,
            marker="*",
            s=280,
            edgecolors="black",
            linewidths=1.2,
            zorder=4,
        )

        ax.text(
            centroid_x,
            centroid_y,
            str(class_id),
            fontsize=9,
            weight="bold",
            color="black",
            ha="center",
            va="center",
            bbox=dict(
                boxstyle="round,pad=0.2",
                facecolor="white",
                edgecolor=color,
                alpha=0.85,
            ),
            zorder=6,
        )

    if CFG["mark_misclassified"]:
        wrong = ~correct
        if np.any(wrong):
            ax.scatter(
                coordinates[wrong, 0],
                coordinates[wrong, 1],
                marker="x",
                color="black",
                s=100,
                linewidths=2.0,
                label="Misclassified",
                zorder=5,
            )

    accuracy = correct.mean() * 100

    ax.set_title(
        f"CNN10 t-SNE Embeddings — Fold {fold}\n",
        fontsize=14,
        pad=12,
    )
    ax.set_xlabel("t-SNE dimension 1")
    ax.set_ylabel("t-SNE dimension 2")
    ax.grid(True, alpha=0.25, linestyle="--")

    ax.legend(
        bbox_to_anchor=(1.02, 1),
        loc="upper left",
        borderaxespad=0,
        fontsize=8,
        markerscale=1.1,
        ncol=1,
    )

    fig.tight_layout()

    png_path = output_dir / f"tsne_fold_{fold}.png"
    fig.savefig(png_path, dpi=250, bbox_inches="tight")
    plt.close(fig)

    print(f"    Saved plot: {png_path}")
    print(f"    Saved coordinates: {csv_path}")
    print(f"    Held-out fold accuracy: {accuracy:.2f}%")

def main():
    set_seed(CFG["random_state"])

    print(f"PyTorch: {torch.__version__}")
    print(f"Device: {DEVICE}")

    output_dir = Path(CFG["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)

    class_names = get_class_names(CFG["metadata_path"])

    for fold in CFG["folds"]:
        print(f"\n{'=' * 65}")
        print(f"Processing held-out fold {fold}")
        print(f"{'=' * 65}")

        fold_checkpoint = (
            Path(CFG["training_dir"])
            / f"fold_{fold}"
            / "checkpoint_epoch50.pth"
        )

        if not fold_checkpoint.exists():
            print(f"WARNING: Checkpoint not found: {fold_checkpoint}")
            print("Skipping this fold.")
            continue

        dataset = FSC22EvaluationDataset(
            metadata_path=CFG["metadata_path"],
            audio_dir=CFG["audio_dir"],
            fold=fold,
        )

        loader = DataLoader(
            dataset,
            batch_size=CFG["batch_size"],
            shuffle=False,
            num_workers=CFG["num_workers"],
            pin_memory=(DEVICE.type == "cuda"),
        )

        print(f"  Held-out samples: {len(dataset)}")
        print(f"  Loading checkpoint: {fold_checkpoint}")

        model = build_model(str(fold_checkpoint))

        embeddings, logits, labels, file_names = extract_embeddings(
            model,
            loader,
        )

        print(f"  Extracted embedding shape: {embeddings.shape}")

        create_tsne_plot(
            embeddings=embeddings,
            logits=logits,
            labels=labels,
            file_names=file_names,
            class_names=class_names,
            fold=fold,
            output_dir=output_dir,
        )

        del model
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    print("\nFinished. Check the output directory:")
    print(output_dir.resolve())


if __name__ == "__main__":
    main()