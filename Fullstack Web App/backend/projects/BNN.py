from django.conf import settings
from collections import defaultdict
import random
from datetime import timedelta

import joblib
from sklearn.preprocessing import StandardScaler
from .models import GridCell, Incident
import math
import torch
import torch.nn as nn

from sklearn.metrics import (
    precision_score,
    recall_score,
    average_precision_score,
)

FEATURES = [
    "elevation",
    "slope",
    "distance_to_road",

    # "attacks_last_24h",
    # "attacks_last_7d",
    # "attacks_last_30d",
    # "days_since_last_attack",

    # "hour_sin",
    # "hour_cos",
    # "day_sin",
    # "day_cos",
]

RISK_INFERENCE_PASSES = 100

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

def load_incidents(project, start_time, end_time):
    return list(
        Incident.objects.filter(
            project=project,
            status=Incident.Status.CONFIRMED,
            timestamp__gte=start_time,
            timestamp__lte=end_time,
        )
        .values(
            "grid_cell_id",
            "timestamp",
        )
        .order_by("timestamp")
    )

def group_incidents_by_cell(incidents):

    grouped = defaultdict(list)

    for incident in incidents:
        grouped[incident["grid_cell_id"]].append(
            incident["timestamp"]
        )

    return grouped

def get_attack_history_from_memory(
    timestamps,
    observation_time,
):
    attacks_last_24h = 0
    attacks_last_7d = 0
    attacks_last_30d = 0

    day_1 = observation_time - timedelta(hours=24)
    day_7 = observation_time - timedelta(days=7)
    day_30 = observation_time - timedelta(days=30)

    last_attack = None

    for timestamp in timestamps:

        if timestamp >= observation_time:
            break

        if timestamp >= day_30:
            attacks_last_30d += 1

        if timestamp >= day_7:
            attacks_last_7d += 1

        if timestamp >= day_1:
            attacks_last_24h += 1

        last_attack = timestamp

    if last_attack:
        days_since_last_attack = (
            observation_time - last_attack
        ).total_seconds() / 86400
    else:
        days_since_last_attack = 999

    return {
        "attacks_last_24h": attacks_last_24h,
        "attacks_last_7d": attacks_last_7d,
        "attacks_last_30d": attacks_last_30d,
        "days_since_last_attack": days_since_last_attack,
    }


def get_future_attack_target_from_memory(
    timestamps,
    observation_time,
):
    future_end = observation_time + timedelta(days=7)

    for timestamp in timestamps:

        if timestamp <= observation_time:
            continue

        if timestamp <= future_end:
            return 1

        break

    return 0

def build_training_sample(
    grid_cell,
    observation_time,
    incident_timestamps,
):

    history = get_attack_history_from_memory(
        incident_timestamps,
        observation_time,
    )

    hour_sin, hour_cos = cyclical(
        observation_time.hour,
        24,
    )

    day_sin, day_cos = cyclical(
        observation_time.weekday(),
        7,
    )

    target = get_future_attack_target_from_memory(
        incident_timestamps,
        observation_time,
    )

    return {
        "elevation": grid_cell.elevation or 0,
        "slope": grid_cell.slope or 0,
        "distance_to_road": grid_cell.distance_to_road or 0,

        "attacks_last_24h":
            history["attacks_last_24h"],

        "attacks_last_7d":
            history["attacks_last_7d"],

        "attacks_last_30d":
            history["attacks_last_30d"],

        "days_since_last_attack":
            history["days_since_last_attack"],

        "hour_sin": hour_sin,
        "hour_cos": hour_cos,

        "day_sin": day_sin,
        "day_cos": day_cos,

        "target": target,

        "grid_cell_id": grid_cell.id,
        "timestamp": observation_time,
    }

def generate_training_samples(
    project,
    start_time,
    end_time,
    interval_days=1,
):
    # We need 30 days of history for the
    # attacks_last_30d feature.
    incident_start = (
        start_time - timedelta(days=30)
    )

    # We need another 7 days after the
    # observation time for the target.
    incident_end = (
        end_time + timedelta(days=7)
    )

    incidents = load_incidents(
        project,
        incident_start,
        incident_end,
    )

    incidents_by_cell = group_incidents_by_cell(
        incidents
    )

    cells = list(
        project.grid_cells.all()
    )

    samples = []

    for cell in cells:

        timestamps = incidents_by_cell.get(
            cell.id,
            [],
        )

        current_time = start_time

        while current_time <= end_time:

            sample = build_training_sample(
                cell,
                current_time,
                timestamps,
            )

            samples.append(sample)

            current_time += timedelta(
                days=interval_days
            )

    return samples

def samples_to_tensors(samples):
    X = torch.tensor(
        [
            [
                sample[feature]
                for feature in FEATURES
            ]
            for sample in samples
        ],
        dtype=torch.float32,
    )

    y = torch.tensor(
        [
            sample["target"]
            for sample in samples
        ],
        dtype=torch.float32,
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

            nn.Linear(16, 1),
        )

    def forward(self, x, stochastic=False):
        for layer in self.network:
            x = layer(x)
            if stochastic and isinstance(layer, nn.ReLU):
                x = nn.functional.dropout(x, p=0.2, training=True)
        return x.squeeze(-1)

def undersample(
    samples,
    negative_ratio=3,
    seed=42,
):
    positives = [
        s for s in samples
        if s["target"] == 1
    ]

    negatives = [
        s for s in samples
        if s["target"] == 0
    ]

    random.seed(seed)

    number_of_negatives = min(
        len(negatives),
        len(positives) * negative_ratio,
    )

    negatives = random.sample(
        negatives,
        number_of_negatives,
    )

    result = positives + negatives

    random.shuffle(result)

    return result

def chronological_split(
    samples,
    test_days=7,
):
    samples = sorted(
        samples,
        key=lambda x: x["timestamp"],
    )

    cutoff = (
        samples[-1]["timestamp"]
        - __import__("datetime").timedelta(
            days=test_days
        )
    )

    train = [
        s for s in samples
        if s["timestamp"] < cutoff
    ]

    test = [
        s for s in samples
        if s["timestamp"] >= cutoff
    ]

    return train, test

def train_mlp(train_samples):

    X, y = samples_to_tensors(
        train_samples
    )

    scaler = StandardScaler()

    X_scaled = scaler.fit_transform(
        X.numpy()
    )

    X_scaled = torch.tensor(
        X_scaled,
        dtype=torch.float32,
    )

    model = RiskMLP(
        input_size=len(FEATURES)
    )

    # Positive-class weighting.
    positives = y.sum()
    negatives = len(y) - positives

    pos_weight = negatives / max(
        positives,
        1,
    )

    criterion = torch.nn.BCEWithLogitsLoss(
        pos_weight=pos_weight
    )

    optimizer = torch.optim.Adam(
        model.parameters(),
        lr=0.001,
    )

    for epoch in range(100):

        optimizer.zero_grad()

        logits = model(X_scaled)

        loss = criterion(
            logits,
            y,
        )

        loss.backward()

        optimizer.step()

        if epoch % 10 == 0:

            print(
                f"Epoch {epoch}: "
                f"loss={loss.item():.4f}"
            )

    return model, scaler


def evaluate_model(
    model,
    scaler,
    test_samples,
):

    X, y = samples_to_tensors(
        test_samples
    )

    X_scaled = scaler.transform(
        X.numpy()
    )

    X_scaled = torch.tensor(
        X_scaled,
        dtype=torch.float32,
    )

    model.eval()

    with torch.no_grad():

        probabilities = torch.sigmoid(
            model(X_scaled)
        )

    predictions = (
        probabilities >= 0.5
    ).int()

    y_true = y.int()

    print(
        "Precision:",
        precision_score(
            y_true,
            predictions,
            zero_division=0,
        )
    )

    print(
        "Recall:",
        recall_score(
            y_true,
            predictions,
            zero_division=0,
        )
    )

    print(
        "PR-AUC:",
        average_precision_score(
            y_true,
            probabilities,
        )
    )

    return probabilities

MODEL_PATH = settings.BASE_DIR / "data" / "models" / "risk_model.pt"
SCALER_PATH = settings.BASE_DIR / "data" / "models" / "risk_scaler.pkl"


def project_model_paths(project):
    project_model_dir = (
        settings.BASE_DIR / "data" / "models" / "projects" / str(project.pk)
    )
    return (
        project_model_dir / "risk_model.pt",
        project_model_dir / "risk_scaler.pkl",
    )


def initialize_project_model(project):
    model_path, scaler_path = project_model_paths(project)
    model_path.parent.mkdir(parents=True, exist_ok=True)

    model = RiskMLP(input_size=len(FEATURES))
    model.load_state_dict(
        torch.load(MODEL_PATH, map_location="cpu")
    )
    scaler = joblib.load(SCALER_PATH)

    torch.save(model.state_dict(), model_path)
    joblib.dump(scaler, scaler_path)
    return model_path, scaler_path


def load_project_model(project):
    model_path, scaler_path = project_model_paths(project)
    if not model_path.exists() and not scaler_path.exists():
        initialize_project_model(project)
    elif not model_path.exists() or not scaler_path.exists():
        raise FileNotFoundError(
            f"Incomplete risk model artifacts for project {project.pk}."
        )

    model = RiskMLP(input_size=len(FEATURES))
    model.load_state_dict(
        torch.load(model_path, map_location="cpu")
    )
    model.eval()
    return model, joblib.load(scaler_path)


def calculate_project_risk(project):
    model, scaler = load_project_model(project)

    cells = list(
        project.grid_cells.all()
    )
    if not cells:
        project.uncertainty = 0
        project.save(update_fields=["uncertainty"])
        return cells

    values = [
        [
            cell.elevation or 0,
            cell.slope or 0,
            cell.distance_to_road or 0,
        ]
        for cell in cells
    ]

    scaled_values = scaler.transform(values)

    x = torch.tensor(scaled_values,dtype=torch.float32)

    with torch.no_grad():
        predictions = torch.stack(
            [
                torch.sigmoid(model(x, stochastic=True)).reshape(-1)
                for _ in range(RISK_INFERENCE_PASSES)
            ]
        )
        probabilities = predictions.mean(dim=0)
        average_uncertainty = (
            predictions.var(dim=0, unbiased=False).mean().item()
        )

    for cell, probability in zip(cells, probabilities):
        cell.risk_score = float(
            probability.item()
        )

    project.uncertainty = float(average_uncertainty)
    project.save(update_fields=["uncertainty"])

    GridCell.objects.bulk_update(
        cells,
        ["risk_score"]
    )

    return cells