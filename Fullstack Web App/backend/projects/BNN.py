from django.db.models import Count
from django.contrib.gis.db.models.functions import Distance
from datetime import timedelta
from .models import Incident
import math
import torch
import torch.nn as nn

FEATURES = [
    "elevation",
    "slope",
    "distance_to_road",

    "attacks_last_24h",
    "attacks_last_7d",
    "attacks_last_30d",
    "days_since_last_attack",

    "hour_sin",
    "hour_cos",
    "day_sin",
    "day_cos",
]

def cyclical(value, period):
    return (
        math.sin(2 * math.pi * value / period),
        math.cos(2 * math.pi * value / period),
    )

def get_neighbour_cells(grid_cell):
    return (
        grid_cell.project.grid_cells
        .exclude(pk=grid_cell.pk)
        .filter(
            geometry__touches=grid_cell.geometry
        )
    )

def get_neighbour_attack_count(project, grid_cell, timestamp):
    neighbours = get_neighbour_cells(grid_cell)

    return Incident.objects.filter(
        project=project,
        grid_cell__in=neighbours,
        status=Incident.Status.CONFIRMED,
        timestamp__lt=timestamp,
        timestamp__gte=timestamp - timedelta(days=7),
    ).count()


def get_attack_history(project, grid_cell, timestamp):
    confirmed = Incident.objects.filter(
        project=project,
        grid_cell=grid_cell,
        status=Incident.Status.CONFIRMED,
        timestamp__lt=timestamp,
    )

    attacks_last_24h = confirmed.filter(
        timestamp__gte=timestamp - timedelta(hours=24)
    ).count()

    attacks_last_7d = confirmed.filter(
        timestamp__gte=timestamp - timedelta(days=7)
    ).count()

    attacks_last_30d = confirmed.filter(
        timestamp__gte=timestamp - timedelta(days=30)
    ).count()

    last_attack = confirmed.order_by("-timestamp").first()

    if last_attack:
        days_since_last_attack = (
            timestamp - last_attack.timestamp
        ).total_seconds() / 86400
    else:
        days_since_last_attack = 999

    return {
        "attacks_last_24h": attacks_last_24h,
        "attacks_last_7d": attacks_last_7d,
        "attacks_last_30d": attacks_last_30d,
        "days_since_last_attack": days_since_last_attack,
    }


def get_future_attack_target(project, grid_cell, timestamp):

    return Incident.objects.filter(
        project=project,
        grid_cell=grid_cell,
        status=Incident.Status.CONFIRMED,
        timestamp__gt=timestamp,
        timestamp__lte=timestamp + timedelta(days=7),
    ).exists()

def build_training_sample(project, grid_cell, timestamp):

    history = get_attack_history(
        project,
        grid_cell,
        timestamp
    )

    hour_sin, hour_cos = cyclical(
        timestamp.hour,
        24
    )

    day_sin, day_cos = cyclical(
        timestamp.weekday(),
        7
    )

    target = get_future_attack_target(
        project,
        grid_cell,
        timestamp
    )

    return {
        # Environmental
        "elevation": grid_cell.elevation,
        "slope": grid_cell.slope,
        "distance_to_road": grid_cell.distance_to_road,

        # Temporal history
        "attacks_last_24h": history["attacks_last_24h"],
        "attacks_last_7d": history["attacks_last_7d"],
        "attacks_last_30d": history["attacks_last_30d"],
        "days_since_last_attack": history["days_since_last_attack"],

        # Time
        "hour_sin": hour_sin,
        "hour_cos": hour_cos,
        "day_sin": day_sin,
        "day_cos": day_cos,

        # Target
        "target": int(target),

        # Useful metadata
        "grid_cell_id": grid_cell.id,
        "timestamp": timestamp,
    }

def samples_to_tensors(samples):
    X = torch.tensor(
        [
            [sample[f] for f in FEATURES]
            for sample in samples
        ],
        dtype=torch.float32
    )

    y = torch.tensor(
        [
            sample["target"]
            for sample in samples
        ],
        dtype=torch.float32
    )

    return X, y


class RiskMLP(nn.Module):
    def __init__(self, input_size):
        super().__init__()

        self.network = nn.Sequential(
            nn.Linear(input_size, 32),
            nn.ReLU(),

            nn.Linear(32, 16),
            nn.ReLU(),

            nn.Linear(16, 1)
        )

    def forward(self, x):
        return self.network(x).squeeze(-1)

from sklearn.preprocessing import StandardScaler

# build_training_sample(project=)

scaler = StandardScaler()

X_scaled = scaler.fit_transform(X)

X_scaled = torch.tensor(
    X_scaled,
    dtype=torch.float32
)

model = RiskMLP(len(FEATURES))

criterion = nn.BCEWithLogitsLoss()

optimizer = torch.optim.Adam(
    model.parameters(),
    lr=0.001
)

for epoch in range(100):

    optimizer.zero_grad()

    logits = model(X_scaled)

    loss = criterion(logits, y)

    loss.backward()

    optimizer.step()

    if epoch % 10 == 0:
        print(
            f"Epoch {epoch}: "
            f"loss={loss.item():.4f}"
        )

with torch.no_grad():

    probabilities = torch.sigmoid(
        model(X_scaled)
    )

print(probabilities)