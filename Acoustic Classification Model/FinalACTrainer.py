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
from sklearn.utils.class_weight import compute_class_weight
from torch.utils.data import DataLoader, Dataset

from models import Cnn10

fsc22_audio_dir = "FSC22/ModifiedAudio"
fsc22_meta_path = "FSC22/Metadata/Modified_Metadata.csv"
device = "cuda" if torch.cuda.is_available() else "cpu"

CFG = {
    "training_name": "26_class_ac_real/",
    "all_folds": [0, 1, 2, 3, 4],
    "epochs": 50,
    "batch_size": 32,
    "seed": 42,
    "model_name": "Cnn10",
    "checkpoints": {
        "Cnn10": "Cnn10_mAP=0.380.pth",
        "Cnn14": "Cnn14_mAP=0.431.pth",
    },
    "sample_rate": 32000,
    "clip_seconds": 5,
    "backbone_lr": 1e-4,
    "head_lr": 1e-3,
    "weight_decay": 1e-5,
    "warmup_epochs": 3,
    "min_lr": 1e-6,
    "shift_prob": 0.5,
    "speed_prob": 0.4,
    "speed_range": (0.9, 1.1),
    "gain_prob": 0.7,
    "gain_db_range": (-6.0, 6.0),
    "noise_prob": 0.5,
    "noise_snr_range": (10, 30),
    "mixup_prob": 0.8,
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

    in_features = model.fc_audioset.in_features
    model.fc_audioset = nn.Linear(in_features, num_classes, bias=True)
    return model.to(device)


def mixup_batch(x, y, alpha):
    lam = torch.distributions.Beta(alpha, alpha).sample((x.size(0),)).to(x.device)
    lam = torch.max(lam, 1 - lam)
    perm = torch.randperm(x.size(0), device=x.device)
    x_mix = lam.unsqueeze(1) * x + (1 - lam.unsqueeze(1)) * x[perm]
    return x_mix, y, y[perm], lam


def save_checkpoint(file_name, epoch, model, optimiser, scheduler, running_loss):
    torch.save({
        "epoch": epoch + 1,
        "model_state_dict": model.state_dict(),
        "optimizer_state_dict": optimiser.state_dict(),
        "scheduler_state_dict": scheduler.state_dict(),
        "loss": running_loss,
    }, file_name)


def get_latest_checkpoint(out_dir):
    checkpoint_files = glob.glob(os.path.join(out_dir, "checkpoint_epoch*.pth"))
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


if __name__ == "__main__":
    print(torch.__version__, torch.version.cuda, torch.cuda.is_available())
    print("Device:", device)

    set_seed(CFG["seed"])

    epochs = CFG["epochs"]
    worker_count = max(1, os.cpu_count() // 2)
    base_dir = f"trainedModels/{CFG['training_name']}"
    os.makedirs(base_dir, exist_ok=True)

    model = build_model(FSC22Dataset.class_count)

    train_dataset = FSC22Dataset(fsc22_meta_path, folds=CFG["all_folds"], augment=True)
    train_loader = DataLoader(train_dataset, batch_size=CFG["batch_size"], num_workers=worker_count,
                              shuffle=True, pin_memory=True, drop_last=True,
                              persistent_workers=True)

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

    latest_ckpt_path, start_epoch = get_latest_checkpoint(base_dir)
    training_stats = []

    if latest_ckpt_path:
        print(f"Resuming training from checkpoint: {latest_ckpt_path} (epoch {start_epoch})")
        checkpoint = torch.load(latest_ckpt_path, map_location=device, weights_only=False)
        model.load_state_dict(checkpoint["model_state_dict"])
        optimiser.load_state_dict(checkpoint["optimizer_state_dict"])
        if "scheduler_state_dict" in checkpoint:
            scheduler.load_state_dict(checkpoint["scheduler_state_dict"])

        stats_path = f"{base_dir}training_stats.json"
        if os.path.exists(stats_path):
            with open(stats_path, "r") as f:
                training_stats = json.load(f)

    if start_epoch >= epochs:
        print(f"Final model already fully trained ({start_epoch}/{epochs} epochs).")
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
                    target_for_acc = y_a
                else:
                    loss = criterion(logits, labels).mean()
                    target_for_acc = labels

                loss.backward()
                optimiser.step()

                running_loss += loss.item()
                running_correct += torch.eq(torch.argmax(logits, dim=1), target_for_acc).sum().item()
                running_total += labels.size(0)

            train_loss = running_loss / len(train_loader)
            train_acc = running_correct / running_total * 100

            scheduler.step()

            print(f"Epoch {epoch + 1:02d} | Train Loss: {train_loss:.3f}, Train Acc*: {train_acc:.2f}%")

            training_stats.append({"epoch": epoch + 1, "loss": train_loss, "accuracy": train_acc})

            if (epoch == epochs - 1 or (epoch + 1) % 10 == 0) and epoch > 0:
                save_checkpoint(f"{base_dir}checkpoint_epoch{epoch + 1}.pth", epoch,
                                model, optimiser, scheduler, train_loss)

            with open(f"{base_dir}training_stats.json", "w") as f:
                json.dump(training_stats, f, indent=4)

    torch.save(model.state_dict(), f"{base_dir}final_model.pth")