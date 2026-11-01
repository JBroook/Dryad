# Full clip classifier

import torch, torchaudio
from torch.utils.data import DataLoader, Dataset
import pandas as pd
import torch.nn as nn
import numpy as np
from sklearn.utils.class_weight import compute_class_weight
from sklearn.metrics import precision_score, recall_score, f1_score, roc_auc_score
import json
import os

from models import Cnn10

premod_audio_dir = "FSC22/Audio Wise V1.0"
fsc22_audio_dir = "FSC22/ModifiedAudio"
fsc22_meta_path = "FSC22/Metadata/Modified_Metadata.csv"
device = "cuda" if torch.cuda.is_available() else "cpu"


def mix_noise(signal, noise, snr_db=10):
    signal_rms = signal.pow(2).mean().sqrt()
    noise_rms = noise.pow(2).mean().sqrt()

    desired_noise_rms = signal_rms / (10 ** (snr_db / 20))

    noise = noise * (desired_noise_rms / (noise_rms + 1e-8))

    return signal + noise


class FSC22Dataset(Dataset):
    class_count = 27

    def __init__(self, fsc22_meta, folds=None, augment=True):
        self.augment = augment
        self.meta_df = pd.read_csv(fsc22_meta)

        self.noise_df = pd.read_csv(fsc22_meta)
        self.noise_df = self.noise_df[self.noise_df['Threat'] == False].reset_index(drop=True)

        if folds:
            self.meta_df = self.meta_df[self.meta_df['Fold'].isin(folds)].reset_index(drop=True)

        self.audio_dir = fsc22_audio_dir

    def __len__(self):
        return len(self.meta_df)

    def __getitem__(self, item):
        row = self.meta_df.iloc[item]
        waveform, sample_rate = torchaudio.load(os.path.join(self.audio_dir, row['Dataset File Name']))

        waveform = waveform.mean(dim=0)

        if self.augment:
            if torch.rand(1) < 0.3:
                shift_amt = torch.randint(0, waveform.size(0) // 4, (1,)).item()
                waveform = torch.roll(waveform, shift_amt, dims=0)

            if len(self.noise_df) > 0 and torch.rand(1) < 0.3:
                noise_row = self.noise_df.sample(n=1).iloc[0]
                noise, _ = torchaudio.load(os.path.join(self.audio_dir, noise_row['Dataset File Name']))
                noise = noise.mean(dim=0)

                if noise.shape[0] < waveform.shape[0]:
                    pad_amount = waveform.shape[0] - noise.shape[0]
                    noise = torch.nn.functional.pad(noise, (0, pad_amount))
                elif noise.shape[0] > waveform.shape[0]:
                    noise = noise[:waveform.shape[0]]

                waveform = mix_noise(waveform, noise, snr_db=torch.randint(20, 35, size=(1,)).item())

        if waveform.abs().max() > 1:
            waveform = waveform / waveform.abs().max()

        label = row['Class ID']

        return waveform, label


def save_checkpoint(file_name, epoch, model, optimiser, running_loss):
    checkpoint = {
        'epoch': epoch + 1,
        'model_state_dict': model.state_dict(),
        'optimizer_state_dict': optimiser.state_dict(),
        'loss': running_loss
    }
    torch.save(checkpoint, file_name)


if __name__ == '__main__':
    print(torch.__version__)
    print(torch.version.cuda)
    print(torch.cuda.is_available())
    print("Device:", device)

    training_name = "final_pure_AC/"
    all_folds = [0, 1, 2, 3, 4]
    epochs = 50
    worker_count = max(1, os.cpu_count() // 2)

    for test_fold in all_folds:
        print(f"\nFold {test_fold}")
        train_folds = [f for f in all_folds if f != test_fold]

        fold_dir = f"trainedModels/{training_name}fold_{test_fold}/"
        os.makedirs(fold_dir, exist_ok=True)
        training_stats = []

        model = Cnn10(
            sample_rate=32000,
            window_size=1024,
            hop_size=320,
            mel_bins=64,
            fmin=50,
            fmax=14000,
            classes_num=527
        )
        checkpoint = torch.load("Cnn10_mAP=0.380.pth", map_location=device)
        model.load_state_dict(checkpoint['model'])
        model.fc_audioset = nn.Linear(512, FSC22Dataset.class_count, bias=True)
        model.to(device)

        train_dataset = FSC22Dataset(fsc22_meta_path, folds=train_folds, augment=True)
        test_dataset = FSC22Dataset(fsc22_meta_path, folds=[test_fold], augment=False)

        train_loader = DataLoader(train_dataset, batch_size=32, num_workers=worker_count, shuffle=True, pin_memory=True)
        test_loader = DataLoader(test_dataset, batch_size=32, num_workers=worker_count, shuffle=False, pin_memory=True)

        labels = train_dataset.meta_df['Class ID'].values
        class_weights = compute_class_weight(class_weight='balanced', classes=np.unique(labels), y=labels)
        weights_tensor = torch.tensor(class_weights, dtype=torch.float).to(device)
        loss_fn = nn.CrossEntropyLoss(weight=weights_tensor)

        pretrained_params = [p for n, p in model.named_parameters() if 'fc_audioset' not in n]
        new_head_params = model.fc_audioset.parameters()

        optimiser = torch.optim.Adam([
            {'params': pretrained_params, 'lr': 5e-5},
            {'params': new_head_params, 'lr': 1e-4}
        ], weight_decay=1e-5)

        scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimiser, T_max=epochs, eta_min=1e-6)

        for epoch in range(epochs):
            model.train()
            running_correct = 0
            running_total = 0
            running_loss = 0

            for inputs, labels in train_loader:
                inputs = inputs.to(device, non_blocking=True)
                labels = labels.to(device, non_blocking=True)

                optimiser.zero_grad()
                output_logits = model(inputs)['logits']

                loss = loss_fn(output_logits, labels)
                running_loss += loss.item()
                loss.backward()
                optimiser.step()

                predictions = torch.argmax(output_logits, dim=1)
                running_correct += torch.eq(predictions, labels).sum().item()
                running_total += labels.size(0)

            acc = running_correct / running_total * 100

            model.eval()
            test_loss = 0
            test_correct = 0
            test_total = 0

            all_test_preds = []
            all_test_targets = []
            all_test_probs = []

            with torch.no_grad():
                for inputs, labels in test_loader:
                    inputs = inputs.to(device, non_blocking=True)
                    labels = labels.to(device, non_blocking=True)

                    output_logits = model(inputs)['logits']
                    loss = loss_fn(output_logits, labels)
                    test_loss += loss.item()

                    probs = torch.softmax(output_logits, dim=1)
                    predictions = torch.argmax(probs, dim=1)

                    test_correct += torch.eq(predictions, labels).sum().item()
                    test_total += labels.size(0)

                    all_test_preds.extend(predictions.cpu().numpy())
                    all_test_targets.extend(labels.cpu().numpy())
                    all_test_probs.extend(probs.cpu().numpy())

            test_acc = test_correct / test_total * 100
            test_preds_arr = np.array(all_test_preds)
            test_targets_arr = np.array(all_test_targets)
            test_probs_arr = np.array(all_test_probs)

            test_precision_macro = precision_score(test_targets_arr, test_preds_arr, average='macro', zero_division=0)
            test_precision_weighted = precision_score(test_targets_arr, test_preds_arr, average='weighted', zero_division=0)
            test_recall_macro = recall_score(test_targets_arr, test_preds_arr, average='macro', zero_division=0)
            test_recall_weighted = recall_score(test_targets_arr, test_preds_arr, average='weighted', zero_division=0)
            test_f1_macro = f1_score(test_targets_arr, test_preds_arr, average='macro', zero_division=0)
            test_f1_weighted = f1_score(test_targets_arr, test_preds_arr, average='weighted', zero_division=0)

            try:
                test_roc_auc_macro = roc_auc_score(test_targets_arr, test_probs_arr, multi_class='ovr', average='macro')
            except ValueError:
                test_roc_auc_macro = np.nan

            print(
                f"Epoch {epoch + 1:02d} | Train Loss: {running_loss:.2f}, Train Acc: {acc:.2f}% | Test Loss: {test_loss:.2f}, Test Acc: {test_acc:.2f}% | Test F1 (Macro): {test_f1_macro:.4f}")

            scheduler.step()

            training_stats.append({
                'epoch': epoch + 1,
                'loss': running_loss,
                'accuracy': acc,
                'test_loss': test_loss,
                'test_accuracy': test_acc,
                'test_precision_macro': test_precision_macro,
                'test_precision_weighted': test_precision_weighted,
                'test_recall_macro': test_recall_macro,
                'test_recall_weighted': test_recall_weighted,
                'test_f1_macro': test_f1_macro,
                'test_f1_weighted': test_f1_weighted,
                'test_roc_auc_macro': test_roc_auc_macro
            })

            if (epoch == epochs - 1 or (epoch + 1) % 10 == 0) and epoch > 0:
                save_checkpoint(f'{fold_dir}checkpoint_epoch{epoch + 1}.pth', epoch,
                                model, optimiser, running_loss)

        with open(f"{fold_dir}training_stats.json", "w") as f:
            json.dump(training_stats, f, indent=4)