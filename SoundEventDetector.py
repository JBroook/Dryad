# Sound event detector evaluable via PSDS
import time

import numpy as np
import torch, torchaudio
from torch.utils.data import DataLoader, Dataset
import pandas as pd
import torch.nn as nn
import scaper
import json

import os
from pathlib import Path

from models import Cnn10

# premod_audio_dir = "FSC22/Audio Wise V1.0"
# fsc22_audio_dir = "FSC22/ModifiedAudio"
fsc22_meta_path = "FSC22/Metadata/Modified_Metadata.csv"
soundscape_meta_path = "FSC22/Metadata/SED_Metadata.csv"
soundscape_audio_dir = "FSC22/SyntheticSoundscapes"
device ="cuda" if torch.cuda.is_available() else "cpu"

class FSC22SoundscapeDataset(Dataset):
    class_count = 27

    def __init__(self, meta_path, folds=None):
        self.meta_df = pd.read_csv(meta_path)
        if folds:
            self.meta_df = self.meta_df[self.meta_df['Fold'].isin(folds)].reset_index(drop=True)

        self.audio_dir = soundscape_audio_dir

        og_df = pd.read_csv(fsc22_meta_path)
        og_df = og_df.drop_duplicates(subset=['Class Name'])
        self.name_to_id = dict(zip(og_df['Class Name'], og_df['Class ID']))

        # NEW: Pre-load all label matrices into RAM
        print("Pre-loading audio tensors and labels into memory")
        self.labels = []
        self.waveforms = []
        for idx in range(len(self.meta_df)):
            row = self.meta_df.iloc[idx]
            # Pre-load labels
            label_path = os.path.join(soundscape_audio_dir + f"/Fold{row['Fold']}", row['Label Tensor Path'])
            self.labels.append(torch.load(label_path, weights_only=False))

            # Pre-load waveform
            audio_path = os.path.join(self.audio_dir + f"/Fold{row['Fold']}", row['Audio Tensor Path'])
            self.waveforms.append(torch.load(audio_path, weights_only=True))
        print(f"Loaded {len(self.waveforms)} items into memory.")

    def __len__(self):
        return len(self.meta_df)

    def __getitem__(self, item):
        # row = self.meta_df.iloc[item]

        # Instantly load processed audio files
        # with log-mel and spectrogram extractors already applied
        waveform = self.waveforms[item]

        # Retrieve label directly from memory
        label_matrix = self.labels[item]

        return waveform, label_matrix


def save_checkpoint(file_name):
    checkpoint = {
        'epoch': epoch + 1,
        'model_state_dict': model.state_dict(),
        'optimizer_state_dict': optimiser.state_dict(),
        'loss': running_test_loss
    }

    # save checkpoint
    torch.save(checkpoint, file_name)

if __name__=='__main__':
    print(torch.__version__)
    print(torch.version.cuda)
    print(torch.cuda.is_available())
    print("Device:",device)

    # 5-fold cross validation training loop
    fold_stats = []
    loss_fn = nn.BCEWithLogitsLoss()

    training_stats = []
    training_name = "SED_v1/"
    dir = Path('trainedModels/'+training_name)

    if not dir.is_dir():
        dir.mkdir()

    for fold in range(5):
        # initialising model
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
        model.fc_audioset = nn.Linear(512, FSC22SoundscapeDataset.class_count, bias=True)
        model.to(device)


        optimiser = torch.optim.Adam(filter(lambda p: p.requires_grad, model.parameters()), lr=1e-4)

        print(f"Training fold {fold}")
        epochs = 200
        test_dataset = FSC22SoundscapeDataset(soundscape_meta_path, folds=[fold])
        train_folds = [0, 1, 2, 3, 4]
        train_folds.pop(fold)
        train_dataset = FSC22SoundscapeDataset(soundscape_meta_path, folds=train_folds)

        worker_count = 0 #os.cpu_count() // 2  # relegate half of cpu count to multiprocess
        train_loader = DataLoader(train_dataset,
                                  batch_size=32,
                                  num_workers=worker_count,
                                  shuffle=True,
                                  pin_memory=True)
        test_loader = DataLoader(test_dataset,
                                 batch_size=32,
                                 num_workers=worker_count,
                                 shuffle=True,
                                 pin_memory=True)

        last_acc = 0
        acc = 0

        model.train()

        for epoch in range(epochs):
            start = time.time()

            model.train()
            running_correct = 0
            running_total = 0
            running_loss = 0

            step = 0
            for i, (inputs, labels) in enumerate(train_loader):
                print(f"Batch {i} loaded")
                step += 1
                inputs = inputs.to(device, non_blocking=True)
                start = time.time()

                labels = labels.to(device, non_blocking=True)

                optimiser.zero_grad()
                forward_start = time.time()
                output_logits = model(inputs)['frame_logits']  # raw calculation results

                loss = loss_fn(output_logits, labels)
                running_loss += loss.item()
                loss.backward()

                optimiser.step()
                print(f"GPU stepped.")

                # predictions = torch.argmax(output_logits, dim=1)
                predictions = (torch.sigmoid(output_logits) > 0.5).float()
                correct = (predictions == labels).sum()
                total = labels.numel()

                running_correct += correct.item()
                running_total += total

            last_acc = acc
            acc = running_correct / running_total * 100
            print(f"Epoch {epoch + 1} | Loss: {running_loss:.2f}, Accuracy: {acc:.2f}%")

            training_stats.append({
                'fold' : fold,
                'epoch' : epoch,
                'loss' : running_loss,
                'accuracy' : acc,
                'test_accuracy' : -1.0,
                'test_loss' : -1.0
            })

            if (epoch + 1) % 5 == 0:  # test every 5 epochs and save model
                model.eval()
                with torch.inference_mode():
                    running_test_correct = 0
                    running_test_total = 0
                    running_test_loss = 0

                    for inputs, labels in test_loader:
                        inputs = inputs.to(device, non_blocking=True)
                        labels = labels.to(device, non_blocking=True)

                        output_logits = model(inputs)['frame_logits']  # raw calculation results (list of 10 probabilities)

                        loss = loss_fn(output_logits, labels)
                        running_test_loss += loss.item()

                        predictions = (torch.sigmoid(output_logits) > 0.5).float()
                        correct = (predictions == labels).sum()
                        total = labels.numel()

                        running_test_correct += correct.item()
                        running_test_total += total

                    test_acc = running_test_correct / running_test_total * 100
                    training_stats[-1]['test_accuracy'] = test_acc
                    training_stats[-1]['test_loss'] = running_test_loss
                    print(f"\n5th -> Epoch {epoch + 1} | Test loss: {running_test_loss:.2f}, Test accuracy: {test_acc:.2f}%\n")

            if acc>90 and (acc-last_acc)<0.05 and acc>last_acc:
                save_checkpoint(f'trainedModels/{training_name}fold{fold}_checkpoint_epoch{epoch + 1}.pth')
                break

            if epoch==199:
                save_checkpoint(f'trainedModels/{training_name}fold{fold}_checkpoint_epoch{epoch + 1}.pth')

    with open("trainedModels/"+training_name+"training_stats.json", "w") as f:
        json.dump(training_stats, f)