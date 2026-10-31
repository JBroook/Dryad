import os
import torch
import torchaudio
import pandas as pd
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from sklearn.metrics import classification_report, accuracy_score

from models import Cnn10

device = "cuda" if torch.cuda.is_available() else "cpu"

esc50_dir = "ESC-50"
esc50_meta_path = os.path.join(esc50_dir, "meta", "esc50.csv")
esc50_audio_dir = os.path.join(esc50_dir, "audio")
checkpoint_path = "trainedModels/refolded/fold_0/checkpoint_epoch40.pth"

# Map ESC-50 categories to their corresponding FSC22 class ID (0 to 26)
CLASS_MAPPING = {
    "chainsaw": 10,
    "rain": 1,
    "wind": 4,
    "crackling_fire": 0,
    "chirping_birds": 22,
    "thunderstorm": 2,
    "footsteps": 18,
    "fireworks": 13,
    "insects": 20,
    "frog": 21,
    "engine": 8,
    "helicopter" : 7
}


class ESC50SubsetDataset(Dataset):
    def __init__(self, meta_path, audio_dir, class_mapping):
        self.audio_dir = audio_dir
        self.meta_df = pd.read_csv(meta_path)
        self.class_mapping = class_mapping

        self.meta_df = self.meta_df[self.meta_df['category'].isin(class_mapping.keys())].reset_index(drop=True)
        self.meta_df['fsc22_class_id'] = self.meta_df['category'].map(class_mapping)

    def __len__(self):
        return len(self.meta_df)

    def __getitem__(self, item):
        row = self.meta_df.iloc[item]
        file_path = os.path.join(self.audio_dir, row['filename'])

        waveform, sample_rate = torchaudio.load(file_path)

        waveform = waveform.mean(dim=0)

        if waveform.abs().max() > 1:
            waveform = waveform / waveform.abs().max()

        label = row['fsc22_class_id']

        return waveform, label


def evaluate(model, dataloader, loss_fn, class_mapping):
    model.eval()
    running_loss = 0.0
    all_preds = []
    all_labels = []

    with torch.no_grad():
        for inputs, labels in dataloader:
            inputs = inputs.to(device, non_blocking=True)
            labels = labels.to(device, non_blocking=True)

            output_logits = model(inputs)['logits']
            loss = loss_fn(output_logits, labels)

            running_loss += loss.item() * inputs.size(0)
            predictions = torch.argmax(output_logits, dim=1)

            all_preds.extend(predictions.cpu().numpy())
            all_labels.extend(labels.cpu().numpy())

    total_samples = len(dataloader.dataset)
    avg_loss = running_loss / total_samples
    accuracy = accuracy_score(all_labels, all_preds) * 100

    target_names = list(class_mapping.keys())
    target_labels = list(class_mapping.values())

    print("\nEVALUATION RESULTS")
    print(f"Test Loss: {avg_loss:.4f} | Test Accuracy: {accuracy:.2f}%\n")
    print("Classification Report:")
    print(classification_report(all_labels, all_preds, labels=target_labels, target_names=target_names, zero_division=0))


if __name__ == '__main__':
    eval_dataset = ESC50SubsetDataset(esc50_meta_path, esc50_audio_dir, CLASS_MAPPING)
    worker_count = max(1, os.cpu_count() // 2)
    eval_loader = DataLoader(eval_dataset, batch_size=32, num_workers=worker_count, shuffle=False, pin_memory=True)

    model = Cnn10(
        sample_rate=32000,
        window_size=1024,
        hop_size=320,
        mel_bins=64,
        fmin=50,
        fmax=14000,
        classes_num=527
    )
    model.fc_audioset = nn.Linear(512, 27, bias=True)

    checkpoint = torch.load(checkpoint_path, map_location=device, weights_only=True)
    model.load_state_dict(checkpoint['model_state_dict'])
    model.to(device)

    loss_fn = nn.CrossEntropyLoss()

    evaluate(model, eval_loader, loss_fn, CLASS_MAPPING)