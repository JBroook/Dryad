import torch
import torch.nn as nn
import torch.nn.functional as F
import SyntheticData as sd
import matplotlib.pyplot as plt
import numpy as np

device ="cuda" if torch.cuda.is_available() else "cpu"

class RiskPredictorMCDropout(nn.Module):
    def __init__(self, num_input_features=8) -> None:
        super().__init__()

        self.blinear1 = nn.Linear(num_input_features, 64)
        self.dropout1 = nn.Dropout(p=0.2)

        self.blinear2 = nn.Linear(64, 64)
        self.dropout2 = nn.Dropout(p=0.2)

        self.blinear3 = nn.Linear(64,32)
        self.dropout3 = nn.Dropout(p=0.2)

        self.output = nn.Linear(32,1)
        self.sigmoid = nn.Sigmoid()

    def forward(self, x):
        x = F.gelu(self.blinear1(x))
        x = self.dropout1(x)

        x = F.gelu(self.blinear2(x))
        x = self.dropout2(x)

        x = F.gelu(self.blinear3(x))
        x = self.dropout3(x)

        x = self.output(x)
        results = {
            "logits" : x,
            "probabilities" : self.sigmoid(x)
        }

        return results

def normalize_tensor(tensor):
    # Flatten spatial dimensions to (W * H, num_features) to find min/max per feature
    flat = tensor.view(-1, tensor.shape[-1])
    min_vals = flat.min(dim=0).values
    max_vals = flat.max(dim=0).values

    # Prevent division by zero for constant features (e.g., all 0s)
    range_vals = torch.where(max_vals - min_vals == 0, torch.ones_like(max_vals), max_vals - min_vals)

    # Broadcast scaling across (W, H, num_features)
    return (tensor - min_vals) / range_vals

def get_input_as_tensor():
    input_tensor = torch.zeros(sd.W, sd.H, sd.INPUT_FEATURES)

    for x in range(sd.W):
        for y in range(sd.H):
            cell = torch.from_numpy(sd.get_cell_attribute(x, y)).float()
            input_tensor[x, y] = cell

    input_tensor = normalize_tensor(input_tensor)

    return input_tensor

def get_label_as_tensor(threshold=0.5):
    label_tensor = torch.zeros(sd.W, sd.H, 1)

    for x in range(sd.W):
        for y in range(sd.H):
            cell = torch.from_numpy(sd.get_cell_attack(x, y)).float()
            label_tensor[x, y] = cell>threshold

    return label_tensor

def predict_mc(model, x, T=100):
    model.train()
    x = x.to(device)

    predicted_risk_grid = torch.zeros(sd.W, sd.H, 1).to(device)

    with torch.no_grad():
        for i in range(T):
            probabilities = model(x)["probabilities"]
            probabilities /= T
            predicted_risk_grid += probabilities

    return predicted_risk_grid

if __name__ == "__main__":
    print(torch.__version__)
    print(torch.version.cuda)
    print(torch.cuda.is_available())
    print("Device:", device)

    model = RiskPredictorMCDropout(num_input_features=sd.INPUT_FEATURES)
    model.to(device)

    input_tensor = get_input_as_tensor()
    input_tensor = input_tensor.to(device)

    label_tensor = get_label_as_tensor()
    label_tensor = label_tensor.to(device)

    epochs = 100

    # heavily penalise wrong answers due to extreme class imbalance
    num_pos = label_tensor.sum().item()
    num_neg = (label_tensor == 0).sum().item()
    pos_weight_val = torch.tensor([num_neg / (num_pos + 1e-7)]).to(device)
    loss_fn = nn.BCEWithLogitsLoss(pos_weight=pos_weight_val)

    optimiser = torch.optim.Adam(model.parameters(), lr=0.005, weight_decay=1e-4)

    distance_to_road_grid = np.zeros((200, 200))

    for x in range(200):
        for y in range(200):
            attrs = sd.get_cell_attribute(x, y)
            distance_to_road_grid[x, y] = attrs[2]

    fig, ax = plt.subplots(figsize=(8, 8))

    # Risk heatmap
    ax.imshow(
        distance_to_road_grid.transpose(),
        cmap='Reds',
        alpha=0.45,  # transparency
        origin='lower'
    )

    # Road 1
    ax.plot(
        sd.road_1[:, 0],
        sd.road_1[:, 1],
        color='black',
        linewidth=2,
        label='Road'
    )

    # Road 2
    ax.plot(
        sd.road_2[:, 0],
        sd.road_2[:, 1],
        color='black',
        linewidth=2,
        label='Road'
    )

    plt.show()

    for epoch in range(epochs):
        break
        model.train()

        logits = model(input_tensor)["logits"]
        optimiser.zero_grad()
        loss = loss_fn(logits, label_tensor)
        loss.backward()
        optimiser.step()

        if (epoch+1)%epochs==0:
            predictions = predict_mc(model, input_tensor).to("cpu")
            predictions = predictions.squeeze().numpy().T

            fig, ax = plt.subplots(figsize=(8, 8))

            # Risk heatmap
            ax.imshow(
                predictions,
                cmap='Reds',
                alpha=0.45,  # transparency
                origin='lower'
            )

            # Road 1
            ax.plot(
                sd.road_1[:, 0],
                sd.road_1[:, 1],
                color='black',
                linewidth=2,
                label='Road'
            )

            # Road 2
            ax.plot(
                sd.road_2[:, 0],
                sd.road_2[:, 1],
                color='black',
                linewidth=2,
                label='Road'
            )

            # River
            ax.plot(
                sd.river[:, 0],
                sd.river[:, 1],
                color='blue',
                linewidth=2,
                label='River'
            )

            # Logging attacks
            ax.scatter(
                sd.attacks[:, 0],
                sd.attacks[:, 1],
                marker='^',
                color='red',
                s=120,
                label='Attack',
                edgecolors='black',
            )
            ax.set_title(f"Epoch {epoch+1}")
            plt.show()