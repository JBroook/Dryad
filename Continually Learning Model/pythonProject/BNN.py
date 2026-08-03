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
        self.blinear2 = nn.Linear(64,32)
        self.dropout2 = nn.Dropout(p=0.2)
        self.output = nn.Linear(32,1)
        self.sigmoid = nn.Sigmoid()

    def forward(self, x):
        x = F.relu(self.blinear1(x))
        x = self.dropout1(x)

        x = F.relu(self.blinear2(x))
        x = self.dropout2(x)

        x = self.output(x)
        results = {
            "logits" : x,
            "probabilities" : self.sigmoid(x)
        }

        return results

def predict_mc(model, x, T=100):
    model.train()
    model.to(device)
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

    model = RiskPredictorMCDropout(num_input_features=5)

    fig, ax = plt.subplots(figsize=(8, 8))

    input_tensor = torch.zeros(sd.W, sd.H, 5)

    for x in range(sd.W):
        for y in range(sd.H):
            cell = torch.from_numpy(sd.get_cell_attribute(x, y)).float()
            input_tensor[x,y] = cell

    predictions = predict_mc(model, input_tensor).to("cpu")
    predictions = predictions.numpy()

    # Background terrain
    # ax.imshow(altitude, cmap='terrain', origin='lower')

    # Risk heatmap
    ax.imshow(
        predictions,
        cmap='Reds',
        alpha=0.45,  # transparency
        origin='lower'
    )
    plt.show()