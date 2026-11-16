# Full clip classifier (v2)

import glob
import json
import os
import random
import re

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F
import torchaudio
from sklearn.metrics import (confusion_matrix, f1_score, precision_score,
                             recall_score, roc_auc_score)
from sklearn.utils.class_weight import compute_class_weight
from torch.utils.data import DataLoader, Dataset

from models import Cnn10

# Config
fsc22_audio_dir = "FSC22/ModifiedAudio"
fsc22_meta_path = "FSC22/Metadata/Modified_Metadata.csv"
device = "cuda" if torch.cuda.is_available() else "cpu"

CFG = {
    "training_name": "26_class_ac_real/",
    "all_folds": [0, 1, 2, 3, 4],
    "epochs": 50,
    "batch_size": 32,
    "seed": 42,

    # Backbone: "Cnn10" or "Cnn14" (Cnn14 needs its own PANNs checkpoint)
    "model_name": "Cnn10",
    "checkpoints": {
        "Cnn10": "Cnn10_mAP=0.380.pth",
        "Cnn14": "Cnn14_mAP=0.431.pth",
    },

    # Audio
    "sample_rate": 32000,
    "clip_seconds": 5,

    # Optimiser
    "backbone_lr": 1e-4,
    "head_lr": 1e-3,
    "weight_decay": 1e-5,
    "warmup_epochs": 3,
    "min_lr": 1e-6,

    # Augmentation (all training-only)
    "shift_prob": 0.5,
    "speed_prob": 0.4,
    "speed_range": (0.9, 1.1),
    "gain_prob": 0.7,
    "gain_db_range": (-6.0, 6.0),
    "noise_prob": 0.5,
    "noise_snr_range": (10, 30),       # dB, inclusive-low / exclusive-high for randint
    "mixup_prob": 0.8,                 # fraction of batches that get mixup
    "mixup_alpha": 0.4,
}


def set_seed(seed):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


def mix_noise(signal, noise, snr_db=10):
    signal_rms = signal.pow(2).mean().sqrt()
    noise_rms = noise.pow(2).mean().sqrt()
    desired_noise_rms = signal_rms / (10 ** (snr_db / 20))
    noise = noise * (desired_noise_rms / (noise_rms + 1e-8))
    return signal + noise


def rand_uniform(low, high):
    return low + (high - low) * torch.rand(1).item()


class FSC22Dataset(Dataset):
    class_count = 26

    def __init__(self, fsc22_meta, folds=None, augment=True):
        self.augment = augment
        self.audio_dir = fsc22_audio_dir
        self.target_len = CFG["sample_rate"] * CFG["clip_seconds"]

        self.meta_df = pd.read_csv(fsc22_meta)
        if folds:
            self.meta_df = self.meta_df[self.meta_df["Fold"].isin(folds)].reset_index(drop=True)

        noise_df = self.meta_df[self.meta_df["Threat"] == False]
        self.noise_files = noise_df["Dataset File Name"].tolist()

    def __len__(self):
        return len(self.meta_df)

    def _load(self, file_name):
        waveform, _ = torchaudio.load(os.path.join(self.audio_dir, file_name))
        return waveform.mean(dim=0)

    def _fix_length(self, waveform):
        n = self.target_len
        if waveform.shape[0] < n:
            waveform = F.pad(waveform, (0, n - waveform.shape[0]))
        elif waveform.shape[0] > n:
            waveform = waveform[:n]
        return waveform

    def _augment(self, waveform):
        if torch.rand(1).item() < CFG["speed_prob"]:
            factor = rand_uniform(*CFG["speed_range"])
            base = 100
            new = int(round(base * factor))
            if new != base:
                waveform = torchaudio.functional.resample(waveform, orig_freq=base, new_freq=new)
                waveform = self._fix_length(waveform)

        if torch.rand(1).item() < CFG["shift_prob"]:
            shift_amt = torch.randint(0, waveform.size(0), (1,)).item()
            waveform = torch.roll(waveform, shift_amt, dims=0)

        if self.noise_files and torch.rand(1).item() < CFG["noise_prob"]:
            idx = torch.randint(0, len(self.noise_files), (1,)).item()
            noise = self._load(self.noise_files[idx])
            noise = self._fix_length(noise)
            lo, hi = CFG["noise_snr_range"]
            snr = torch.randint(lo, hi, (1,)).item()
            waveform = mix_noise(waveform, noise, snr_db=snr)

        if torch.rand(1).item() < CFG["gain_prob"]:
            gain_db = rand_uniform(*CFG["gain_db_range"])
            waveform = waveform * (10 ** (gain_db / 20))

        return waveform

    def __getitem__(self, item):
        row = self.meta_df.iloc[item]
        waveform = self._fix_length(self._load(row["Dataset File Name"]))

        if self.augment:
            waveform = self._augment(waveform)

        peak = waveform.abs().max()
        if peak > 1:
            waveform = waveform / peak

        return waveform, int(row["Class ID"])


def build_model(num_classes):
    name = CFG["model_name"]
    cls = {"Cnn10": Cnn10}.get(name)

    model = cls(
        sample_rate=CFG["sample_rate"],
        window_size=1024,
        hop_size=320,
        mel_bins=64,
        fmin=50,
        fmax=14000,
        classes_num=527,
    )
    checkpoint = torch.load(CFG["checkpoints"][name], map_location=device, weights_only=False)
    model.load_state_dict(checkpoint["model"])

    in_features = model.fc_audioset.in_features  # 512 for Cnn10, 2048 for Cnn14
    model.fc_audioset = nn.Linear(in_features, num_classes, bias=True)
    return model.to(device)


def mixup_batch(x, y, alpha):
    """Waveform-level mixup. lam >= 0.5 so y_a is always the dominant label."""
    lam = torch.distributions.Beta(alpha, alpha).sample((x.size(0),)).to(x.device)
    lam = torch.max(lam, 1 - lam)
    perm = torch.randperm(x.size(0), device=x.device)
    x_mix = lam.unsqueeze(1) * x + (1 - lam.unsqueeze(1)) * x[perm]
    return x_mix, y, y[perm], lam


def save_checkpoint(file_name, epoch, model, optimiser, scheduler, running_loss):
    torch.save({
        "epoch": epoch + 1,  # save 1-indexed completed epoch count
        "model_state_dict": model.state_dict(),
        "optimizer_state_dict": optimiser.state_dict(),
        "scheduler_state_dict": scheduler.state_dict(),
        "loss": running_loss,
    }, file_name)


def get_latest_checkpoint(fold_dir):
    """Finds the checkpoint with the highest epoch number in fold_dir."""
    checkpoint_files = glob.glob(os.path.join(fold_dir, "checkpoint_epoch*.pth"))
    if not checkpoint_files:
        return None, 0

    latest_epoch = -1
    latest_path = None
    for filepath in checkpoint_files:
        match = re.search(r"checkpoint_epoch(\d+)\.pth", os.path.basename(filepath))
        if match:
            epoch = int(match.group(1))
            if epoch > latest_epoch:
                latest_epoch = epoch
                latest_path = filepath

    return latest_path, latest_epoch


@torch.no_grad()
def evaluate(model, loader, criterion):
    model.eval()
    total_loss, n_batches = 0.0, 0
    preds, targets, probs_all = [], [], []

    for inputs, labels in loader:
        inputs = inputs.to(device, non_blocking=True)
        labels = labels.to(device, non_blocking=True)

        logits = model(inputs)["logits"]
        total_loss += criterion(logits, labels).mean().item()
        n_batches += 1

        probs = torch.softmax(logits, dim=1)
        preds.append(torch.argmax(probs, dim=1).cpu().numpy())
        targets.append(labels.cpu().numpy())
        probs_all.append(probs.cpu().numpy())

    preds = np.concatenate(preds)
    targets = np.concatenate(targets)
    probs_all = np.concatenate(probs_all)

    present = np.unique(targets)
    aucs = []
    for c in present:
        binary = (targets == c).astype(int)
        if binary.min() == binary.max():
            continue
        aucs.append(roc_auc_score(binary, probs_all[:, c]))
    roc_auc = float(np.mean(aucs)) if aucs else float("nan")

    cm = confusion_matrix(targets, preds, labels=list(range(FSC22Dataset.class_count)))

    metrics = {
        "test_loss": total_loss / max(n_batches, 1),
        "test_accuracy": float((preds == targets).mean() * 100),
        "test_precision_macro": float(precision_score(targets, preds, average="macro", zero_division=0)),
        "test_precision_weighted": float(precision_score(targets, preds, average="weighted", zero_division=0)),
        "test_recall_macro": float(recall_score(targets, preds, average="macro", zero_division=0)),
        "test_recall_weighted": float(recall_score(targets, preds, average="weighted", zero_division=0)),
        "test_f1_macro": float(f1_score(targets, preds, average="macro", zero_division=0)),
        "test_f1_weighted": float(f1_score(targets, preds, average="weighted", zero_division=0)),
        "test_roc_auc_macro": roc_auc,
        "confusion_matrix": cm.tolist(),
    }
    return metrics, preds, targets


def report_confusion(all_targets, all_preds, out_dir, class_names):
    n = FSC22Dataset.class_count
    cm = confusion_matrix(all_targets, all_preds, labels=list(range(n)))
    np.savetxt(os.path.join(out_dir, "confusion_matrix_all_folds.csv"), cm, fmt="%d", delimiter=",")

    off = cm.copy()
    np.fill_diagonal(off, 0)
    flat = np.dstack(np.unravel_index(np.argsort(-off, axis=None), off.shape))[0]
    print("\nMost confused class pairs (true -> predicted : count)")
    for t, p in flat[:15]:
        if off[t, p] == 0:
            break
        print(f"  {class_names[t]} -> {class_names[p]} : {off[t, p]}")

    per_class_recall = cm.diagonal() / np.maximum(cm.sum(axis=1), 1)
    print("\nPer-class recall (worst 10)")
    for c in np.argsort(per_class_recall)[:10]:
        print(f"  {class_names[c]}: {per_class_recall[c] * 100:.1f}%")

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        cm_norm = cm / np.maximum(cm.sum(axis=1, keepdims=True), 1)
        fig, ax = plt.subplots(figsize=(12, 10))
        im = ax.imshow(cm_norm, cmap="Blues", vmin=0, vmax=1)
        ax.set_xticks(range(n))
        ax.set_yticks(range(n))
        ax.set_xticklabels(class_names, rotation=90, fontsize=7)
        ax.set_yticklabels(class_names, fontsize=7)
        ax.set_xlabel("Predicted")
        ax.set_ylabel("True")
        ax.set_title("Row-normalised confusion matrix (final epoch, all folds)")
        fig.colorbar(im, ax=ax)
        fig.tight_layout()
        fig.savefig(os.path.join(out_dir, "confusion_matrix_all_folds.png"), dpi=150)
        plt.close(fig)
    except ImportError:
        print("matplotlib not installed; skipped confusion matrix image (CSV was saved).")


def get_class_names():
    meta = pd.read_csv(fsc22_meta_path)
    for col in ("Class Name", "Class_Name", "Class"):
        if col in meta.columns:
            mapping = meta.drop_duplicates("Class ID").set_index("Class ID")[col].to_dict()
            return [str(mapping.get(i, i)) for i in range(FSC22Dataset.class_count)]
    return [str(i) for i in range(FSC22Dataset.class_count)]


if __name__ == "__main__":
    print(torch.__version__, torch.version.cuda, torch.cuda.is_available())
    print("Device:", device)

    set_seed(CFG["seed"])

    epochs = CFG["epochs"]
    worker_count = max(1, os.cpu_count() // 2)
    base_dir = f"trainedModels/{CFG['training_name']}"
    os.makedirs(base_dir, exist_ok=True)
    class_names = get_class_names()

    agg_preds, agg_targets = [], []
    fold_summaries = []

    for test_fold in CFG["all_folds"]:
        print(f"\nFold {test_fold}")
        train_folds = [f for f in CFG["all_folds"] if f != test_fold]

        fold_dir = f"{base_dir}fold_{test_fold}/"
        os.makedirs(fold_dir, exist_ok=True)

        model = build_model(FSC22Dataset.class_count)

        train_dataset = FSC22Dataset(fsc22_meta_path, folds=train_folds, augment=True)
        test_dataset = FSC22Dataset(fsc22_meta_path, folds=[test_fold], augment=False)

        train_loader = DataLoader(train_dataset, batch_size=CFG["batch_size"], num_workers=worker_count,
                                  shuffle=True, pin_memory=True, drop_last=True,
                                  persistent_workers=True)
        test_loader = DataLoader(test_dataset, batch_size=CFG["batch_size"], num_workers=worker_count,
                                 shuffle=False, pin_memory=True, persistent_workers=True)

        train_labels = train_dataset.meta_df["Class ID"].values
        class_weights = compute_class_weight(class_weight="balanced",
                                             classes=np.unique(train_labels), y=train_labels)
        weights_tensor = torch.tensor(class_weights, dtype=torch.float).to(device)
        criterion = nn.CrossEntropyLoss(weight=weights_tensor, reduction="none")

        pretrained_params = [p for n, p in model.named_parameters() if "fc_audioset" not in n]
        head_params = list(model.fc_audioset.parameters())

        optimiser = torch.optim.Adam([
            {"params": pretrained_params, "lr": CFG["backbone_lr"]},
            {"params": head_params, "lr": CFG["head_lr"]},
        ], weight_decay=CFG["weight_decay"])

        warmup = torch.optim.lr_scheduler.LinearLR(
            optimiser, start_factor=0.1, end_factor=1.0, total_iters=CFG["warmup_epochs"])
        cosine = torch.optim.lr_scheduler.CosineAnnealingLR(
            optimiser, T_max=epochs - CFG["warmup_epochs"], eta_min=CFG["min_lr"])
        scheduler = torch.optim.lr_scheduler.SequentialLR(
            optimiser, schedulers=[warmup, cosine], milestones=[CFG["warmup_epochs"]])

        # Check for existing checkpoint to resume
        latest_ckpt_path, start_epoch = get_latest_checkpoint(fold_dir)
        training_stats = []

        if latest_ckpt_path:
            print(f"Resuming training from checkpoint: {latest_ckpt_path} (epoch {start_epoch})")
            checkpoint = torch.load(latest_ckpt_path, map_location=device, weights_only=False)
            model.load_state_dict(checkpoint["model_state_dict"])
            optimiser.load_state_dict(checkpoint["optimizer_state_dict"])
            if "scheduler_state_dict" in checkpoint:
                scheduler.load_state_dict(checkpoint["scheduler_state_dict"])

            stats_path = f"{fold_dir}training_stats.json"
            if os.path.exists(stats_path):
                with open(stats_path, "r") as f:
                    training_stats = json.load(f)

        if start_epoch >= epochs:
            print(f"Fold {test_fold} already fully trained ({start_epoch}/{epochs} epochs). Evaluating final model...")
            metrics, preds, targets = evaluate(model, test_loader, criterion)
        else:
            for epoch in range(start_epoch, epochs):
                model.train()
                running_loss, running_correct, running_total = 0.0, 0, 0

                for inputs, labels in train_loader:
                    inputs = inputs.to(device, non_blocking=True)
                    labels = labels.to(device, non_blocking=True)

                    use_mixup = torch.rand(1).item() < CFG["mixup_prob"]
                    if use_mixup:
                        inputs, y_a, y_b, lam = mixup_batch(inputs, labels, CFG["mixup_alpha"])

                    optimiser.zero_grad()
                    logits = model(inputs)["logits"]

                    if use_mixup:
                        loss = (lam * criterion(logits, y_a) + (1 - lam) * criterion(logits, y_b)).mean()

                        target_for_acc = y_a  # dominant label (lam >= 0.5)
                    else:
                        loss = criterion(logits, labels).mean()
                        target_for_acc = labels

                    loss.backward()
                    optimiser.step()

                    running_loss += loss.item()
                    running_correct += torch.eq(torch.argmax(logits, dim=1), target_for_acc).sum().item()
                    running_total += labels.size(0)

                train_loss = running_loss / len(train_loader)
                train_acc = running_correct / running_total * 100  # approximate when mixup is active

                metrics, preds, targets = evaluate(model, test_loader, criterion)
                scheduler.step()

                print(f"Epoch {epoch + 1:02d} | Train Loss: {train_loss:.3f}, Train Acc*: {train_acc:.2f}% | "
                      f"Test Loss: {metrics['test_loss']:.3f}, Test Acc: {metrics['test_accuracy']:.2f}% | "
                      f"Test F1 (Macro): {metrics['test_f1_macro']:.4f}")

                training_stats.append({"epoch": epoch + 1, "loss": train_loss, "accuracy": train_acc, **metrics})

                if (epoch == epochs - 1 or (epoch + 1) % 10 == 0) and epoch > 0:
                    save_checkpoint(f"{fold_dir}checkpoint_epoch{epoch + 1}.pth", epoch,
                                    model, optimiser, scheduler, train_loss)

                with open(f"{fold_dir}training_stats.json", "w") as f:
                    json.dump(training_stats, f, indent=4)

        # Record metrics for overall cross-fold aggregation
        fold_summaries.append({"fold": test_fold, **(training_stats[-1] if training_stats else metrics)})
        agg_preds.append(preds)
        agg_targets.append(targets)

    # Cross-fold summary (final epoch)
    accs = [s["test_accuracy"] for s in fold_summaries]
    f1s = [s["test_f1_macro"] for s in fold_summaries]
    print("\n==== Final-epoch results across folds ====")
    for s in fold_summaries:
        print(f"Fold {s['fold']}: Acc {s['test_accuracy']:.2f}% | F1 macro {s['test_f1_macro']:.4f}")
    print(f"Mean Acc: {np.mean(accs):.2f}% (+/- {np.std(accs):.2f}) | "
          f"Mean F1 macro: {np.mean(f1s):.4f} (+/- {np.std(f1s):.4f})")

    with open(f"{base_dir}final_summary.json", "w") as f:
        json.dump({"config": {k: v for k, v in CFG.items()}, "folds": fold_summaries,
                   "mean_accuracy": float(np.mean(accs)), "std_accuracy": float(np.std(accs)),
                   "mean_f1_macro": float(np.mean(f1s)), "std_f1_macro": float(np.std(f1s))},
                  f, indent=4)

    report_confusion(np.concatenate(agg_targets), np.concatenate(agg_preds), base_dir, class_names)