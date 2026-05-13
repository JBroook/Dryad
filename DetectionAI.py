# Steps
# 1. Load fsc22 dataset
# 2. Initiate CNN10 model
# 3. Reconfigure CNN10 final layer to fit audio class count
# 4. Build dataloader that overlaps random sounds from fsc22 to esc50 sounds
# 5. Train CNN10 until it reaches high accuracy
# 6. Evaluate via confusion matrix

import torch, torchaudio
from torch.utils.data import DataLoader, Dataset
import pandas as pd
import torch.nn as nn
import json

import os

from models import Cnn10

premod_audio_dir = "FSC22/Audio Wise V1.0"
fsc22_audio_dir = "FSC22/ModifiedAudio"
fsc22_meta_path = "FSC22/Metadata/Modified_Metadata.csv"
device ="cuda" if torch.cuda.is_available() else "cpu"

def mix_noise(signal, noise, snr_db=10):
    signal_rms = signal.pow(2).mean().sqrt()
    noise_rms = noise.pow(2).mean().sqrt()

    desired_noise_rms = signal_rms / (10 ** (snr_db / 20))

    noise = noise * (desired_noise_rms / (noise_rms + 1e-8))

    return signal + noise

class FSC22Dataset(Dataset):
    def __init__(self, fsc22_meta, folds=None, augment=True):
        self.augment = augment
        self.meta_df = pd.read_csv(fsc22_meta)
        # filter out non-threat classes
        self.meta_df = self.meta_df[self.meta_df['Threat']].reset_index(drop=True)
        # reset class IDs to be in continuous range
        self.meta_df['Class ID'] = pd.factorize(self.meta_df['Class Name'])[0]

        # get noise data
        self.noise_df = pd.read_csv(fsc22_meta)
        self.noise_df = self.noise_df[self.noise_df['Threat']==False].reset_index(drop=True)

        if folds:
            # filter out unwanted folds
            self.meta_df = self.meta_df[self.meta_df['Fold'].isin(folds)].reset_index(drop=True)

        self.class_count = len(self.meta_df['Class Name'].unique())
        self.audio_dir = fsc22_audio_dir

    def __len__(self):
        return len(self.meta_df)

    def __getitem__(self, item):
        row = self.meta_df.iloc[item]
        waveform, sample_rate = torchaudio.load(os.path.join(self.audio_dir, row['Dataset File Name']))

        # average left and right channels to convert stereo to mono
        waveform = waveform.mean(dim=0)

        if self.augment:
            # get random noise
            noise_row = self.noise_df.sample(n=1).iloc[0]
            noise, _ = torchaudio.load(os.path.join(self.audio_dir, noise_row['Dataset File Name']))
            noise = noise.mean(dim=0)
            if torch.rand(1) < 0.5:
                waveform = mix_noise(waveform, noise, snr_db=torch.randint(15, 30, size=(1,)).item())

        # normalize audio
        if waveform.abs().max() > 1:
            waveform = waveform / waveform.abs().max()

        label = row['Class ID']

        return waveform, label

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
    loss_fn = nn.CrossEntropyLoss()

    training_stats = []
    training_name = "100epoch_1RNR/"

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
        model.fc_audioset = nn.Linear(512, 10, bias=True)
        model.to(device)

        for param in model.parameters():
            param.requires_grad = True

        optimiser = torch.optim.Adam(filter(lambda p: p.requires_grad, model.parameters()), lr=1e-4)

        print(f"Training fold {fold}")
        epochs = 100
        test_dataset = FSC22Dataset(fsc22_meta_path, folds=[fold], augment=False)
        train_folds = [0, 1, 2, 3, 4]
        train_folds.pop(fold)
        train_dataset = FSC22Dataset(fsc22_meta_path, folds=train_folds)

        worker_count = os.cpu_count() // 2  # relegate half of cpu count to multiprocess
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

        for epoch in range(epochs):
            model.train()
            running_correct = 0
            running_total = 0
            running_loss = 0

            for inputs, labels in train_loader:
                inputs = inputs.to(device, non_blocking=True)
                labels = labels.to(device, non_blocking=True)

                optimiser.zero_grad()
                output_logits = model(inputs)['logits']  # raw calculation results

                loss = loss_fn(output_logits, labels)
                running_loss += loss.item()
                loss.backward()

                optimiser.step()

                predictions = torch.argmax(output_logits, dim=1)
                running_correct += torch.eq(predictions, labels).sum().item()
                running_total += labels.size(0)

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

                        output_logits = model(inputs)['logits']  # raw calculation results (list of 10 probabilities)

                        loss = loss_fn(output_logits, labels)
                        running_test_loss += loss.item()

                        predictions = torch.argmax(output_logits, dim=1)
                        running_test_correct += torch.eq(predictions, labels).sum().item()
                        running_test_total += labels.size(0)

                    test_acc = running_test_correct / running_test_total * 100
                    training_stats[-1]['test_accuracy'] = test_acc
                    training_stats[-1]['test_loss'] = running_test_loss
                    print(f"\n5th -> Epoch {epoch + 1} | Test loss: {running_test_loss:.2f}, Test accuracy: {test_acc:.2f}%\n")

            if acc>90 and (acc-last_acc)<0.05 and acc>last_acc:
                save_checkpoint(f'trainedModels/{training_name}fold{fold}_checkpoint_epoch{epoch + 1}.pth')
                break

            if epoch==99:
                save_checkpoint(f'trainedModels/{training_name}fold{fold}_checkpoint_epoch{epoch + 1}.pth')

    with open("trainedModels/"+training_name+"training_stats.json", "w") as f:
        json.dump(training_stats, f)